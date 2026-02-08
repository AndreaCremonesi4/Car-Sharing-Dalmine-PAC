"""
Test suite per modello Equipaggio

Coverage target: 100% del modulo equipaggio.py
"""

import pytest
from src.data.models import Studente
from src.data.models import Equipaggio


class TestEquipaggioModel:
    def test_creazione_equipaggio_valido(self):
        """Verifica creazione equipaggio con autista e passeggeri"""
        autista = Studente(
            email="autista@studenti.unibg.it",
            localita="brescia",
            corso="ingegneria",
        )

        passeggero1 = Studente(
            email="pass1@studenti.unibg.it",
            localita="bergamo",
            corso="economia",
        )

        passeggero2 = Studente(
            email="pass2@studenti.unibg.it",
            localita="treviglio",
            corso="ingegneria",
        )

        equipaggio = Equipaggio(
            id=1,
            autista=autista,
            passeggeri=[passeggero1, passeggero2],
            percorso_tappe=["BRESCIA", "TREVIGLIO", "BERGAMO", "DALMINE"],
        )

        assert equipaggio.id == 1
        assert equipaggio.autista == autista
        assert len(equipaggio.passeggeri) == 2
        assert equipaggio.passeggeri[0] == passeggero1
        assert len(equipaggio.percorso_tappe) == 4

    def test_equipaggio_senza_passeggeri(self):
        """Verifica creazione equipaggio con solo autista"""
        autista = Studente(
            email="solo@studenti.unibg.it", localita="bergamo", corso="medicina"
        )

        equipaggio = Equipaggio(id=2, autista=autista, passeggeri=[])

        assert equipaggio.autista == autista
        assert len(equipaggio.passeggeri) == 0
        assert len(equipaggio.percorso_tappe) == 0

    def test_property_membri(self):
        """Verifica che membri contenga autista + passeggeri"""
        autista = Studente(
            email="autista@test.it", localita="MILANO", corso="INFORMATICA"
        )
        pass1 = Studente(email="pass1@test.it", localita="MONZA", corso="ECONOMIA")
        pass2 = Studente(email="pass2@test.it", localita="LECCO", corso="INFORMATICA")

        equipaggio = Equipaggio(id=3, autista=autista, passeggeri=[pass1, pass2])

        membri = equipaggio.membri
        assert len(membri) == 3
        assert membri[0] == autista
        assert membri[1] == pass1
        assert membri[2] == pass2

    def test_property_capacita_utilizzata(self):
        """Verifica calcolo capacità utilizzata"""
        autista = Studente(email="driver@test.it", localita="COMO", corso="FISICA")

        # Solo autista
        equipaggio = Equipaggio(id=4, autista=autista, passeggeri=[])
        assert equipaggio.capacita_utilizzata == 1

        # Con 3 passeggeri
        passeggeri = [
            Studente(email=f"pass{i}@test.it", localita="LOC", corso="CORSO")
            for i in range(3)
        ]
        equipaggio = Equipaggio(id=5, autista=autista, passeggeri=passeggeri)
        assert equipaggio.capacita_utilizzata == 4

    def test_property_corsi_rappresentati(self):
        """Verifica che corsi_rappresentati ritorni set unico"""
        autista = Studente(email="a@test.it", localita="BERGAMO", corso="INGEGNERIA")
        pass1 = Studente(email="b@test.it", localita="BRESCIA", corso="ECONOMIA")
        pass2 = Studente(
            email="c@test.it",
            localita="MONZA",
            corso="INGEGNERIA",  # Stesso corso dell'autista
        )
        pass3 = Studente(email="d@test.it", localita="LECCO", corso="MEDICINA")

        equipaggio = Equipaggio(id=6, autista=autista, passeggeri=[pass1, pass2, pass3])

        corsi = equipaggio.corsi_rappresentati
        assert isinstance(corsi, set)
        assert len(corsi) == 3
        assert "INGEGNERIA" in corsi
        assert "ECONOMIA" in corsi
        assert "MEDICINA" in corsi

    def test_campi_obbligatori_mancanti(self):
        """Verifica che manchino gestione campi obbligatori"""
        autista = Studente(email="test@test.it", localita="BERGAMO", corso="INGEGNERIA")

        with pytest.raises(TypeError):
            Equipaggio(id=1, autista=autista)  # Mancano passeggeri

        with pytest.raises(TypeError):
            Equipaggio(id=1)  # Mancano autista e passeggeri
