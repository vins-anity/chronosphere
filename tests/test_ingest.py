"""
Tests for GSI Ingest Endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio


class TestGSIEndpoint:
    """Tests for /api/v1/gsi endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        # Mock the startup dependencies
        with patch("app.core.db.connect_db", new_callable=AsyncMock):
            with patch("app.core.db.disconnect_db", new_callable=AsyncMock):
                with patch("app.worker.worker.process_gsi_stream", new_callable=AsyncMock):
                    from app.ingest.main import app
                    from app.core import globals
                    globals.queue = asyncio.Queue()
                    return TestClient(app)
    
    def test_gsi_valid_json(self, client):
        """Valid GSI JSON should return 200."""
        payload = {
            "provider": {"timestamp": 123456},
            "map": {"clock_time": 600, "radiant_gold": 30000, "dire_gold": 25000},
        }
        response = client.post("/api/v1/gsi", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_gsi_empty_json(self, client):
        """Empty JSON should still be accepted."""
        response = client.post("/api/v1/gsi", json={})
        assert response.status_code == 200
    
    def test_gsi_invalid_json(self, client):
        """Invalid JSON should return 400."""
        response = client.post(
            "/api/v1/gsi",
            content=b"not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
    
    def test_gsi_queues_data(self, client):
        """GSI data should be queued for processing."""
        from app.core import globals
        
        initial_size = globals.queue.qsize()
        
        payload = {"map": {"clock_time": 100}}
        client.post("/api/v1/gsi", json=payload)
        
        # Queue should have one more item
        assert globals.queue.qsize() == initial_size + 1


class TestWebSocketEndpoint:
    """Tests for /ws/live WebSocket endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        with patch("app.core.db.connect_db", new_callable=AsyncMock):
            with patch("app.core.db.disconnect_db", new_callable=AsyncMock):
                with patch("app.worker.worker.process_gsi_stream", new_callable=AsyncMock):
                    from app.ingest.main import app
                    from app.core import globals
                    globals.queue = asyncio.Queue()
                    return TestClient(app)
    
    def test_websocket_connect(self, client):
        """WebSocket should accept connections."""
        with client.websocket_connect("/ws/live") as websocket:
            # Connection should be established
            assert websocket is not None


class TestHealthCheck:
    """Tests for API health."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        with patch("app.core.db.connect_db", new_callable=AsyncMock):
            with patch("app.core.db.disconnect_db", new_callable=AsyncMock):
                with patch("app.worker.worker.process_gsi_stream", new_callable=AsyncMock):
                    from app.ingest.main import app
                    from app.core import globals
                    globals.queue = asyncio.Queue()
                    return TestClient(app)
    
    def test_docs_available(self, client):
        """OpenAPI docs should be available."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_json(self, client):
        """OpenAPI JSON should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/v1/gsi" in data["paths"]
