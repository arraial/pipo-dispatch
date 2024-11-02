#!usr/bin/env python3
import asyncio
import signal
import contextlib
from fastapi import FastAPI
from prometheus_client import REGISTRY, make_asgi_app

from pipo_dispatch.config import settings
from pipo_dispatch.signal_manager import SignalManager
from pipo_dispatch._queues import router as probe_router


@contextlib.asynccontextmanager
async def _run_bot(app: FastAPI):
    asyncio.current_task().set_name(settings.main_task_name)
    SignalManager.add_handlers(
        asyncio.get_event_loop(),
        settings.main_task_name,
        (signal.SIGUSR1, signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT),
    )
    await probe_router.broker.connect()
    await probe_router.broker.start()
    yield


def get_app() -> FastAPI:
    application = FastAPI(lifespan=_run_bot)
    application.mount("/metrics", make_asgi_app(registry=REGISTRY))
    application.include_router(probe_router)
    return application
