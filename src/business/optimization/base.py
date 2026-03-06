from abc import ABC, abstractmethod
from typing import List, Dict
from src.data.models.studente import Studente
from src.data.models.equipaggio import Equipaggio
from src.data.models.percorso import Percorso


class OptimizationStrategy(ABC):
    """
    Interfaccia per algoritmi di ottimizzazione.

    """

    @abstractmethod
    def optimize_cluster(
        self, cluster: List[Studente], percorsi: Dict[str, Percorso]
    ) -> List[Equipaggio]:
        """
        Forma equipaggi ottimali da un cluster di studenti.

        Args:
            cluster: Studenti dello stesso cluster geografico
            percorsi: Mappa chiave->Percorso per lookup veloce

        Returns:
            Lista equipaggi formati
        """
        pass