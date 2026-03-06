import json
import pytest

from src.data.repositories import StudentiRepository, CacheRepository, ConfigRepository
from src.business.validators import DataValidator
from src.business.clustering import KMeansClusteringService
from src.business.optimization import GreedyOptimizer
from src.business.orchestrators import OptimizationFacade, OptimizeOrchestrator
from src.data.models import Equipaggio


STUDENTI_JSON = [
    {"email": "s1@test.it", "localita": "BERGAMO", "corso": "ING"},
    {"email": "s2@test.it", "localita": "TREVIOLO", "corso": "ING"},
    {"email": "s3@test.it", "localita": "ALBINO", "corso": "ECO"},
    {"email": "s4@test.it", "localita": "BERGAMO", "corso": "ECO"},
]


COORDINATE_JSON = {
    "BERGAMO": [45.70, 9.67],
    "TREVIOLO": [45.68, 9.62],
    "ALBINO": [45.75, 9.65],
    "DALMINE": [45.65, 9.60],
}

PERCORSI_JSON = {
    "BERGAMO-DALMINE": {"durata_sec": 720, "distanza_m": 12000, "geometria": []},
    "TREVIOLO-DALMINE": {"durata_sec": 480, "distanza_m": 8000, "geometria": []},
    "ALBINO-DALMINE": {"durata_sec": 900, "distanza_m": 15000, "geometria": []},
    "DALMINE-DALMINE": {"durata_sec": 0, "distanza_m": 0, "geometria": []},
    "BERGAMO-TREVIOLO": {"durata_sec": 240, "distanza_m": 4000, "geometria": []},
    "TREVIOLO-BERGAMO": {"durata_sec": 240, "distanza_m": 4000, "geometria": []},
    "BERGAMO-ALBINO": {"durata_sec": 360, "distanza_m": 6000, "geometria": []},
    "ALBINO-BERGAMO": {"durata_sec": 360, "distanza_m": 6000, "geometria": []},
    "TREVIOLO-ALBINO": {"durata_sec": 600, "distanza_m": 10000, "geometria": []},
    "ALBINO-TREVIOLO": {"durata_sec": 600, "distanza_m": 10000, "geometria": []},
    "DALMINE-BERGAMO": {"durata_sec": 720, "distanza_m": 12000, "geometria": []},
    "DALMINE-TREVIOLO": {"durata_sec": 480, "distanza_m": 8000, "geometria": []},
    "DALMINE-ALBINO": {"durata_sec": 900, "distanza_m": 15000, "geometria": []},
}

LOCALITA_JSON = {
    "BERGAMO": "Bergamo",
    "TREVIOLO": "Treviolo",
    "ALBINO": "Albino",
    "DALMINE": "Dalmine",
}


@pytest.fixture
def env(tmp_path):
    input_dir = tmp_path / "data" / "input"
    input_dir.mkdir(parents=True)
    cache_dir = tmp_path / "data" / "cache"
    cache_dir.mkdir(parents=True)
    config_dir = tmp_path / "data" / "config"
    config_dir.mkdir(parents=True)

    (input_dir / "studenti.json").write_text(
        json.dumps(STUDENTI_JSON, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (cache_dir / "cache_coordinate.json").write_text(
        json.dumps(COORDINATE_JSON, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (cache_dir / "cache_percorsi.json").write_text(
        json.dumps(PERCORSI_JSON, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (config_dir / "localita.json").write_text(
        json.dumps(LOCALITA_JSON, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    config_repo = ConfigRepository(config_dir)
    studenti_repo = StudentiRepository(input_dir / "studenti.json", config_repo)
    cache_repo = CacheRepository(cache_dir)
    validator = DataValidator(comune_destinazione="DALMINE")
    clustering = KMeansClusteringService(n_clusters=2)
    optimizer = GreedyOptimizer(
        capacita_auto=4, bonus_corso_laurea=180, max_deviazione_sec=99999
    )
    facade = OptimizationFacade(clustering=clustering, optimizer=optimizer)
    orchestrator = OptimizeOrchestrator(
        studenti_repo=studenti_repo,
        cache_repo=cache_repo,
        validator=validator,
        optimization_facade=facade,
    )
    return orchestrator, cache_dir, tmp_path


@pytest.mark.integration
def test_flusso_completo_restituisce_equipaggi(env):
    orchestrator, _, _ = env
    flotta = orchestrator.execute()
    assert len(flotta) > 0
    assert all(isinstance(eq, Equipaggio) for eq in flotta)


@pytest.mark.integration
def test_tutti_gli_studenti_assegnati(env):
    orchestrator, _, _ = env
    flotta = orchestrator.execute()
    assegnati = [eq.autista for eq in flotta] + [
        p for eq in flotta for p in eq.passeggeri
    ]
    assert len(assegnati) == 4


@pytest.mark.integration
def test_equipaggi_rispettano_capacita(env):
    orchestrator, _, _ = env
    flotta = orchestrator.execute()
    assert all(len(eq.membri) <= 4 for eq in flotta)


@pytest.mark.integration
def test_ogni_equipaggio_ha_tappe_valide(env):
    orchestrator, _, _ = env
    flotta = orchestrator.execute()
    for eq in flotta:
        assert len(eq.percorso_tappe) >= 2
        assert eq.percorso_tappe[-1] == "DALMINE"


@pytest.mark.integration
def test_cache_incompleta_solleva_value_error(env):
    _, cache_dir, tmp_path = env
    percorsi_incompleti = {
        k: v for k, v in PERCORSI_JSON.items() if k != "ALBINO-DALMINE"
    }
    (cache_dir / "cache_percorsi.json").write_text(
        json.dumps(percorsi_incompleti, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    config_repo = ConfigRepository(tmp_path / "data" / "config")
    studenti_repo = StudentiRepository(
        tmp_path / "data" / "input" / "studenti.json", config_repo
    )
    cache_repo = CacheRepository(cache_dir)
    validator = DataValidator(comune_destinazione="DALMINE")
    clustering = KMeansClusteringService(n_clusters=2)
    optimizer = GreedyOptimizer(
        capacita_auto=4, bonus_corso_laurea=180, max_deviazione_sec=99999
    )
    facade = OptimizationFacade(clustering=clustering, optimizer=optimizer)
    orchestrator = OptimizeOrchestrator(studenti_repo, cache_repo, validator, facade)

    with pytest.raises(ValueError, match="Cache incompleta"):
        orchestrator.execute()
