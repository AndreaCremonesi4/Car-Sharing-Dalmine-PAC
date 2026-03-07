import pytest
from unittest.mock import MagicMock, patch
from src.business.orchestrators.optimize_orchestrator import OptimizeOrchestrator


def _make_studente(localita: str):
    s = MagicMock()
    s.localita = localita
    return s


def _make_validation_result(is_valid: bool, errors=None):
    r = MagicMock()
    r.is_valid = is_valid
    r.errors = errors or []
    return r


def _make_orchestrator(
    studenti=None, is_valid=True, validation_errors=None, flotta=None
):
    studenti_repo = MagicMock()
    studenti_repo.load_studenti.return_value = studenti or []

    cache_repo = MagicMock()
    cache_repo.coordinate_cache.get.side_effect = lambda loc: (45.5, 9.6)
    cache_repo.percorsi_cache.data.items.return_value = []

    validator = MagicMock()
    validator.validate_cache_completeness.return_value = _make_validation_result(
        is_valid, validation_errors
    )

    optimization = MagicMock()
    optimization.optimize_full.return_value = flotta or []

    orc = OptimizeOrchestrator(
        studenti_repo=studenti_repo,
        cache_repo=cache_repo,
        validator=validator,
        optimization_facade=optimization,
    )
    return orc, studenti_repo, cache_repo, validator, optimization


@pytest.mark.unit
def test_execute_pipeline_nominale(capsys):
    studenti = [_make_studente("Bergamo")]
    eq1, eq2 = MagicMock(), MagicMock()
    orc, studenti_repo, cache_repo, validator, optimization = _make_orchestrator(
        studenti=studenti, flotta=[eq1, eq2]
    )
    result = orc.execute()
    studenti_repo.load_studenti.assert_called_once()
    validator.validate_cache_completeness.assert_called_once_with(studenti, cache_repo)
    optimization.optimize_full.assert_called_once()
    assert result == [eq1, eq2]
    assert "Ottimizzazione completata" in capsys.readouterr().out


@pytest.mark.unit
def test_execute_raise_value_error_se_cache_invalida():
    orc, _, _, _, optimization = _make_orchestrator(
        is_valid=False, validation_errors=["Coordinate mancanti per: Bergamo"]
    )
    with pytest.raises(ValueError, match="Cache incompleta"):
        orc.execute()
    optimization.optimize_full.assert_not_called()


@pytest.mark.unit
def test_execute_arricchisce_studenti_con_coordinate():
    s1 = _make_studente("Bergamo")
    orc, _, cache_repo, _, _ = _make_orchestrator(studenti=[s1])
    cache_repo.coordinate_cache.get.side_effect = lambda loc: (45.69, 9.67)
    orc.execute()
    assert s1.coordinate == (45.69, 9.67)


@pytest.mark.unit
def test_build_percorsi_dict_converte_cache_in_dict():
    orc, _, cache_repo, _, _ = _make_orchestrator()
    cache_repo.percorsi_cache.data.items.return_value = [
        ("Bergamo-DALMINE", {"durata": 1200}),
        ("Brescia-DALMINE", {"durata": 900}),
    ]
    with patch(
        "src.business.orchestrators.optimize_orchestrator.Percorso"
    ) as MockPercorso:
        MockPercorso.from_cache_dict.return_value = MagicMock()
        result = orc._build_percorsi_dict()
        assert "Bergamo-DALMINE" in result
        assert "Brescia-DALMINE" in result
        assert MockPercorso.from_cache_dict.call_count == 2


@pytest.mark.unit
def test_build_percorsi_dict_vuoto_se_cache_vuota():
    orc, _, cache_repo, _, _ = _make_orchestrator()
    cache_repo.percorsi_cache.data.items.return_value = []
    assert orc._build_percorsi_dict() == {}
