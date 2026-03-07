import json

import pytest

from src.config import PathConfig, AppConfig


class TestPathConfig:
    def test_directory_structure(self):
        data_root = PathConfig.data_root()

        # Directory principali sotto data/
        assert PathConfig.config_dir().parent == data_root
        assert PathConfig.input_dir().parent == data_root
        assert PathConfig.cache_dir().parent == data_root
        assert PathConfig.output_dir().parent == data_root

        # report/ sotto output/
        assert PathConfig.report_dir().parent == PathConfig.output_dir()

    def test_specific_files_paths(self):
        # File di config
        assert PathConfig.localita_file().parent == PathConfig.config_dir()
        assert PathConfig.localita_file().name == "localita.json"

        assert PathConfig.quartieri_file().parent == PathConfig.config_dir()
        assert PathConfig.quartieri_file().name == "quartieri.json"

        assert PathConfig.app_config_file().parent == PathConfig.config_dir()
        assert PathConfig.app_config_file().name == "app_config.json"

        # File di input
        assert PathConfig.studenti_file().parent == PathConfig.input_dir()
        assert PathConfig.studenti_file().name == "studenti.json"

        # File di cache
        assert PathConfig.coordinate_cache_file().parent == PathConfig.cache_dir()
        assert PathConfig.coordinate_cache_file().name == "cache_coordinate.json"

        assert PathConfig.percorsi_cache_file().parent == PathConfig.cache_dir()
        assert PathConfig.percorsi_cache_file().name == "cache_percorsi.json"

        # File di output
        assert PathConfig.mappa_html_file().parent == PathConfig.output_dir()
        assert PathConfig.mappa_html_file().name == "mappa_finale.html"


class TestAppConfig:
    def test_from_env_and_file_raises_without_api_key(self, monkeypatch, tmp_path):
        # Puntiamo il file di config a una path temporanea inesistente
        config_file = tmp_path / "config" / "app_config.json"
        monkeypatch.setattr("src.config.PathConfig.app_config_file", lambda: config_file)

        # Rimuoviamo eventuale variabile d'ambiente impostata esternamente
        monkeypatch.delenv("ORS_API_KEY", raising=False)

        with pytest.raises(ValueError):
            AppConfig.from_env_and_file()

    def test_from_env_and_file_uses_defaults_when_config_missing(
        self, monkeypatch, tmp_path
    ):
        config_file = tmp_path / "config" / "app_config.json"
        monkeypatch.setattr("src.config.PathConfig.app_config_file", lambda: config_file)

        monkeypatch.setenv("ORS_API_KEY", "fake-key")

        cfg = AppConfig.from_env_and_file()

        assert cfg.ors_api_key == "fake-key"
        # Valori di default definiti in from_env_and_file
        assert cfg.nominatim_user_agent == "carpooling-dalmine-v1"
        assert cfg.capacita_macchina == 4
        assert cfg.bonus_corso_laurea == 180
        assert cfg.max_deviazione_sec == 900
        assert cfg.numero_cluster == 7
        assert cfg.comune_destinazione == "DALMINE"
        assert cfg.batch_size_chiamate == 100
        assert cfg.jitter_factor == pytest.approx(0.0003)
        assert cfg.log_level == "INFO"
        assert cfg.environment == "development"

    def test_from_env_and_file_overrides_with_values_from_file(
        self, monkeypatch, tmp_path
    ):
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "app_config.json"

        data = {
            "nominatim_user_agent": "custom-agent",
            "capacita_macchina": 3,
            "bonus_corso_laurea": 200,
            "max_deviazione_sec": 600,
            "numero_cluster": 5,
            "comune_destinazione": "BERGAMO",
            "batch_size_chiamate": 50,
            "jitter_factor": 0.001,
            "log_level": "DEBUG",
            "environment": "production",
        }
        config_file.write_text(json.dumps(data), encoding="utf-8")

        monkeypatch.setattr("src.config.PathConfig.app_config_file", lambda: config_file)
        monkeypatch.setenv("ORS_API_KEY", "file-key")

        cfg = AppConfig.from_env_and_file()

        # API key sempre dall'ambiente
        assert cfg.ors_api_key == "file-key"

        # Parametri letti dal file
        assert cfg.nominatim_user_agent == "custom-agent"
        assert cfg.capacita_macchina == 3
        assert cfg.bonus_corso_laurea == 200
        assert cfg.max_deviazione_sec == 600
        assert cfg.numero_cluster == 5
        assert cfg.comune_destinazione == "BERGAMO"
        assert cfg.batch_size_chiamate == 50
        assert cfg.jitter_factor == pytest.approx(0.001)
        assert cfg.log_level == "DEBUG"
        assert cfg.environment == "production"

    def test_to_dict_hides_api_key(self):
        cfg = AppConfig(
            ors_api_key="super-secret",
            nominatim_user_agent="ua",
            capacita_macchina=4,
            bonus_corso_laurea=180,
            max_deviazione_sec=900,
            numero_cluster=7,
            comune_destinazione="DALMINE",
            batch_size_chiamate=100,
            jitter_factor=0.0003,
            log_level="INFO",
            environment="dev",
        )

        d = cfg.to_dict()

        assert d["ors_api_key"] == "***HIDDEN***"
        assert d["nominatim_user_agent"] == "ua"
        assert d["capacita_macchina"] == 4
        assert d["bonus_corso_laurea"] == 180
        assert d["max_deviazione_sec"] == 900
        assert d["numero_cluster"] == 7
        assert d["comune_destinazione"] == "DALMINE"
        assert d["batch_size_chiamate"] == 100
        assert d["jitter_factor"] == pytest.approx(0.0003)
        assert d["log_level"] == "INFO"
        assert d["environment"] == "dev"