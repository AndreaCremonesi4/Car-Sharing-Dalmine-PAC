import pytest
import json
from pathlib import Path
from src.data.repositories import ConfigRepository
from src.services.api import GeocodingService


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.integration
class TestGeocodingIntegration:
    @pytest.fixture
    def geocoding_service(self, tmp_path):
        config_dir = tmp_path / "config"
        _write_json(config_dir / "localita.json", {"BERGAMO": "Bergamo"})
        _write_json(config_dir / "quartieri.json", ["CITTA_ALTA"])

        config_repo = ConfigRepository(config_dir)
        # user_agent dedicato per Nominatim
        return GeocodingService(
            config_repo=config_repo, user_agent="carsharing-test/1.0"
        )

    def test_geocoding_bergamo_reale(self, geocoding_service):
        coords = geocoding_service.geocode_localita("BERGAMO")

        assert coords is not None
        lat, lon = coords
        # Range approssimativo per Bergamo
        assert 45.6 < lat < 45.8
        assert 9.5 < lon < 9.8

    @pytest.mark.slow
    def test_localita_inesistente(self, geocoding_service):
        coords = geocoding_service.geocode_localita("ATLANTIDE123")
        assert coords is None