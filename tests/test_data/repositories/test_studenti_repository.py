import pytest
import json
from pathlib import Path
from src.data.repositories import StudentiRepository
from src.data.models import Studente


class DummyConfigRepo:
    """Stub minimale con solo get_localita_display_name."""

    def __init__(self, mapping):
        self._mapping = mapping

    def get_localita_display_name(self, key: str):
        return self._mapping.get(key)


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_load_studenti_success(tmp_path):
    studenti_file = tmp_path / "studenti.json"
    data = [
        {
            "email": "MARIO.ROSSI@STUDENTI.UNIBG.IT",
            "localita": "bergamo",
            "corso": "ingegneria",
        },
        {"email": "test2@test.it", "localita": "DALMINE", "corso": "ECONOMIA"},
    ]
    _write_json(studenti_file, data)

    config_repo = DummyConfigRepo({"BERGAMO": "Bergamo", "DALMINE": "Dalmine"})
    repo = StudentiRepository(studenti_file, config_repo)

    studenti = repo.load_studenti()

    assert len(studenti) == 2
    assert all(isinstance(s, Studente) for s in studenti)

    s1 = studenti[0]
    assert s1.email == "mario.rossi@studenti.unibg.it"
    assert s1.localita == "BERGAMO"
    assert s1.corso == "INGEGNERIA"


def test_load_studenti_file_mancante(tmp_path):
    studenti_file = tmp_path / "studenti.json"
    config_repo = DummyConfigRepo({})
    repo = StudentiRepository(studenti_file, config_repo)

    with pytest.raises(FileNotFoundError):
        repo.load_studenti()


def test_load_studenti_salti_entry_con_campi_mancanti(tmp_path, capsys):
    studenti_file = tmp_path / "studenti.json"
    data = [
        {"email": "ok@test.it", "localita": "BERGAMO", "corso": "INGEGNERIA"},
        {"email": "manca_corso@test.it", "localita": "DALMINE"},  # manca 'corso'
    ]
    _write_json(studenti_file, data)

    config_repo = DummyConfigRepo({"BERGAMO": "Bergamo", "DALMINE": "Dalmine"})
    repo = StudentiRepository(studenti_file, config_repo)

    studenti = repo.load_studenti()

    captured = capsys.readouterr()
    assert "campo mancante" in captured.out
    assert len(studenti) == 1
    assert studenti[0].email == "ok@test.it"


def test_load_studenti_localita_sconosciuta(tmp_path, capsys):
    studenti_file = tmp_path / "studenti.json"
    data = [
        {"email": "unknown@test.it", "localita": "ATLANTIDE", "corso": "INGEGNERIA"},
    ]
    _write_json(studenti_file, data)

    config_repo = DummyConfigRepo({})  # nessuna località mappata
    repo = StudentiRepository(studenti_file, config_repo)

    studenti = repo.load_studenti()

    captured = capsys.readouterr()
    assert "Località sconosciuta" in captured.out
    assert len(studenti) == 1
    assert studenti[0].localita == "ATLANTIDE".upper()