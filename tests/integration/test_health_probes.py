#!usr/bin/env python3
import pytest
from fastapi.testclient import TestClient

from pipo_dispatch.config import settings
from pipo_dispatch.app import create_app

@pytest.mark.integration
class TestHealthProbes:
    @pytest.fixture
    async def client(self):
        with TestClient(create_app()) as test_client:
            yield test_client

    def test_livez(self, client):
        response = client.get("/livez", timeout=settings.probes.liveness.timeout)
        assert response.status_code == settings.probes.liveness.status_code

    def test_readyz(self, client):
        response = client.get("/readyz", timeout=settings.probes.readiness.timeout)
        assert response.status_code == 204
