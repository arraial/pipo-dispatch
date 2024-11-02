import ssl
import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from prometheus_client import REGISTRY
from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.fastapi import RabbitRouter, Logger
from faststream.rabbit.prometheus import RabbitPrometheusMiddleware
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware
from faststream.security import BaseSecurity
from pipo_dispatch.config import settings
from pipo_dispatch.audio_source.source_oracle import SourceOracle
from pipo_dispatch.models import ProviderOperation, MusicRequest

tracer_provider = TracerProvider(
    resource=Resource.create(attributes={"service.name": "faststream"})
)
trace.set_tracer_provider(tracer_provider)

router = RabbitRouter(
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
        RabbitPrometheusMiddleware(registry=REGISTRY),
        RabbitTelemetryMiddleware(tracer_provider=tracer_provider),
    ),
)

broker = router.broker


@router.get("/livez")
async def liveness() -> bool:
    return True


@router.get("/readyz")
async def readiness() -> bool:
    return await router.broker.ping(timeout=settings.probes.readiness.timeout)


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


# FIXME b = broker
async def declare_dlx(b):
    await b.declare_queue(plq)
    await b.declare_exchange(dlx)
    await b.declare_queue(dlq)


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


@router.subscriber(
    queue=dispatcher_queue,
    description="Consumes from dispatch topic and produces to provider exchange",
)
async def dispatch(
    logger: Logger,
    request: MusicRequest,
) -> None:
    logger.debug("Processing request: %s", request)
    sources = SourceOracle.process_queries(request.query, request.shuffle)
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
        logger.debug("Will publish to provider %s request: %s", provider, request)
        await router.broker.publish(
            request,
            routing_key=provider,
            exchange=provider_exch,
        )
        logger.info("Published request: %s", request.uuid)
