from abc import ABC, abstractmethod
from typing import List
from src.data.models.studente import Studente


class ClusteringStrategy(ABC):
    """
    Interfaccia per algoritmi di clustering.
    Permette di implementare strategie alternative
    mantenendo il resto del codice invariato.
    """

    @abstractmethod
    def cluster_studenti(self, studenti: List[Studente]) -> List[List[Studente]]:
        """
        Raggruppa studenti in cluster geografici.

        Args:
            studenti: Lista studenti con coordinate già popolate

        Returns:
            Lista di cluster (ogni cluster è una lista di studenti)
        """
        pass
