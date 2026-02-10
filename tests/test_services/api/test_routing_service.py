import pytest
import requests

from src.services.api import RoutingService
from src.data.models import Percorso


class DummyResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


@pytest.fixture
def routing_service():
    return RoutingService(api_key="fake-key")


def test_calculate_route_success(monkeypatch, routing_service):
    payload = {
        "features": [
            {
                "properties": {
                    "summary": {
                        "duration": 900.5,
                        "distance": 15000.0,
                    }
                },
                "geometry": {
                    "coordinates": [
                        [9.6773, 45.6983],
                        [9.5969, 45.6469],
                    ]
                },
            }
        ]
    }

    def fake_get(url, params, timeout):
        return DummyResponse(200, payload=payload)

    monkeypatch.setattr("src.services.api.routing_service.requests.get", fake_get)
    monkeypatch.setattr("src.services.api.routing_service.time.sleep", lambda s: None)
    monkeypatch.setattr(
        "src.services.api.routing_service.random.uniform", lambda a, b: 2.0
    )

    start = (45.6983, 9.6773)
    end = (45.6469, 9.5969)

    percorso = routing_service.calculate_route(start, end, "BERGAMO", "DALMINE")

    assert isinstance(percorso, Percorso)
    assert percorso.partenza == "BERGAMO"
    assert percorso.destinazione == "DALMINE"
    assert percorso.durata_sec == int(900.5)
    assert percorso.distanza_m == pytest.approx(15000.0)
    assert percorso.geometria == [(9.6773, 45.6983), (9.5969, 45.6469)]


def test_calculate_route_status_non_200_ritorna_none(monkeypatch, routing_service):
    def fake_get(url, params, timeout):
        return DummyResponse(400, text="Bad request")

    monkeypatch.setattr("src.services.api.routing_service.requests.get", fake_get)
    monkeypatch.setattr("src.services.api.routing_service.time.sleep", lambda s: None)

    percorso = routing_service.calculate_route(
        (45.7, 9.6),
        (45.65, 9.59),
        "A",
        "B",
    )

    assert percorso is None


def test_calculate_route_request_exception(monkeypatch, routing_service):
    def fake_get(url, params, timeout):
        raise requests.RequestException("network error")

    monkeypatch.setattr("src.services.api.routing_service.requests.get", fake_get)
    monkeypatch.setattr("src.services.api.routing_service.time.sleep", lambda s: None)

    percorso = routing_service.calculate_route(
        (45.7, 9.6),
        (45.65, 9.59),
        "A",
        "B",
    )

    assert percorso is None
