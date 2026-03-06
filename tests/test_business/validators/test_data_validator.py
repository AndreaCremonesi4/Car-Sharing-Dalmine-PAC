import pytest
from unittest.mock import MagicMock
from src.business.validators.data_validator import DataValidator, ValidationResult


def _make_studente(localita: str):
    s = MagicMock()
    s.localita = localita
    return s


def _make_cache(
    coordinate_has=True, coordinate_get=(45.5, 9.6), percorsi_completo=True
):
    cache = MagicMock()
    cache.coordinate_cache.has.return_value = coordinate_has
    cache.coordinate_cache.get.return_value = coordinate_get
    cache.percorsi_cache.has_complete.return_value = percorsi_completo
    return cache


@pytest.mark.unit
def test_init_destinazione_default():
    v = DataValidator()
    assert v.destinazione == "DALMINE"


@pytest.mark.unit
def test_init_destinazione_custom():
    v = DataValidator(comune_destinazione="BERGAMO")
    assert v.destinazione == "BERGAMO"


@pytest.mark.unit
def test_validate_restituisce_validation_result():
    v = DataValidator()
    cache = _make_cache()
    result = v.validate_cache_completeness([_make_studente("Bergamo")], cache)
    assert isinstance(result, ValidationResult)


@pytest.mark.unit
def test_validate_is_valid_true_quando_tutto_presente():
    v = DataValidator()
    cache = _make_cache(
        coordinate_has=True, coordinate_get=(45.5, 9.6), percorsi_completo=True
    )
    result = v.validate_cache_completeness([_make_studente("Bergamo")], cache)
    assert result.is_valid is True
    assert result.errors == []


@pytest.mark.unit
def test_validate_errore_se_coordinate_mancanti():
    v = DataValidator()
    cache = _make_cache(coordinate_has=False)
    result = v.validate_cache_completeness([_make_studente("Bergamo")], cache)
    assert result.is_valid is False
    assert any("Coordinate mancanti" in e for e in result.errors)


@pytest.mark.unit
def test_validate_errore_se_coordinate_none():
    v = DataValidator()
    cache = _make_cache(coordinate_has=True, coordinate_get=None)
    result = v.validate_cache_completeness([_make_studente("Bergamo")], cache)
    assert result.is_valid is False
    assert any("non geocodificabile" in e for e in result.errors)


@pytest.mark.unit
def test_validate_errore_se_percorso_mancante():
    v = DataValidator()
    cache = _make_cache(
        coordinate_has=True, coordinate_get=(45.5, 9.6), percorsi_completo=False
    )
    result = v.validate_cache_completeness([_make_studente("Bergamo")], cache)
    assert result.is_valid is False
    assert any("Percorso mancante" in e for e in result.errors)


@pytest.mark.unit
def test_validate_include_destinazione_nel_check_coordinate():
    v = DataValidator(comune_destinazione="DALMINE")
    cache = _make_cache()
    _make_studente("Bergamo")
    v.validate_cache_completeness([_make_studente("Bergamo")], cache)
    chiamate = [c.args[0] for c in cache.coordinate_cache.has.call_args_list]
    assert "DALMINE" in chiamate


@pytest.mark.unit
def test_validate_destinazione_non_controllata_per_percorsi():
    v = DataValidator(comune_destinazione="DALMINE")
    cache = _make_cache()
    v.validate_cache_completeness([_make_studente("Bergamo")], cache)
    chiamate_percorsi = [
        c.args[0] for c in cache.percorsi_cache.has_complete.call_args_list
    ]
    assert "DALMINE" not in chiamate_percorsi


@pytest.mark.unit
def test_validate_lista_studenti_vuota_controlla_solo_destinazione():
    v = DataValidator()
    cache = _make_cache()
    v.validate_cache_completeness([], cache)
    chiamate = [c.args[0] for c in cache.coordinate_cache.has.call_args_list]
    assert chiamate == ["DALMINE"]


@pytest.mark.unit
def test_validate_non_duplica_check_per_stessa_localita():
    v = DataValidator()
    cache = _make_cache()
    studenti = [_make_studente("Bergamo"), _make_studente("Bergamo")]
    v.validate_cache_completeness(studenti, cache)
    chiamate = [c.args[0] for c in cache.coordinate_cache.has.call_args_list]
    assert chiamate.count("Bergamo") == 1


@pytest.mark.unit
@pytest.mark.parametrize("localita", ["Bergamo", "Brescia", "Milano"])
def test_validate_controlla_percorso_verso_destinazione_per_ogni_localita(localita):
    v = DataValidator()
    cache = _make_cache()
    v.validate_cache_completeness([_make_studente(localita)], cache)
    cache.percorsi_cache.has_complete.assert_any_call(localita, "DALMINE")


@pytest.mark.unit
def test_validate_errori_multipli_tutti_presenti_nella_lista():
    v = DataValidator()
    cache = _make_cache(coordinate_has=False, percorsi_completo=False)
    studenti = [_make_studente("Bergamo"), _make_studente("Brescia")]
    result = v.validate_cache_completeness(studenti, cache)
    assert result.is_valid is False
    assert len(result.errors) >= 2
