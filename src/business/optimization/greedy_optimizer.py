from typing import List, Dict, Optional
from .base import OptimizationStrategy
from src.data.models.studente import Studente
from src.data.models.equipaggio import Equipaggio
from src.data.models.percorso import Percorso


class GreedyOptimizer(OptimizationStrategy):
    """
    Algoritmo greedy per formazione equipaggi.
    Logica: autista = più lontano, passeggeri = minima deviazione con bonus corso.
    """

    def __init__(
        self,
        capacita_auto: int,
        bonus_corso_laurea: int,
        max_deviazione_sec: int,
        comune_destinazione: str = "DALMINE",
    ):
        self.capacita_auto = capacita_auto
        self.bonus_corso = bonus_corso_laurea
        self.max_deviazione = max_deviazione_sec
        self.destinazione = comune_destinazione

    def optimize_cluster(
        self, cluster: List[Studente], percorsi: Dict[str, Percorso]
    ) -> List[Equipaggio]:
        """
        Implementazione algoritmo greedy.
        """
        equipaggi = []
        non_assegnati = self._ordina_per_distanza(cluster, percorsi)
        equipaggio_id = 1

        while non_assegnati:
            # Autista = più lontano
            autista = non_assegnati.pop(0)
            membri = [autista]

            # Riempi auto
            while len(membri) < self.capacita_auto and non_assegnati:
                candidato = self._trova_miglior_passeggero(
                    membri, non_assegnati, percorsi
                )

                if candidato:
                    membri.append(candidato)
                    non_assegnati.remove(candidato)
                else:
                    break  # Nessuno compatibile

            # Crea equipaggio
            equipaggio = Equipaggio(
                id=equipaggio_id,
                autista=autista,
                passeggeri=membri[1:],
                percorso_tappe=self._calcola_tappe(membri, percorsi),
            )
            equipaggi.append(equipaggio)
            equipaggio_id += 1

        return equipaggi

    def _ordina_per_distanza(self, cluster, percorsi) -> List[Studente]:
        """Ordina studenti dal più lontano al più vicino da destinazione"""
        return sorted(
            cluster, key=lambda s: self._get_durata_a_dest(s, percorsi), reverse=True
        )

    def _get_durata_a_dest(self, studente: Studente, percorsi: Dict) -> float:
        """Helper per ottenere durata verso destinazione"""
        key = f"{studente.localita}-{self.destinazione}"
        percorso = percorsi.get(key)
        return percorso.durata_sec if percorso else float("inf")

    def _trova_miglior_passeggero(
        self, membri_attuali: List[Studente], candidati: List[Studente], percorsi: Dict
    ) -> Optional[Studente]:
        """
        Trova candidato con minima deviazione pesata dal bonus corso.
        Implementa la formula: Score = Deviazione - Bonus.
        """
        ultimo = membri_attuali[-1]
        corsi_presenti = {m.corso for m in membri_attuali}

        miglior_candidato = None
        miglior_score = float("inf")

        for candidato in candidati:
            # Caso speciale: stessa località
            if ultimo.localita == candidato.localita:
                deviazione = 0
            else:
                deviazione = self._calcola_deviazione(
                    ultimo.localita, candidato.localita, percorsi
                )

            # Filtro tolleranza
            if deviazione > self.max_deviazione:
                continue

            # Bonus se stesso corso
            bonus = self.bonus_corso if candidato.corso in corsi_presenti else 0
            score = deviazione - bonus

            if score < miglior_score:
                miglior_score = score
                miglior_candidato = candidato

        return miglior_candidato

    def _calcola_deviazione(self, loc_a: str, loc_b: str, percorsi: Dict) -> float:
        """
        Calcola deviazione temporale: (A->B->Dest) - (A->Dest).
        
        """
        p_ab = percorsi.get(f"{loc_a}-{loc_b}")
        p_b_dest = percorsi.get(f"{loc_b}-{self.destinazione}")
        p_a_dest = percorsi.get(f"{loc_a}-{self.destinazione}")

        if not (p_ab and p_b_dest and p_a_dest):
            return float("inf")  # Dati mancanti

        tempo_con_deviazione = p_ab.durata_sec + p_b_dest.durata_sec
        tempo_diretto = p_a_dest.durata_sec

        return tempo_con_deviazione - tempo_diretto

    def _calcola_tappe(self, membri: List[Studente], percorsi: Dict) -> List[str]:
        """Ordina tappe per durata decrescente verso destinazione"""
        tappe_ordinate = sorted(
            membri, key=lambda s: self._get_durata_a_dest(s, percorsi), reverse=True
        )
        localita = [s.localita for s in tappe_ordinate]
        localita.append(self.destinazione)
        return localita