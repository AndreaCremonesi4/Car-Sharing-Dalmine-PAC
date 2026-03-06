import pytest
from unittest.mock import MagicMock
from src.business.optimization.greedy_optimizer import GreedyOptimizer


def _make_studente(localita: str, corso: str = "Ingegneria"):
    s = MagicMock()
    s.localita = localita
    s.corso = corso
    return s


def _make_percorso(durata_sec: float):
    p = MagicMock()
    p.durata_sec = durata_sec
    return p


def _make_percorsi(definizioni: dict) -> dict:
    return {k: _make_percorso(v) for k, v in definizioni.items()}


def _make_optimizer(capacita=4, bonus=300, max_dev=600):
    return GreedyOptimizer(
        capacita_auto=capacita,
        bonus_corso_laurea=bonus,
        max_deviazione_sec=max_dev,
        comune_destinazione="DALMINE",
    )


@pytest.mark.unit
def test_init_destinazione_default():
    orc = GreedyOptimizer(
        capacita_auto=4, bonus_corso_laurea=300, max_deviazione_sec=600
    )
    assert orc.destinazione == "DALMINE"


@pytest.mark.unit
def test_init_destinazione_custom():
    orc = GreedyOptimizer(
        capacita_auto=4,
        bonus_corso_laurea=300,
        max_deviazione_sec=600,
        comune_destinazione="BERGAMO",
    )
    assert orc.destinazione == "BERGAMO"


@pytest.mark.unit
def test_optimize_cluster_restituisce_lista():
    opt = _make_optimizer()
    s1 = _make_studente("Bergamo")
    percorsi = _make_percorsi({"Bergamo-DALMINE": 1200})
    result = opt.optimize_cluster([s1], percorsi)
    assert isinstance(result, list)


@pytest.mark.unit
def test_optimize_cluster_tutti_gli_studenti_assegnati():
    opt = _make_optimizer(capacita=4)
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Brescia")
    s3 = _make_studente("Milano")
    percorsi = _make_percorsi(
        {
            "Bergamo-DALMINE": 1200,
            "Brescia-DALMINE": 900,
            "Milano-DALMINE": 600,
            "Bergamo-Brescia": 400,
            "Bergamo-Milano": 500,
            "Brescia-Milano": 300,
            "Brescia-Bergamo": 400,
            "Milano-Bergamo": 500,
            "Milano-Brescia": 300,
        }
    )
    result = opt.optimize_cluster([s1, s2, s3], percorsi)
    assegnati = [e.autista for e in result] + [p for e in result for p in e.passeggeri]
    assert len(assegnati) == 3


@pytest.mark.unit
def test_optimize_cluster_autista_e_il_piu_lontano():
    opt = _make_optimizer(capacita=2)
    s_vicino = _make_studente("Brescia")
    s_lontano = _make_studente("Bergamo")
    percorsi = _make_percorsi(
        {
            "Bergamo-DALMINE": 1200,
            "Brescia-DALMINE": 600,
            "Bergamo-Brescia": 400,
            "Brescia-Bergamo": 400,
        }
    )
    result = opt.optimize_cluster([s_vicino, s_lontano], percorsi)
    assert result[0].autista is s_lontano


@pytest.mark.unit
def test_optimize_cluster_singolo_studente_crea_un_equipaggio():
    opt = _make_optimizer()
    s1 = _make_studente("Bergamo")
    percorsi = _make_percorsi({"Bergamo-DALMINE": 1200})
    result = opt.optimize_cluster([s1], percorsi)
    assert len(result) == 1
    assert result[0].autista is s1
    assert result[0].passeggeri == []


@pytest.mark.unit
def test_optimize_cluster_rispetta_capacita_auto():
    opt = _make_optimizer(capacita=2, max_dev=99999)
    studenti = [_make_studente(f"Loc{i}") for i in range(4)]
    percorsi = {}
    for i in range(4):
        percorsi[f"Loc{i}-DALMINE"] = 1000 - i * 100
        for j in range(4):
            if i != j:
                percorsi[f"Loc{i}-Loc{j}"] = 100
    result = opt.optimize_cluster(studenti, _make_percorsi(percorsi))
    assert all(len(e.passeggeri) + 1 <= 2 for e in result)


@pytest.mark.unit
def test_optimize_cluster_id_equipaggi_incrementali():
    opt = _make_optimizer(capacita=1)
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Brescia")
    percorsi = _make_percorsi(
        {
            "Bergamo-DALMINE": 1200,
            "Brescia-DALMINE": 600,
        }
    )
    result = opt.optimize_cluster([s1, s2], percorsi)
    ids = [e.id for e in result]
    assert ids == list(range(1, len(result) + 1))


@pytest.mark.unit
def test_get_durata_a_dest_percorso_presente():
    opt = _make_optimizer()
    s = _make_studente("Bergamo")
    percorsi = _make_percorsi({"Bergamo-DALMINE": 1200})
    assert opt._get_durata_a_dest(s, percorsi) == pytest.approx(1200)


@pytest.mark.unit
def test_get_durata_a_dest_percorso_mancante():
    opt = _make_optimizer()
    s = _make_studente("Bergamo")
    assert opt._get_durata_a_dest(s, {}) == float("inf")


@pytest.mark.unit
def test_ordina_per_distanza_ordine_decrescente():
    opt = _make_optimizer()
    s1 = _make_studente("Vicino")
    s2 = _make_studente("Lontano")
    percorsi = _make_percorsi(
        {
            "Vicino-DALMINE": 300,
            "Lontano-DALMINE": 1500,
        }
    )
    result = opt._ordina_per_distanza([s1, s2], percorsi)
    assert result[0] is s2
    assert result[1] is s1


@pytest.mark.unit
def test_calcola_deviazione_formula_corretta():
    opt = _make_optimizer()
    percorsi = _make_percorsi(
        {
            "A-B": 400,
            "B-DALMINE": 300,
            "A-DALMINE": 600,
        }
    )
    result = opt._calcola_deviazione("A", "B", percorsi)
    assert result == pytest.approx((400 + 300) - 600)


@pytest.mark.unit
def test_calcola_deviazione_percorso_mancante_ritorna_inf():
    opt = _make_optimizer()
    result = opt._calcola_deviazione("A", "B", {})
    assert result == float("inf")


@pytest.mark.unit
@pytest.mark.parametrize("chiave_mancante", ["A-B", "B-DALMINE", "A-DALMINE"])
def test_calcola_deviazione_inf_se_un_percorso_mancante(chiave_mancante):
    opt = _make_optimizer()
    tutti = {"A-B": 400, "B-DALMINE": 300, "A-DALMINE": 600}
    percorsi = _make_percorsi({k: v for k, v in tutti.items() if k != chiave_mancante})
    assert opt._calcola_deviazione("A", "B", percorsi) == float("inf")


@pytest.mark.unit
def test_trova_miglior_passeggero_stesso_corso_preferito():
    opt = _make_optimizer(bonus=500, max_dev=99999)
    autista = _make_studente("Bergamo", corso="Ingegneria")
    c_stesso_corso = _make_studente("Brescia", corso="Ingegneria")
    c_altro_corso = _make_studente("Milano", corso="Economia")
    percorsi = _make_percorsi(
        {
            "Bergamo-Brescia": 400,
            "Brescia-DALMINE": 300,
            "Bergamo-DALMINE": 600,
            "Bergamo-Milano": 400,
            "Milano-DALMINE": 300,
        }
    )
    result = opt._trova_miglior_passeggero(
        [autista], [c_stesso_corso, c_altro_corso], percorsi
    )
    assert result is c_stesso_corso


@pytest.mark.unit
def test_trova_miglior_passeggero_esclude_deviazione_eccessiva():
    opt = _make_optimizer(bonus=0, max_dev=100)
    autista = _make_studente("Bergamo")
    candidato = _make_studente("Brescia")
    percorsi = _make_percorsi(
        {
            "Bergamo-Brescia": 500,
            "Brescia-DALMINE": 300,
            "Bergamo-DALMINE": 600,
        }
    )
    result = opt._trova_miglior_passeggero([autista], [candidato], percorsi)
    assert result is None


@pytest.mark.unit
def test_trova_miglior_passeggero_stessa_localita_deviazione_zero():
    opt = _make_optimizer(bonus=0, max_dev=0)
    autista = _make_studente("Bergamo")
    candidato = _make_studente("Bergamo")
    percorsi = _make_percorsi({"Bergamo-DALMINE": 600})
    result = opt._trova_miglior_passeggero([autista], [candidato], percorsi)
    assert result is candidato


@pytest.mark.unit
def test_trova_miglior_passeggero_nessun_candidato_ritorna_none():
    opt = _make_optimizer()
    autista = _make_studente("Bergamo")
    result = opt._trova_miglior_passeggero([autista], [], {})
    assert result is None


@pytest.mark.unit
def test_calcola_tappe_termina_con_destinazione():
    opt = _make_optimizer()
    s1 = _make_studente("Bergamo")
    s2 = _make_studente("Brescia")
    percorsi = _make_percorsi(
        {
            "Bergamo-DALMINE": 1200,
            "Brescia-DALMINE": 600,
        }
    )
    tappe = opt._calcola_tappe([s1, s2], percorsi)
    assert tappe[-1] == "DALMINE"


@pytest.mark.unit
def test_calcola_tappe_ordine_distanza_decrescente():
    opt = _make_optimizer()
    s_vicino = _make_studente("Brescia")
    s_lontano = _make_studente("Bergamo")
    percorsi = _make_percorsi(
        {
            "Bergamo-DALMINE": 1200,
            "Brescia-DALMINE": 600,
        }
    )
    tappe = opt._calcola_tappe([s_vicino, s_lontano], percorsi)
    assert tappe[0] == "Bergamo"
    assert tappe[1] == "Brescia"
    assert tappe[2] == "DALMINE"