import ssl
import logging
from opentelemetry import metrics, trace
from opentelemetry.trace import SpanKind
from prometheus_client import REGISTRY
from faststream.security import BaseSecurity
from faststream.opentelemetry import Baggage
from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.fastapi import RabbitRouter, Logger, RabbitMessage
from faststream.rabbit.prometheus import RabbitPrometheusMiddleware
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware


from pipo_dispatch.config import settings
from pipo_dispatch.audio_source.source_oracle import SourceOracle
from pipo_dispatch.models import ProviderOperation, MusicRequest
from pipo_dispatch.telemetry import setup_telemetry
from pipo_dispatch.config import settings

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)


def __load_router(service_name: str) -> RabbitRouter:
    telemetry = setup_telemetry(service_name, settings.telemetry.local)
    core_router = RabbitRouter(
        app_id=settings.app,
        url=settings.queue_broker_url,
        host=settings.player.queue.broker.host,
        virtualhost=settings.player.queue.broker.vhost,
        port=settings.player.queue.broker.port,
        timeout=settings.player.queue.broker.timeout,
        max_consumers=settings.player.queue.broker.max_consumers,
        graceful_timeout=settings.player.queue.broker.graceful_timeout,
        logger=logging.getLogger(__name__),
        security=BaseSecurity(ssl_context=ssl.create_default_context()),
        middlewares=(
            RabbitPrometheusMiddleware(
                registry=REGISTRY,
                app_name=settings.telemetry.metrics.service,
                metrics_prefix="faststream",
            ),
            RabbitTelemetryMiddleware(tracer_provider=telemetry.traces or None),
        ),
    )
    return core_router


router = __load_router(settings.app)


def get_router():
    return router


def get_broker():
    return router.broker


plq = RabbitQueue(
    name=settings.player.queue.service.parking_lot.queue,
    durable=settings.player.queue.service.parking_lot.durable,
)

dlx = RabbitExchange(
    name=settings.player.queue.service.dead_letter.exchange.name,
    type=ExchangeType.TOPIC,
    durable=settings.player.queue.service.dead_letter.exchange.durable,
)

dlq = RabbitQueue(
    name=settings.player.queue.service.dead_letter.queue.name,
    durable=settings.player.queue.service.dead_letter.queue.durable,
    routing_key=settings.player.queue.service.dead_letter.queue.routing_key,
    arguments=settings.player.queue.service.dead_letter.queue.args,
)


async def declare_dlx(broker):
    await broker.declare_queue(plq)
    await broker.declare_exchange(dlx)
    await broker.declare_queue(dlq)


dispatcher_queue = RabbitQueue(
    settings.player.queue.service.dispatcher.queue,
    durable=True,
    arguments=settings.player.queue.service.dispatcher.args,
)

provider_exch = RabbitExchange(
    settings.player.queue.service.transmuter.exchange,
    type=ExchangeType.TOPIC,
    durable=True,
)


dispatch_success_counter = meter.create_counter(
    name="pipo.dispatch.requests.success",
    description="Number of requests dispatched successfully",
    unit="requests",
)

dispatch_fail_counter = meter.create_counter(
    name="pipo.dispatch.requests.fail",
    description="Number of requests dispatched unsuccessfully",
    unit="requests",
)


@router.subscriber(
    queue=dispatcher_queue,
    description="Consumes from dispatch topic and produces to provider exchange",
)
async def dispatch(
    logger: Logger,
    msg: RabbitMessage,
    request: MusicRequest,
) -> None:
    with tracer.start_as_current_span("dispatch", kind=SpanKind.SERVER):
        logger.debug("Processing request: %s", request)
        baggage = Baggage.from_headers(msg.headers)
        with tracer.start_as_current_span("dispatch.process.queries"):
            sources = SourceOracle.process_queries(request.query, request.shuffle)
        with tracer.start_as_current_span("dispatch.process.sources") as sp:
            for source in sources:
                logger.debug("Processing source: %s", source)
                provider = f"{settings.player.queue.service.transmuter.routing_key}.{source.handler_type}.{source.operation}"
                request = ProviderOperation(
                    uuid=request.uuid,
                    server_id=request.server_id,
                    provider=provider,
                    operation=source.operation,
                    shuffle=request.shuffle,
                    query=source.query,
                )
                logger.debug(
                    "Will publish to provider %s request: %s", provider, request
                )
                baggage.set("sub-query", source.query or "")
                await router.broker.publish(
                    request,
                    routing_key=provider,
                    exchange=provider_exch,
                )
                sp.add_event("dispatch.process.source", attributes={"source": source})
                logger.info("Published request: %s", request.uuid)
        if sources:
            dispatch_success_counter.add(1)
        else:
            dispatch_fail_counter.add(1)
