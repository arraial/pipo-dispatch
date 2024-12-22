#!usr/bin/env python3
import pytest
from pipo_dispatch._queues import get_router
from pipo_dispatch.app import create_app
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthProbes:
    @pytest.fixture
    async def client(self):
        with TestClient(create_app(get_router())) as test_client:
            yield test_client

    def test_livez(self, client):
        response = client.get("/livez")
        assert response.status_code == 200

    def test_readyz(self, client):
        response = client.get("/readyz")
        assert response.status_code == 204
