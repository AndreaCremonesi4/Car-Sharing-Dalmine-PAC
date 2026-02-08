from pathlib import Path
import json
from typing import Optional


class ConfigRepository:
    """
    Repository per configurazioni statiche immutabili.
    Legge da data/config/(localita.json, quartieri.json).
    """

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self._localita_map: Optional[dict] = None
        self._quartieri_set: Optional[set] = None

    @property
    def localita_map(self) -> dict:
        """Lazy loading della mappa località"""
        if self._localita_map is None:
            file_path = self.config_dir / "localita.json"
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._localita_map = data
        return self._localita_map

    @property
    def quartieri_set(self) -> set:
        """Lazy loading del set quartieri Bergamo"""
        if self._quartieri_set is None:
            file_path = self.config_dir / "quartieri.json"
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._quartieri_set = set(data)
        return self._quartieri_set

    def get_localita_display_name(self, key: str) -> Optional[str]:
        """Converte chiave (es. BERGAMO) in nome display (es. Bergamo)"""
        return self.localita_map.get(key)

    def is_quartiere_bergamo(self, key: str) -> bool:
        """Verifica se località è quartiere di Bergamo (per geocoding)"""
        return key in self.quartieri_set
