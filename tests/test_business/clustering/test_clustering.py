import pytest
from unittest.mock import MagicMock
from src.business.clustering.kmeans_clustering import KMeansClusteringService


def _make_studente(coordinate):
    s = MagicMock()
    s.coordinate = coordinate
    return s


@pytest.fixture
def sei_studenti_validi():
    return [
        _make_studente((45.6, 9.7)),
        _make_studente((45.5, 9.6)),
        _make_studente((45.4, 9.5)),
        _make_studente((45.7, 9.8)),
        _make_studente((45.3, 9.4)),
        _make_studente((45.8, 9.9)),
    ]


@pytest.mark.unit
def test_output_e_lista_di_liste(sei_studenti_validi):
    service = KMeansClusteringService(n_clusters=2)
    result = service.cluster_studenti(sei_studenti_validi)
    assert isinstance(result, list)
    assert all(isinstance(c, list) for c in result)


@pytest.mark.unit
def test_numero_cluster_non_supera_n_clusters(sei_studenti_validi):
    service = KMeansClusteringService(n_clusters=3)
    result = service.cluster_studenti(sei_studenti_validi)
    assert len(result) <= 3


@pytest.mark.unit
def test_tutti_gli_studenti_validi_assegnati(sei_studenti_validi):
    service = KMeansClusteringService(n_clusters=2)
    result = service.cluster_studenti(sei_studenti_validi)
    assegnati = [s for cluster in result for s in cluster]
    assert len(assegnati) == len(sei_studenti_validi)


@pytest.mark.unit
def test_nessun_cluster_vuoto_restituito(sei_studenti_validi):
    service = KMeansClusteringService(n_clusters=2)
    result = service.cluster_studenti(sei_studenti_validi)
    assert all(len(c) > 0 for c in result)


@pytest.mark.unit
def test_singolo_cluster_contiene_tutti(sei_studenti_validi):
    service = KMeansClusteringService(n_clusters=1)
    result = service.cluster_studenti(sei_studenti_validi)
    assert len(result) == 1
    assert len(result[0]) == len(sei_studenti_validi)


@pytest.mark.unit
def test_studenti_senza_coordinate_esclusi_dal_risultato():
    studenti = [
        _make_studente((45.6, 9.7)),
        _make_studente((45.5, 9.6)),
        _make_studente(None),
        _make_studente((45.4, 9.5)),
    ]
    service = KMeansClusteringService(n_clusters=2)
    result = service.cluster_studenti(studenti)
    assegnati = [s for cluster in result for s in cluster]
    assert all(s.coordinate is not None for s in assegnati)


@pytest.mark.unit
def test_studente_none_non_compare_in_nessun_cluster():
    studente_senza_coord = _make_studente(None)
    studenti = [
        _make_studente((45.6, 9.7)),
        _make_studente((45.5, 9.6)),
        studente_senza_coord,
        _make_studente((45.4, 9.5)),
    ]
    service = KMeansClusteringService(n_clusters=2)
    result = service.cluster_studenti(studenti)
    assegnati = [s for cluster in result for s in cluster]
    assert studente_senza_coord not in assegnati


@pytest.mark.unit
def test_value_error_se_studenti_validi_insufficienti():
    studenti = [_make_studente((45.6, 9.7)), _make_studente((45.5, 9.6))]
    service = KMeansClusteringService(n_clusters=5)
    with pytest.raises(ValueError, match="Studenti insufficienti"):
        service.cluster_studenti(studenti)


@pytest.mark.unit
def test_value_error_se_tutti_senza_coordinate():
    studenti = [_make_studente(None), _make_studente(None), _make_studente(None)]
    service = KMeansClusteringService(n_clusters=2)
    with pytest.raises(ValueError):
        service.cluster_studenti(studenti)


@pytest.mark.unit
@pytest.mark.parametrize("n_clusters", [1, 2, 3])
def test_clustering_con_n_clusters_variabile(n_clusters):
    studenti = [_make_studente((45.0 + i * 0.1, 9.5 + i * 0.1)) for i in range(6)]
    service = KMeansClusteringService(n_clusters=n_clusters)
    result = service.cluster_studenti(studenti)
    assert len(result) <= n_clusters
    assert all(len(c) > 0 for c in result)
    assert sum(len(c) for c in result) == 6
