import json
from pathlib import Path

from src.data.repositories import ConfigRepository


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_lazy_loading_localita_e_quartieri(tmp_path):
    config_dir = tmp_path / "config"
    _write_json(
        config_dir / "localita.json", {"BERGAMO": "Bergamo", "DALMINE": "Dalmine"}
    )
    _write_json(config_dir / "quartieri.json", ["REDONA", "CITTA_ALTA"])

    repo = ConfigRepository(config_dir)

    # Prima chiamata carica da disco
    mappa1 = repo.localita_map
    quartieri1 = repo.quartieri_set

    # Chiamate successive riusano gli stessi oggetti
    mappa2 = repo.localita_map
    quartieri2 = repo.quartieri_set

    assert mappa1 == {"BERGAMO": "Bergamo", "DALMINE": "Dalmine"}
    assert quartieri1 == {"REDONA", "CITTA_ALTA"}
    assert mappa1 is mappa2
    assert quartieri1 is quartieri2


def test_get_localita_display_name_e_quartiere(tmp_path):
    config_dir = tmp_path / "config"
    _write_json(config_dir / "localita.json", {"BERGAMO": "Bergamo"})
    _write_json(config_dir / "quartieri.json", ["CITTA_ALTA"])

    repo = ConfigRepository(config_dir)

    assert repo.get_localita_display_name("BERGAMO") == "Bergamo"
    assert repo.get_localita_display_name("DALMINE") is None

    assert repo.is_quartiere_bergamo("CITTA_ALTA") is True
    assert repo.is_quartiere_bergamo("BERGAMO") is False