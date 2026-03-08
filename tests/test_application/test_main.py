import pytest
import sys
from pathlib import Path

# Per testare main.py vogliamo simulare l'esecuzione
# "python src/main.py", dove la directory src è in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import main as main_mod  # type: ignore[import-not-found]  # noqa: E402


class DummyConfigRepo:
    def __init__(self, config_dir):
        self.config_dir = config_dir


class DummyCacheRepo:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir


class DummyStudentiRepo:
    def __init__(self, studenti_file, config_repo):
        self.studenti_file = studenti_file
        self.config_repo = config_repo


def test_initialize_layer1_data_usa_pathconfig(monkeypatch):
    # Patchiamo le repository per evitare I/O reale
    monkeypatch.setattr(main_mod, "ConfigRepository", DummyConfigRepo)
    monkeypatch.setattr(main_mod, "CacheRepository", DummyCacheRepo)
    monkeypatch.setattr(main_mod, "StudentiRepository", DummyStudentiRepo)

    expected_config_dir = main_mod.PathConfig.config_dir()
    expected_cache_dir = main_mod.PathConfig.cache_dir()
    expected_studenti_file = main_mod.PathConfig.studenti_file()

    config_repo, cache_repo, studenti_repo = main_mod.initialize_layer1_data()

    assert isinstance(config_repo, DummyConfigRepo)
    assert isinstance(cache_repo, DummyCacheRepo)
    assert isinstance(studenti_repo, DummyStudentiRepo)

    assert config_repo.config_dir == expected_config_dir
    assert cache_repo.cache_dir == expected_cache_dir
    assert studenti_repo.studenti_file == expected_studenti_file
    assert studenti_repo.config_repo is config_repo


class DummyGeocodingService:
    def __init__(self, config_repo, user_agent):
        self.config_repo = config_repo
        self.user_agent = user_agent


class DummyRoutingService:
    def __init__(self, api_key):
        self.api_key = api_key


class DummyExternalAPIFacade:
    def __init__(self, geocoding, routing, cache_repo):
        self.geocoding = geocoding
        self.routing = routing
        self.cache_repo = cache_repo


def test_initialize_layer2_services_cablatura_correlata(monkeypatch):
    monkeypatch.setattr(main_mod, "GeocodingService", DummyGeocodingService)
    monkeypatch.setattr(main_mod, "RoutingService", DummyRoutingService)
    monkeypatch.setattr(main_mod, "ExternalAPIFacade", DummyExternalAPIFacade)

    class SimpleAppConfig:
        def __init__(self):
            self.nominatim_user_agent = "ua-test"
            self.ors_api_key = "api-key"

    app_cfg = SimpleAppConfig()
    dummy_config_repo = object()
    dummy_cache_repo = object()

    facade = main_mod.initialize_layer2_services(
        app_cfg, dummy_config_repo, dummy_cache_repo
    )

    assert isinstance(facade, DummyExternalAPIFacade)
    assert isinstance(facade.geocoding, DummyGeocodingService)
    assert isinstance(facade.routing, DummyRoutingService)
    assert facade.geocoding.config_repo is dummy_config_repo
    assert facade.geocoding.user_agent == "ua-test"
    assert facade.routing.api_key == "api-key"
    assert facade.cache_repo is dummy_cache_repo


class DummyClustering:
    def __init__(self, n_clusters):
        self.n_clusters = n_clusters


class DummyOptimizer:
    def __init__(
        self, capacita_auto, bonus_corso_laurea, max_deviazione_sec, comune_destinazione
    ):
        self.capacita_auto = capacita_auto
        self.bonus_corso_laurea = bonus_corso_laurea
        self.max_deviazione_sec = max_deviazione_sec
        self.comune_destinazione = comune_destinazione


class DummyOptimizationFacade:
    def __init__(self, clustering, optimizer):
        self.clustering = clustering
        self.optimizer = optimizer


class DummyPopulateOrchestrator:
    def __init__(self, studenti_repo, api_facade, clustering, comune_destinazione):
        self.studenti_repo = studenti_repo
        self.api_facade = api_facade
        self.clustering = clustering
        self.comune_destinazione = comune_destinazione


class DummyOptimizeOrchestrator:
    def __init__(self, studenti_repo, cache_repo, validator, optimization_facade):
        self.studenti_repo = studenti_repo
        self.cache_repo = cache_repo
        self.validator = validator
        self.optimization_facade = optimization_facade


def test_initialize_layer3_business_cablatura_correlata(monkeypatch):
    monkeypatch.setattr(main_mod, "KMeansClusteringService", DummyClustering)
    monkeypatch.setattr(main_mod, "GreedyOptimizer", DummyOptimizer)
    monkeypatch.setattr(main_mod, "OptimizationFacade", DummyOptimizationFacade)
    monkeypatch.setattr(main_mod, "PopulateOrchestrator", DummyPopulateOrchestrator)
    monkeypatch.setattr(main_mod, "OptimizeOrchestrator", DummyOptimizeOrchestrator)

    class SimpleAppConfig:
        def __init__(self):
            self.numero_cluster = 7
            self.capacita_macchina = 4
            self.bonus_corso_laurea = 180
            self.max_deviazione_sec = 900
            self.comune_destinazione = "DALMINE"

    app_cfg = SimpleAppConfig()
    studenti_repo = object()
    cache_repo = object()
    api_facade = object()

    populate_orch, optimize_orch = main_mod.initialize_layer3_business(
        app_cfg, studenti_repo, cache_repo, api_facade
    )

    assert isinstance(populate_orch, DummyPopulateOrchestrator)
    assert isinstance(optimize_orch, DummyOptimizeOrchestrator)

    # Verifica parametri passati a clustering/optimizer tramite OptimizationFacade
    opt_facade = optimize_orch.optimization_facade
    assert isinstance(opt_facade.clustering, DummyClustering)
    assert opt_facade.clustering.n_clusters == 7

    assert isinstance(opt_facade.optimizer, DummyOptimizer)
    assert opt_facade.optimizer.capacita_auto == 4
    assert opt_facade.optimizer.bonus_corso_laurea == 180
    assert opt_facade.optimizer.max_deviazione_sec == 900
    assert opt_facade.optimizer.comune_destinazione == "DALMINE"


class DummyCLIParser:
    def __init__(self, mode):
        self._mode = mode

    def parse(self):
        class ProgramConfig:
            def __init__(self, mode):
                self.mode = mode

        return ProgramConfig(self._mode)


class DummyMapGenerator:
    def __init__(self, jitter_factor):
        self.jitter_factor = jitter_factor


class DummyConsoleFormatter:
    def __init__(self, config_repo):
        self.config_repo = config_repo


def test_initialize_layer4_presentation_cablatura_correlata(monkeypatch):
    monkeypatch.setattr(main_mod, "CLIArgumentParser", lambda: DummyCLIParser("popola"))
    monkeypatch.setattr(main_mod, "MapGenerator", DummyMapGenerator)
    monkeypatch.setattr(main_mod, "ConsoleFormatter", DummyConsoleFormatter)

    class SimpleAppConfig:
        def __init__(self):
            self.jitter_factor = 0.001

    app_cfg = SimpleAppConfig()
    dummy_config_repo = object()

    cli_parser, map_generator, console_formatter = (
        main_mod.initialize_layer4_presentation(app_cfg, dummy_config_repo)
    )

    assert isinstance(cli_parser, DummyCLIParser)
    assert isinstance(map_generator, DummyMapGenerator)
    assert isinstance(console_formatter, DummyConsoleFormatter)

    assert map_generator.jitter_factor == pytest.approx(0.001)
    assert console_formatter.config_repo is dummy_config_repo


def _setup_minimal_main_environment(monkeypatch, mode: str):
    # Dummy AppConfig usato da main()
    class DummyAppConfig:
        def __init__(self):
            self.jitter_factor = 0.001

        @classmethod
        def from_env_and_file(cls):
            return cls()

        def print_summary(self):
            # Metodo intenzionalmente vuoto: in questi test non vogliamo
            # output su console, ma solo verificare il wiring di main().
            ...

    monkeypatch.setattr(main_mod, "AppConfig", DummyAppConfig)

    # Layer 1
    def fake_init_layer1():
        return "config_repo", "cache_repo", "studenti_repo"

    monkeypatch.setattr(main_mod, "initialize_layer1_data", fake_init_layer1)

    # Layer 2
    def fake_init_layer2(app_config, config_repo, cache_repo):
        return "api_facade"

    monkeypatch.setattr(main_mod, "initialize_layer2_services", fake_init_layer2)

    # Layer 3
    def fake_init_layer3(app_config, studenti_repo, cache_repo, api_facade):
        return "populate_orch", "optimize_orch"

    monkeypatch.setattr(main_mod, "initialize_layer3_business", fake_init_layer3)

    # Layer 4: restituisce un parser che produce la modalità desiderata
    def fake_init_layer4(app_config, config_repo):
        return DummyCLIParser(mode), "map_generator", "console_formatter"

    monkeypatch.setattr(main_mod, "initialize_layer4_presentation", fake_init_layer4)


def test_main_routing_modalita_popola(monkeypatch):
    _setup_minimal_main_environment(monkeypatch, mode="popola")

    called = {"popola": False, "ottimizza": False}

    def fake_execute_popola(orchestrator, app_config):
        called["popola"] = True

    def fake_execute_ottimizza(opt_orch, console_formatter, map_gen, cache_repo):
        called["ottimizza"] = True

    monkeypatch.setattr(main_mod, "execute_populate_mode", fake_execute_popola)
    monkeypatch.setattr(main_mod, "execute_optimize_mode", fake_execute_ottimizza)

    main_mod.main()

    assert called["popola"] is True
    assert called["ottimizza"] is False


def test_main_routing_modalita_ottimizza(monkeypatch):
    _setup_minimal_main_environment(monkeypatch, mode="ottimizza")

    called = {"popola": False, "ottimizza": False}

    def fake_execute_popola(orchestrator, app_config):
        called["popola"] = True

    def fake_execute_ottimizza(opt_orch, console_formatter, map_gen, cache_repo):
        called["ottimizza"] = True

    monkeypatch.setattr(main_mod, "execute_populate_mode", fake_execute_popola)
    monkeypatch.setattr(main_mod, "execute_optimize_mode", fake_execute_ottimizza)

    main_mod.main()

    assert called["popola"] is False
    assert called["ottimizza"] is True


def test_main_modalita_sconosciuta_fa_exit_1(monkeypatch):
    _setup_minimal_main_environment(monkeypatch, mode="sconosciuta")

    # Sostituiamo sys.exit per intercettare il codice
    def fake_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(main_mod.sys, "exit", fake_exit)

    with pytest.raises(SystemExit) as excinfo:
        main_mod.main()

    assert excinfo.value.code == 1


def test_main_errore_configurazione_fa_exit_1(monkeypatch):
    # AppConfig.from_env_and_file solleva ValueError
    class FailingAppConfig:
        @classmethod
        def from_env_and_file(cls):
            raise ValueError("config error")

    monkeypatch.setattr(main_mod, "AppConfig", FailingAppConfig)

    # Evitiamo che sys.exit termini il test runner
    def fake_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(main_mod.sys, "exit", fake_exit)

    with pytest.raises(SystemExit) as excinfo:
        main_mod.main()

    assert excinfo.value.code == 1
