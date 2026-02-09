import pytest
from src.services.api import GeocodingService


class DummyConfigRepo:
    def __init__(self, mapping, quartieri=None):
        self._mapping = mapping
        self._quartieri = set(quartieri or [])

    def get_localita_display_name(self, key: str):
        return self._mapping.get(key)

    def is_quartiere_bergamo(self, key: str) -> bool:
        return key in self._quartieri


class DummyLocation:
    def __init__(self, lat, lon):
        self.latitude = lat
        self.longitude = lon


@pytest.fixture
def geocoding_service(monkeypatch):
    config = DummyConfigRepo(
        mapping={"BERGAMO": "Bergamo", "REDONA": "Redona"},
        quartieri={"REDONA"},
    )
    svc = GeocodingService(config_repo=config, user_agent="test-agent")

    # Evita sleep reale: usa il path completo del modulo sotto src
    monkeypatch.setattr("src.services.api.geocoding_service.time.sleep", lambda s: None)

    return svc


def test_geocode_quartiere_bergamo_costruisce_query_corretta(
    geocoding_service, monkeypatch
):
    queries = []

    def fake_geocode(query, timeout):
        queries.append(query)
        return DummyLocation(45.7, 9.67)

    # Patchiamo direttamente l’istanza Nominatim usata dal service
    monkeypatch.setattr(geocoding_service.geolocator, "geocode", fake_geocode)

    coords = geocoding_service.geocode_localita("REDONA")

    assert coords == (45.7, 9.67)
    assert queries == ["Redona, Bergamo, BG, Italia"]


def test_geocode_localita_generica_costruisce_query_corretta(
    geocoding_service, monkeypatch
):
    queries = []

    def fake_geocode(query, timeout):
        queries.append(query)
        return DummyLocation(45.65, 9.6)

    monkeypatch.setattr(geocoding_service.geolocator, "geocode", fake_geocode)

    coords = geocoding_service.geocode_localita("BERGAMO")

    assert coords == (45.65, 9.6)
    assert queries == ["Bergamo, Italia"]


def test_geocode_localita_non_mappata_ritorna_none():
    config = DummyConfigRepo(mapping={}, quartieri=set())
    svc = GeocodingService(config_repo=config, user_agent="test-agent")

    coords = svc.geocode_localita("SCONOSCIUTA")

    # Località non mappata => None e nessuna chiamata a Nominatim
    assert coords is None
