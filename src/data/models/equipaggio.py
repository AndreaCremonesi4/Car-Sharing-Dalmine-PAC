from dataclasses import dataclass, field
from typing import List
from .studente import Studente


@dataclass
class Equipaggio:
    """Rappresenta un'auto completa con autista e passeggeri."""

    id: int  # Identificatore numerico auto
    autista: Studente  # Primo della lista, più lontano
    passeggeri: List[Studente]  # Passeggeri caricati
    percorso_tappe: List[str] = field(default_factory=list)  # Ordine località

    @property
    def membri(self) -> List[Studente]:
        """Tutti i membri dell'equipaggio (autista + passeggeri)"""
        return [self.autista] + self.passeggeri

    @property
    def capacita_utilizzata(self) -> int:
        """Numero totale persone in auto"""
        return len(self.membri)

    @property
    def corsi_rappresentati(self) -> set:
        """Set dei corsi presenti nell'equipaggio"""
        return {membro.corso for membro in self.membri}
