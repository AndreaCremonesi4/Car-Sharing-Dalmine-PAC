import pytest
from unittest.mock import MagicMock
from src.business.orchestrators.populate_orchestrator import PopulateOrchestrator


def _make_studente(localita: str, coordinate=None):
    s = MagicMock()
    s.localita = localita
    s.coordinate = coordinate
    return s


def _make_orchestrator(studenti, n_clusters=2, cache_has_complete=False):
    studenti_repo = MagicMock()
    studenti_repo.load_studenti.return_value = studenti

    cache = MagicMock()
    cache.percorsi_cache.has_complete.return_value = cache_has_complete

    api_facade = MagicMock()
    api_facade.cache = cache
    api_facade.get_coordinate_with_cache.side_effect = lambda loc: (45.5, 9.6)

    clustering = MagicMock()
    clustering.n_clusters = n_clusters

    orchestrator = PopulateOrchestrator(
        studenti_repo=studenti_repo,
        api_facade=api_facade,
        clustering=clustering,
        comune_destinazione="DALMINE",
    )
    return orchestrator, studenti_repo, api_facade, clustering, cache


@pytest.mark.unit
def test_init_assegna_destinazione_default():
    api_facade = MagicMock()
    api_facade.cache = MagicMock()
    orc = PopulateOrchestrator(
        studenti_repo=MagicMock(),
        api_facade=api_facade,
        clustering=MagicMock(),
    )
    assert orc.destinazione == "DALMINE"


@pytest.mark.unit
def test_init_assegna_destinazione_custom():
    api_facade = MagicMock()
    api_facade.cache = MagicMock()
    orc = PopulateOrchestrator(
        studenti_repo=MagicMock(),
        api_facade=api_facade,
        clustering=MagicMock(),
        comune_destinazione="BERGAMO",
    )
    assert orc.destinazione == "BERGAMO"


@pytest.mark.unit
def test_init_cache_presa_da_api_facade():
    api_facade = MagicMock()
    cache_mock = MagicMock()
    api_facade.cache = cache_mock
    orc = PopulateOrchestrator(MagicMock(), api_facade, MagicMock())
    assert orc.cache is cache_mock


@pytest.mark.unit
def test_geocode_localita_assegna_coordinate_agli_studenti():
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Brescia")
    orc, _, api_facade, _, _ = _make_orchestrator([s1, s2])
    api_facade.get_coordinate_with_cache.side_effect = lambda loc: {
        "Bergamo": (45.69, 9.67),
        "Brescia": (45.54, 10.22),
        "DALMINE": (45.64, 9.70),
    }[loc]
    orc._geocode_localita([s1, s2])
    assert s1.coordinate == (45.69, 9.67)
    assert s2.coordinate == (45.54, 10.22)


@pytest.mark.unit
def test_geocode_localita_include_destinazione_nelle_chiamate():
    s1 = _make_studente("Bergamo")
    orc, _, api_facade, _, _ = _make_orchestrator([s1])
    orc._geocode_localita([s1])
    chiamate = [c.args[0] for c in api_facade.get_coordinate_with_cache.call_args_list]
    assert "DALMINE" in chiamate


@pytest.mark.unit
def test_geocode_localita_non_duplica_richieste_per_stessa_localita():
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Bergamo")
    orc, _, api_facade, _, _ = _make_orchestrator([s1, s2])
    orc._geocode_localita([s1, s2])
    chiamate = [c.args[0] for c in api_facade.get_coordinate_with_cache.call_args_list]
    assert chiamate.count("Bergamo") == 1


@pytest.mark.unit
def test_identifica_percorsi_restituisce_set_di_tuple():
    s1 = _make_studente("Bergamo", (45.69, 9.67))
    s2 = _make_studente("Brescia", (45.54, 10.22))
    orc, _, _, clustering, _ = _make_orchestrator([s1, s2])
    clustering.cluster_studenti.return_value = [[s1, s2]]
    result = orc._identifica_percorsi_necessari([s1, s2])
    assert isinstance(result, set)
    assert all(isinstance(p, tuple) and len(p) == 2 for p in result)


@pytest.mark.unit
def test_identifica_percorsi_include_destinazione_nel_cluster():
    s1 = _make_studente("Bergamo", (45.69, 9.67))
    orc, _, _, clustering, _ = _make_orchestrator([s1])
    clustering.cluster_studenti.return_value = [[s1]]
    result = orc._identifica_percorsi_necessari([s1])
    localita_coinvolte = {loc for coppia in result for loc in coppia}
    assert "DALMINE" in localita_coinvolte


@pytest.mark.unit
def test_identifica_percorsi_genera_permutazioni_bidirezionali():
    s1 = _make_studente("Bergamo", (45.69, 9.67))
    s2 = _make_studente("Brescia", (45.54, 10.22))
    orc, _, _, clustering, _ = _make_orchestrator([s1, s2])
    clustering.cluster_studenti.return_value = [[s1, s2]]
    result = orc._identifica_percorsi_necessari([s1, s2])
    assert ("Bergamo", "Brescia") in result
    assert ("Brescia", "Bergamo") in result


@pytest.mark.unit
def test_download_salta_se_cache_completa(capsys):
    orc, _, api_facade, _, _ = _make_orchestrator([], cache_has_complete=True)
    percorsi = {("Bergamo", "DALMINE"), ("Brescia", "DALMINE")}
    orc._download_percorsi_batch(percorsi, batch_size=1000)
    api_facade.get_percorso_with_cache.assert_not_called()
    captured = capsys.readouterr()
    assert "già completa" in captured.out


@pytest.mark.unit
def test_download_chiama_api_per_percorsi_mancanti():
    orc, _, api_facade, _, _ = _make_orchestrator([], cache_has_complete=False)
    percorsi = {("Bergamo", "DALMINE")}
    orc._download_percorsi_batch(percorsi, batch_size=1000)
    api_facade.get_percorso_with_cache.assert_called_once_with("Bergamo", "DALMINE")


@pytest.mark.unit
def test_download_rispetta_batch_size(capsys):
    orc, _, api_facade, _, _ = _make_orchestrator([], cache_has_complete=False)
    percorsi = {(f"Loc{i}", "DALMINE") for i in range(10)}
    orc._download_percorsi_batch(percorsi, batch_size=3)
    assert api_facade.get_percorso_with_cache.call_count == 3
    captured = capsys.readouterr()
    assert "Rimanenti" in captured.out


@pytest.mark.unit
def test_download_salvataggio_incrementale_ogni_10():
    orc, _, _, _, cache = _make_orchestrator([], cache_has_complete=False)
    percorsi = {(f"Loc{i}", "DALMINE") for i in range(20)}
    orc._download_percorsi_batch(percorsi, batch_size=1000)
    assert cache.save_all.call_count >= 1


@pytest.mark.unit
def test_execute_pipeline_nominale(capsys):
    s1 = _make_studente("Bergamo", (45.69, 9.67))
    s2 = _make_studente("Brescia", (45.54, 10.22))
    orc, studenti_repo, api_facade, clustering, cache = _make_orchestrator(
        [s1, s2], n_clusters=2, cache_has_complete=True
    )
    clustering.cluster_studenti.return_value = [[s1], [s2]]
    api_facade.get_coordinate_with_cache.side_effect = lambda loc: (45.5, 9.6)
    orc.execute()
    studenti_repo.load_studenti.assert_called_once()
    clustering.cluster_studenti.assert_called_once()
    cache.save_all.assert_called()
    captured = capsys.readouterr()
    assert "Popolamento completato" in captured.out


@pytest.mark.unit
def test_execute_raise_value_error_se_studenti_insufficienti():
    s1 = _make_studente("Bergamo", None)
    s2 = _make_studente("Brescia", None)
    orc, _, api_facade, _, _ = _make_orchestrator([s1, s2], n_clusters=5)
    api_facade.get_coordinate_with_cache.return_value = None
    with pytest.raises(ValueError, match="Studenti insufficienti"):
        orc.execute()


@pytest.mark.unit
def test_execute_chiama_save_all_finale():
    s1 = _make_studente("Bergamo", (45.69, 9.67))
    orc, _, api_facade, clustering, cache = _make_orchestrator(
        [s1], n_clusters=1, cache_has_complete=True
    )
    clustering.cluster_studenti.return_value = [[s1]]
    api_facade.get_coordinate_with_cache.side_effect = lambda loc: (45.5, 9.6)
    orc.execute()
    cache.save_all.assert_called()
