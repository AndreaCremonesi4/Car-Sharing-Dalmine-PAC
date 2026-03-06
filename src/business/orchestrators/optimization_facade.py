from typing import List, Dict
from ..clustering.base import ClusteringStrategy
from ..optimization.base import OptimizationStrategy
from src.data.models.studente import Studente
from src.data.models.equipaggio import Equipaggio
from src.data.models.percorso import Percorso


class OptimizationFacade:
    """
    Facade che coordina clustering + ottimizzazione.
    API semplificata per l'orchestrator principale.
    """

    def __init__(self, clustering: ClusteringStrategy, optimizer: OptimizationStrategy):
        self.clustering = clustering
        self.optimizer = optimizer

    def optimize_full(
        self, studenti: List[Studente], percorsi: Dict[str, Percorso]
    ) -> List[Equipaggio]:
        """
        Pipeline completo: clustering + ottimizzazione multi-cluster.
        """
        # 1. Clustering geografico
        clusters = self.clustering.cluster_studenti(studenti)
        print(f"Creati {len(clusters)} cluster")

        # 2. Ottimizzazione per cluster
        flotta = []
        for i, cluster in enumerate(clusters, 1):
            print(
                f"Ottimizzazione cluster {i}/{len(clusters)} "
                f"({len(cluster)} studenti)..."
            )
            equipaggi = self.optimizer.optimize_cluster(cluster, percorsi)
            flotta.extend(equipaggi)

        return flotta