"""
Test suite per modello Studente

Coverage target: 100% del modulo studente.py
"""

import pytest
from src.data.models import Studente


class TestStudenteModel:
    def test_creazione_studente_valido(self):
        """Verifica creazione studente con dati validi"""
        studente = Studente(
            email="Mario.Rossi@studenti.unibg.it",
            localita="bergamo",
            corso="ingegneria",
        )

        assert studente.email == "mario.rossi@studenti.unibg.it"
        assert studente.localita == "BERGAMO"
        assert studente.corso == "INGEGNERIA"
        assert studente.coordinate is None

    def test_normalizzazione_automatica(self):
        """Verifica che __post_init__ normalizzi i dati"""
        studente = Studente(
            email="TEST@UNIBG.IT", localita="treviglio", corso="Economia"
        )

        assert studente.email == "test@unibg.it"
        assert studente.localita == "TREVIGLIO"
        assert studente.corso == "ECONOMIA"

    def test_coordinate_opzionali(self):
        """Verifica che coordinate siano opzionali"""
        studente = Studente(email="test@test.it", localita="BERGAMO", corso="MEDICINA")

        assert studente.coordinate is None

        # Assegnazione successiva
        studente.coordinate = (45.6983, 9.6773)
        assert studente.coordinate == (45.6983, 9.6773)

    def test_campi_obbligatori_mancanti(self):
        """Verifica che manchi gestione campi obbligatori"""
        with pytest.raises(TypeError):
            Studente(email="test@test.it")  # Mancano localita e corso
