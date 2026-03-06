import pytest
from unittest.mock import MagicMock
from src.business.orchestrators.optimization_facade import OptimizationFacade


def _make_studente(localita: str):
    s = MagicMock()
    s.localita = localita
    return s


def _make_equipaggio():
    return MagicMock()


def _make_facade(clusters=None, equipaggi_per_cluster=None):
    clustering = MagicMock()
    optimizer = MagicMock()

    clustering.cluster_studenti.return_value = clusters or []
    optimizer.optimize_cluster.side_effect = equipaggi_per_cluster or (lambda c, p: [])

    facade = OptimizationFacade(clustering=clustering, optimizer=optimizer)
    return facade, clustering, optimizer


@pytest.mark.unit
def test_init_assegna_clustering_e_optimizer():
    clustering = MagicMock()
    optimizer = MagicMock()
    facade = OptimizationFacade(clustering=clustering, optimizer=optimizer)
    assert facade.clustering is clustering
    assert facade.optimizer is optimizer


@pytest.mark.unit
def test_optimize_full_restituisce_lista():
    facade, _, _ = _make_facade(clusters=[[]])
    result = facade.optimize_full([], {})
    assert isinstance(result, list)


@pytest.mark.unit
def test_optimize_full_chiama_cluster_studenti():
    studenti = [_make_studente("Bergamo")]
    facade, clustering, _ = _make_facade(clusters=[studenti])
    facade.optimize_full(studenti, {})
    clustering.cluster_studenti.assert_called_once_with(studenti)


@pytest.mark.unit
def test_optimize_full_chiama_optimize_cluster_per_ogni_cluster():
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Brescia")
    s3 = _make_studente("Milano")
    clusters = [[s1, s2], [s3]]
    percorsi = {"Bergamo-DALMINE": MagicMock()}
    facade, _, optimizer = _make_facade(
        clusters=clusters, equipaggi_per_cluster=lambda c, p: []
    )
    facade.optimize_full([s1, s2, s3], percorsi)
    assert optimizer.optimize_cluster.call_count == 2
    optimizer.optimize_cluster.assert_any_call([s1, s2], percorsi)
    optimizer.optimize_cluster.assert_any_call([s3], percorsi)


@pytest.mark.unit
def test_optimize_full_aggrega_equipaggi_di_tutti_i_cluster():
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Brescia")
    eq1 = _make_equipaggio()
    eq2 = _make_equipaggio()
    eq3 = _make_equipaggio()
    clusters = [[s1], [s2]]
    risposte = iter([[eq1, eq2], [eq3]])
    facade, _, _ = _make_facade(
        clusters=clusters, equipaggi_per_cluster=lambda c, p: next(risposte)
    )
    result = facade.optimize_full([s1, s2], {})
    assert result == [eq1, eq2, eq3]


@pytest.mark.unit
def test_optimize_full_nessun_cluster_restituisce_lista_vuota():
    facade, _, _ = _make_facade(clusters=[])
    result = facade.optimize_full([], {})
    assert result == []


@pytest.mark.unit
def test_optimize_full_passa_percorsi_invariati_a_optimizer():
    s1 = _make_studente("Bergamo")
    percorsi = {"Bergamo-DALMINE": MagicMock()}
    facade, _, optimizer = _make_facade(
        clusters=[[s1]], equipaggi_per_cluster=lambda c, p: []
    )
    facade.optimize_full([s1], percorsi)
    _, _ = optimizer.optimize_cluster.call_args
    chiamata_args = optimizer.optimize_cluster.call_args.args
    assert chiamata_args[1] is percorsi


@pytest.mark.unit
def test_optimize_full_cluster_senza_equipaggi_non_aggiunge_nulla():
    s1 = _make_studente("Bergamo")
    facade, _, _ = _make_facade(clusters=[[s1]], equipaggi_per_cluster=lambda c, p: [])
    result = facade.optimize_full([s1], {})
    assert result == []


@pytest.mark.unit
def test_optimize_full_stampa_numero_cluster(capsys):
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Brescia")
    facade, _, _ = _make_facade(
        clusters=[[s1], [s2]], equipaggi_per_cluster=lambda c, p: []
    )
    facade.optimize_full([s1, s2], {})
    captured = capsys.readouterr()
    assert "2" in captured.out


@pytest.mark.unit
def test_optimize_full_stampa_avanzamento_cluster(capsys):
    s1 = _make_studente("Bergamo")
    facade, _, _ = _make_facade(clusters=[[s1]], equipaggi_per_cluster=lambda c, p: [])
    facade.optimize_full([s1], {})
    captured = capsys.readouterr()
    assert "1/1" in captured.out