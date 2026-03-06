import numpy as np
from sklearn.cluster import KMeans
from typing import List
from .base import ClusteringStrategy
from src.data.models.studente import Studente


class KMeansClusteringService(ClusteringStrategy):
    """
    Implementazione clustering con K-Means.
    Raggruppa studenti per vicinanza geografica.
    """

    def __init__(self, n_clusters: int):
        self.n_clusters = n_clusters

    def cluster_studenti(self, studenti: List[Studente]) -> List[List[Studente]]:
        """
        Applica K-Means alle coordinate degli studenti.
        """
        # Filtra studenti senza coordinate
        studenti_validi = [s for s in studenti if s.coordinate is not None]

        if len(studenti_validi) < self.n_clusters:
            raise ValueError(
                f"Studenti insufficienti ({len(studenti_validi)}) "
                f"per {self.n_clusters} cluster"
            )

        # Matrice coordinate
        coordinate_matrix = np.array([s.coordinate for s in studenti_validi])

        # Esecuzione K-Means
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=0, n_init="auto").fit(
            coordinate_matrix
        )

        # Raggruppa studenti per label
        clusters = [[] for _ in range(self.n_clusters)]
        for studente, label in zip(studenti_validi, kmeans.labels_):
            clusters[label].append(studente)

        # Filtra cluster vuoti
        return [c for c in clusters if c]
