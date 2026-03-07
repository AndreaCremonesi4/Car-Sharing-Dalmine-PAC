from typing import List
from src.data.models.equipaggio import Equipaggio
from src.data.repositories.config_repository import ConfigRepository


class ConsoleFormatter:
    """
    Formattazione output testuale per terminale.
    """

    def __init__(self, config_repo: ConfigRepository):
        self.config_repo = config_repo

    def format_flotta(self, flotta: List[Equipaggio]) -> str:
        """Genera rappresentazione testuale della flotta"""
        if not flotta:
            return "Nessuna auto creata."

        lines = ["=== SOLUZIONE FINALE ===\n"]

        for equipaggio in flotta:
            # Ordina membri per distanza decrescente da destinazione
            membri_ordinati = sorted(
                equipaggio.membri,
                key=lambda s: s.localita,
                reverse=True,
            )

            header = f"--- Auto {equipaggio.id} ({equipaggio.capacita_utilizzata} persone) ---"
            lines.append(header)

            for membro in membri_ordinati:
                loc_display = self.config_repo.get_localita_display_name(
                    membro.localita
                )
                lines.append(
                    f"  - {membro.email} | Da: {loc_display} | Corso: {membro.corso}"
                )

            lines.append("-" * len(header))
            lines.append("")

        return "\n".join(lines)

    def print_flotta(self, flotta: List[Equipaggio]):
        """Stampa flotta su stdout"""
        print(self.format_flotta(flotta))
