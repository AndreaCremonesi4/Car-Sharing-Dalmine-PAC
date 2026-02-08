"""
Test suite per modello Percorso

Coverage target: 100% del modulo percorso.py
"""

import pytest
from src.data.models import Percorso


class TestPercorsoModel:
    def test_creazione_percorso_valido(self):
        """Verifica creazione percorso con dati validi"""
        geometria = [(9.6773, 45.6983), (9.7, 45.7), (9.75, 45.75)]

        percorso = Percorso(
            partenza="BERGAMO",
            destinazione="DALMINE",
            durata_sec=900,
            distanza_m=7500.5,
            geometria=geometria,
        )

        assert percorso.partenza == "BERGAMO"
        assert percorso.destinazione == "DALMINE"
        assert percorso.durata_sec == 900
        assert percorso.distanza_m == pytest.approx(7500.5)
        assert len(percorso.geometria) == 3
        assert percorso.geometria[0] == (9.6773, 45.6983)

    def test_property_durata_minuti(self):
        """Verifica conversione da secondi a minuti"""
        percorso = Percorso(
            partenza="MILANO",
            destinazione="BERGAMO",
            durata_sec=3600,  # 1 ora
            distanza_m=50000,
            geometria=[],
        )

        assert percorso.durata_minuti == pytest.approx(60.0)

        # Test con valore non intero
        percorso2 = Percorso(
            partenza="A",
            destinazione="B",
            durata_sec=150,
            distanza_m=1000,
            geometria=[],
        )

        assert percorso2.durata_minuti == pytest.approx(2.5)

    def test_property_distanza_km(self):
        """Verifica conversione da metri a chilometri"""
        percorso = Percorso(
            partenza="BRESCIA",
            destinazione="BERGAMO",
            durata_sec=1800,
            distanza_m=45000,
            geometria=[],
        )

        assert percorso.distanza_km == pytest.approx(45.0)

        # Test con valore decimale
        percorso2 = Percorso(
            partenza="X",
            destinazione="Y",
            durata_sec=600,
            distanza_m=5250.75,
            geometria=[],
        )

        assert percorso2.distanza_km == pytest.approx(5.25075)

    def test_geometria_vuota(self):
        """Verifica che geometria possa essere vuota"""
        percorso = Percorso(
            partenza="START",
            destinazione="END",
            durata_sec=100,
            distanza_m=500,
            geometria=[],
        )

        assert percorso.geometria == []
        assert len(percorso.geometria) == 0

    def test_from_cache_dict_valido(self):
        """Verifica factory method from_cache_dict con dati validi"""
        key = "BERGAMO-DALMINE"
        data = {
            "durata_sec": 720,
            "distanza_m": 8200.3,
            "geometria": [[9.6773, 45.6983], [9.70, 45.71], [9.75, 45.76]],
        }

        percorso = Percorso.from_cache_dict(key, data)

        assert percorso.partenza == "BERGAMO"
        assert percorso.destinazione == "DALMINE"
        assert percorso.durata_sec == 720
        assert percorso.distanza_m == pytest.approx(8200.3)
        assert len(percorso.geometria) == 3
        assert percorso.geometria[0] == (9.6773, 45.6983)
        assert percorso.geometria[1] == (9.70, 45.71)
        assert percorso.geometria[2] == (9.75, 45.76)

    def test_from_cache_dict_key_parsing(self):
        """Verifica parsing corretto della chiave composta"""
        key = "MILANO-BRESCIA"
        data = {"durata_sec": 3000, "distanza_m": 90000, "geometria": []}

        percorso = Percorso.from_cache_dict(key, data)

        assert percorso.partenza == "MILANO"
        assert percorso.destinazione == "BRESCIA"

    def test_from_cache_dict_con_localita_composte(self):
        """Verifica che località con trattini multipli sollevi ValueError"""
        key = "SESTO-SAN-GIOVANNI-DALMINE"
        data = {"durata_sec": 1200, "distanza_m": 15000, "geometria": [[9.0, 45.0]]}

        with pytest.raises(ValueError, match="too many values to unpack"):
            Percorso.from_cache_dict(key, data)

    def test_campi_obbligatori_mancanti(self):
        """Verifica che manchino gestione campi obbligatori"""
        with pytest.raises(TypeError):
            Percorso(
                partenza="BERGAMO",
                destinazione="DALMINE",
                # Mancano durata_sec, distanza_m, geometria
            )

        with pytest.raises(TypeError):
            Percorso()  # Tutti i campi mancanti

    def test_conversioni_properties_con_zero(self):
        """Verifica comportamento properties con valori zero"""
        percorso = Percorso(
            partenza="A", destinazione="B", durata_sec=0, distanza_m=0, geometria=[]
        )

        assert percorso.durata_minuti == pytest.approx(0.0)
        assert percorso.distanza_km == pytest.approx(0.0)
