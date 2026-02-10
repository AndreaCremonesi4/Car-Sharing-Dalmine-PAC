import pytest
from pathlib import Path
from src.data.repositories.cache_repository import (
    CacheRepository,
    CoordinateCache,
    PercorsiCache,
)
from src.data.models import Percorso


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "cache"
    d.mkdir()
    return d


class TestCoordinateCache:
    def test_cache_vuota_iniziale(self, temp_cache_dir):
        cache_file = temp_cache_dir / "coord.json"
        cache = CoordinateCache(cache_file)

        assert cache.data == {}
        assert not cache.has("BERGAMO")
        assert cache.get("BERGAMO") is None

    def test_set_e_get_coordinate(self, temp_cache_dir):
        cache_file = temp_cache_dir / "coord.json"
        cache = CoordinateCache(cache_file)

        coords = (45.6983, 9.6773)
        cache.set("BERGAMO", coords)

        assert cache.has("BERGAMO")
        assert cache.get("BERGAMO") == coords

    def test_persistenza_su_disco(self, temp_cache_dir):
        cache_file = temp_cache_dir / "coord.json"

        cache1 = CoordinateCache(cache_file)
        cache1.set("DALMINE", (45.6469, 9.5969))
        cache1.save()

        cache2 = CoordinateCache(cache_file)
        assert cache2.has("DALMINE")
        assert cache2.get("DALMINE") == (45.6469, 9.5969)

    def test_cache_con_valore_none(self, temp_cache_dir):
        cache_file = temp_cache_dir / "coord.json"
        cache = CoordinateCache(cache_file)

        cache.set("ATLANTIDE", None)

        assert cache.has("ATLANTIDE")
        assert cache.get("ATLANTIDE") is None


class TestPercorsiCache:
    def test_get_percorso_mancante_o_incompleto(self, temp_cache_dir):
        cache_file = temp_cache_dir / "percorsi.json"
        cache = PercorsiCache(cache_file)

        assert cache.get("BERGAMO", "DALMINE") is None

        # Scriviamo manualmente un record incompleto (senza geometria)
        cache.data["BERGAMO-DALMINE"] = {
            "durata_sec": 720,
            "distanza_m": 12500,
        }
        assert cache.get("BERGAMO", "DALMINE") is None

    def test_set_e_get_percorso_completo(self, temp_cache_dir):
        cache_file = temp_cache_dir / "percorsi.json"
        cache = PercorsiCache(cache_file)

        percorso = Percorso(
            partenza="BERGAMO",
            destinazione="DALMINE",
            durata_sec=720,
            distanza_m=12500,
            geometria=[(9.6773, 45.6983), (9.5969, 45.6469)],
        )

        cache.set(percorso)

        assert cache.has_complete("BERGAMO", "DALMINE")

        p2 = cache.get("BERGAMO", "DALMINE")
        assert isinstance(p2, Percorso)
        assert p2.partenza == "BERGAMO"
        assert p2.destinazione == "DALMINE"
        assert p2.durata_sec == 720
        assert p2.distanza_m == 12500
        assert p2.geometria == [(9.6773, 45.6983), (9.5969, 45.6469)]

    def test_persistenza_percorsi_su_disco(self, temp_cache_dir):
        cache_file = temp_cache_dir / "percorsi.json"

        cache1 = PercorsiCache(cache_file)
        p = Percorso(
            partenza="BERGAMO",
            destinazione="DALMINE",
            durata_sec=720,
            distanza_m=12500,
            geometria=[(9.6773, 45.6983), (9.5969, 45.6469)],
        )
        cache1.set(p)
        cache1.save()

        cache2 = PercorsiCache(cache_file)
        assert cache2.has_complete("BERGAMO", "DALMINE")
        assert isinstance(cache2.get("BERGAMO", "DALMINE"), Percorso)


class TestCacheRepository:
    def test_save_all_crea_file_cache(self, temp_cache_dir):
        repo = CacheRepository(temp_cache_dir)

        repo.coordinate_cache.set("BERGAMO", (45.6983, 9.6773))
        p = Percorso(
            partenza="BERGAMO",
            destinazione="DALMINE",
            durata_sec=720,
            distanza_m=12500,
            geometria=[(9.6773, 45.6983), (9.5969, 45.6469)],
        )
        repo.percorsi_cache.set(p)

        repo.save_all()

        assert (temp_cache_dir / "cache_coordinate.json").exists()
        assert (temp_cache_dir / "cache_percorsi.json").exists()