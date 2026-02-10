from src.data.models.percorso import Percorso
from src.services.external_api_facade import ExternalAPIFacade


class DummyCoordinateCache:
    def __init__(self):
        self.data = {}
        self.get_calls = 0
        self.set_calls = []

    def has(self, key: str) -> bool:
        return key in self.data

    def get(self, key: str):
        self.get_calls += 1
        return self.data.get(key)

    def set(self, key: str, coords):
        self.set_calls.append((key, coords))
        self.data[key] = coords


class DummyPercorsiCache:
    def __init__(self):
        self.data = {}
        self.set_calls = []

    def has_complete(self, partenza: str, destinazione: str) -> bool:
        key = f"{partenza}-{destinazione}"
        return key in self.data and isinstance(self.data[key], Percorso)

    def get(self, partenza: str, destinazione: str):
        return self.data.get(f"{partenza}-{destinazione}")

    def set(self, percorso: Percorso):
        key = f"{percorso.partenza}-{percorso.destinazione}"
        self.set_calls.append(key)
        self.data[key] = percorso


class DummyCacheRepo:
    def __init__(self):
        self.coordinate_cache = DummyCoordinateCache()
        self.percorsi_cache = DummyPercorsiCache()


class DummyGeocodingService:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def geocode_localita(self, key: str):
        self.calls.append(key)
        return self.mapping.get(key)


class DummyRoutingService:
    def __init__(self, percorso: Percorso | None):
        self.percorso = percorso
        self.calls = []

    def calculate_route(self, start_coords, end_coords, start_key, end_key):
        self.calls.append((start_coords, end_coords, start_key, end_key))
        return self.percorso


def test_get_coordinate_with_cache_hit():
    cache = DummyCacheRepo()
    cache.coordinate_cache.data["BERGAMO"] = (45.7, 9.67)

    facade = ExternalAPIFacade(
        geocoding=DummyGeocodingService({}),
        routing=DummyRoutingService(None),
        cache=cache,
    )

    coords = facade.get_coordinate_with_cache("BERGAMO")

    assert coords == (45.7, 9.67)
    # Nessuna chiamata a geocoding in caso di hit
    assert cache.coordinate_cache.get_calls == 1
    assert facade.geocoding.calls == []


def test_get_coordinate_with_cache_miss_salva_in_cache():
    cache = DummyCacheRepo()
    geocoding = DummyGeocodingService({"DALMINE": (45.65, 9.6)})

    facade = ExternalAPIFacade(
        geocoding=geocoding,
        routing=DummyRoutingService(None),
        cache=cache,
    )

    coords = facade.get_coordinate_with_cache("DALMINE")

    assert coords == (45.65, 9.6)
    assert geocoding.calls == ["DALMINE"]
    assert cache.coordinate_cache.data["DALMINE"] == (45.65, 9.6)


def test_get_coordinate_with_cache_miss_e_none_viene_cachato():
    cache = DummyCacheRepo()
    geocoding = DummyGeocodingService({"ATLANTIDE": None})

    facade = ExternalAPIFacade(
        geocoding=geocoding,
        routing=DummyRoutingService(None),
        cache=cache,
    )

    coords = facade.get_coordinate_with_cache("ATLANTIDE")

    assert coords is None
    assert cache.coordinate_cache.data["ATLANTIDE"] is None


def test_get_percorso_same_localita():
    cache = DummyCacheRepo()
    geocoding = DummyGeocodingService({})
    routing = DummyRoutingService(None)

    facade = ExternalAPIFacade(
        geocoding=geocoding,
        routing=routing,
        cache=cache,
    )

    p = facade.get_percorso_with_cache("BERGAMO", "BERGAMO")

    assert isinstance(p, Percorso)
    assert p.partenza == "BERGAMO"
    assert p.destinazione == "BERGAMO"
    assert p.durata_sec == 0
    assert p.distanza_m == 0
    assert p.geometria == []


def test_get_percorso_cache_hit():
    cache = DummyCacheRepo()
    geocoding = DummyGeocodingService({})
    percorso = Percorso(
        partenza="BERGAMO",
        destinazione="DALMINE",
        durata_sec=720,
        distanza_m=12500,
        geometria=[(9.6773, 45.6983), (9.5969, 45.6469)],
    )
    cache.percorsi_cache.data["BERGAMO-DALMINE"] = percorso

    facade = ExternalAPIFacade(
        geocoding=geocoding,
        routing=DummyRoutingService(None),
        cache=cache,
    )

    p = facade.get_percorso_with_cache("BERGAMO", "DALMINE")

    assert p is percorso
    # Niente geocoding / routing in caso di hit
    assert geocoding.calls == []


def test_get_percorso_cache_miss_coordinate_mancanti():
    cache = DummyCacheRepo()
    geocoding = DummyGeocodingService({"BERGAMO": None, "DALMINE": (45.65, 9.6)})

    facade = ExternalAPIFacade(
        geocoding=geocoding,
        routing=DummyRoutingService(None),
        cache=cache,
    )

    p = facade.get_percorso_with_cache("BERGAMO", "DALMINE")

    assert p is None  # coordinate mancanti -> nessun percorso


def test_get_percorso_cache_miss_con_routing_e_salvataggio():
    cache = DummyCacheRepo()
    geocoding = DummyGeocodingService(
        {
            "BERGAMO": (45.6983, 9.6773),
            "DALMINE": (45.6469, 9.5969),
        }
    )
    percorso = Percorso(
        partenza="BERGAMO",
        destinazione="DALMINE",
        durata_sec=720,
        distanza_m=12500,
        geometria=[(9.6773, 45.6983), (9.5969, 45.6469)],
    )
    routing = DummyRoutingService(percorso)

    facade = ExternalAPIFacade(
        geocoding=geocoding,
        routing=routing,
        cache=cache,
    )

    p = facade.get_percorso_with_cache("BERGAMO", "DALMINE")

    assert p is percorso
    assert cache.percorsi_cache.has_complete("BERGAMO", "DALMINE")
