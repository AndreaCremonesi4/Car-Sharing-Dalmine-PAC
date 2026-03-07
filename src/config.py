"""
Configurazione centralizzata del progetto.
Gestisce path, parametri algoritmo, variabili ambiente.
"""

import os
from pathlib import Path
from dataclasses import dataclass
import json
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# PATH CONFIGURATION
# =============================================================================


class PathConfig:
    """
    Configurazione dinamica dei percorsi file.
    Supporta override tramite variabili ambiente per multi-ambiente deployment.
    """

    @staticmethod
    def get_project_root() -> Path:
        """
        Ottiene la root del progetto.

        Returns:
            Path assoluto della directory root del progetto
        """
        return Path(__file__).parent.parent.resolve()

    @staticmethod
    def get_data_root() -> Path:
        """
        Ottiene la directory dati.

        Returns:
            Path assoluto della directory dati
        """
        return PathConfig.get_project_root() / "data"

    # === DIRECTORY PRINCIPALI ===

    @classmethod
    def data_root(cls) -> Path:
        """Directory dati principale"""
        return cls.get_data_root()

    # === SOTTODIRECTORY DATI ===

    @classmethod
    def config_dir(cls) -> Path:
        """Configurazioni statiche"""
        return cls.data_root() / "config"

    @classmethod
    def input_dir(cls) -> Path:
        """Dati di input utente"""
        return cls.data_root() / "input"

    @classmethod
    def cache_dir(cls) -> Path:
        """Cache generata dal programma"""
        return cls.data_root() / "cache"

    @classmethod
    def output_dir(cls) -> Path:
        """Output generati"""
        return cls.data_root() / "output"

    @classmethod
    def report_dir(cls) -> Path:
        """Report dettagliati"""
        return cls.output_dir() / "report"

    # === FILE SPECIFICI ===

    # File di configurazione (read-only)
    @classmethod
    def localita_file(cls) -> Path:
        """File localita.json con mappatura località"""
        return cls.config_dir() / "localita.json"

    @classmethod
    def quartieri_file(cls) -> Path:
        """File quartieri.json con elenco quartieri Bergamo"""
        return cls.config_dir() / "quartieri.json"

    @classmethod
    def app_config_file(cls) -> Path:
        """File app_config.json con parametri applicazione"""
        return cls.config_dir() / "app_config.json"

    # File di input
    @classmethod
    def studenti_file(cls) -> Path:
        """File studenti.json con dati studenti"""
        return cls.input_dir() / "studenti.json"

    # File di cache
    @classmethod
    def coordinate_cache_file(cls) -> Path:
        """Cache coordinate geocodificate"""
        return cls.cache_dir() / "cache_coordinate.json"

    @classmethod
    def percorsi_cache_file(cls) -> Path:
        """Cache percorsi stradali"""
        return cls.cache_dir() / "cache_percorsi.json"

    # File di output
    @classmethod
    def mappa_html_file(cls) -> Path:
        """Mappa HTML interattiva"""
        return cls.output_dir() / "mappa_finale.html"


# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================


@dataclass
class AppConfig:
    """
    Configurazione applicazione con parametri business e tecnici.
    Caricabile da file JSON.
    """

    # === API CONFIGURATION ===
    ors_api_key: str
    nominatim_user_agent: str = "carsharing-dalmine-v1"

    # === BUSINESS RULES ===
    capacita_macchina: int = 4
    bonus_corso_laurea: int = 180  # secondi (3 minuti)
    max_deviazione_sec: int = 900  # 15 minuti
    numero_cluster: int = 7
    comune_destinazione: str = "DALMINE"

    # === PROCESSING ===
    batch_size_chiamate: int = 100
    jitter_factor: float = 0.0003  # ~30 metri

    # === LOGGING ===
    log_level: str = "INFO"
    environment: str = "development"

    @classmethod
    def from_env_and_file(cls) -> "AppConfig":
        """
        Carica configurazione da variabili ambiente e file JSON.

        """
        # Carica file JSON se esiste
        config_from_file = {}
        config_file = PathConfig.app_config_file()
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_from_file = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: File config JSON malformato: {e}")

        # API Key obbligatoria
        ors_api_key = os.getenv("ORS_API_KEY")
        if not ors_api_key:
            raise ValueError(
                "ORS_API_KEY non configurata!\nImposta la variabile ambiente"
            )

        # Costruisci config con precedenza file > default
        return cls(
            ors_api_key=ors_api_key,
            nominatim_user_agent=config_from_file.get(
                "nominatim_user_agent", "carpooling-dalmine-v1"
            ),
            capacita_macchina=int(config_from_file.get("capacita_macchina", 4)),
            bonus_corso_laurea=int(config_from_file.get("bonus_corso_laurea", 180)),
            max_deviazione_sec=int(config_from_file.get("max_deviazione_sec", 900)),
            numero_cluster=int(config_from_file.get("numero_cluster", 7)),
            comune_destinazione=config_from_file.get("comune_destinazione", "DALMINE"),
            batch_size_chiamate=int(config_from_file.get("batch_size_chiamate", 100)),
            jitter_factor=float(config_from_file.get("jitter_factor", 0.0003)),
            log_level=config_from_file.get("log_level", "INFO"),
            environment=config_from_file.get("environment", "development"),
        )

    def to_dict(self) -> dict:
        """Serializza configurazione in dizionario"""
        return {
            "ors_api_key": "***HIDDEN***",  # Chiave non esposta
            "nominatim_user_agent": self.nominatim_user_agent,
            "capacita_macchina": self.capacita_macchina,
            "bonus_corso_laurea": self.bonus_corso_laurea,
            "max_deviazione_sec": self.max_deviazione_sec,
            "numero_cluster": self.numero_cluster,
            "comune_destinazione": self.comune_destinazione,
            "batch_size_chiamate": self.batch_size_chiamate,
            "jitter_factor": self.jitter_factor,
            "log_level": self.log_level,
            "environment": self.environment,
        }

    def print_summary(self):
        """Stampa riepilogo configurazione per debug"""
        print("=== CONFIGURAZIONE APPLICAZIONE ===")
        print(f"Ambiente:              {self.environment}")
        print(f"Capacità auto:         {self.capacita_macchina} persone")
        print(f"Numero cluster:        {self.numero_cluster}")
        print(
            f"Bonus corso laurea:    {self.bonus_corso_laurea} sec ({self.bonus_corso_laurea / 60:.1f} min)"
        )
        print(
            f"Max deviazione:        {self.max_deviazione_sec} sec ({self.max_deviazione_sec / 60:.1f} min)"
        )
        print(f"Destinazione:          {self.comune_destinazione}")
        print(f"Batch size API:        {self.batch_size_chiamate}")
        print(f"Log level:             {self.log_level}")
        print()