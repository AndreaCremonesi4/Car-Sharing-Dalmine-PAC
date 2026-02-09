import os
import pytest
from src.services.api import RoutingService


@pytest.mark.integration
@pytest.mark.slow
def test_routing_bergamo_dalmine_reale():
    api_key = os.getenv("ORS_API_KEY")
    if not api_key:
        pytest.skip("ORS_API_KEY non configurata, salto test di integrazione routing")

    service = RoutingService(api_key=api_key)

    # Coordinate approssimative Bergamo e Dalmine
    start = (45.6983, 9.6773)
    end = (45.6469, 9.5969)

    percorso = service.calculate_route(start, end, "BERGAMO", "DALMINE")

    assert percorso is not None
    assert percorso.distanza_m > 0
    assert percorso.durata_sec > 0
    assert len(percorso.geometria) > 1