import argparse
from dataclasses import dataclass


@dataclass
class ProgramConfig:
    """Configurazione programma da argomenti CLI"""

    mode: str  # 'popola' o 'ottimizza'


class CLIArgumentParser:
    """
    Parser argomenti linea di comando.
    """

    def parse(self) -> ProgramConfig:
        parser = argparse.ArgumentParser(
            description="Sistema carpooling universitario Dalmine",
            formatter_class=argparse.RawTextHelpFormatter,
        )

        parser.add_argument(
            "modalita",
            choices=["popola", "ottimizza"],
            help="""Modalità di esecuzione:
  popola    - Scarica dati da API e popola cache (lento, richiede Internet)
  ottimizza - Calcola equipaggi usando cache (veloce, offline)""",
        )

        args = parser.parse_args()
        return ProgramConfig(mode=args.modalita)
