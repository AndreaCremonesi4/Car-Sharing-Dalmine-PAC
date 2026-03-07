import pytest
from src.data.models import Studente, Equipaggio
from src.presentation.formatters.console_formatter import ConsoleFormatter


class DummyConfigRepo:
    """Config repo finto per test: restituisce nomi display per località."""

    def __init__(self, mapping=None):
        self._mapping = mapping or {}

    def get_localita_display_name(self, key: str):
        return self._mapping.get(key, key)


def _make_studente(email: str, localita: str, corso: str) -> Studente:
    return Studente(email=email, localita=localita, corso=corso)


def _make_equipaggio(eid: int, autista: Studente, passeggeri=None, tappe=None):
    return Equipaggio(
        id=eid,
        autista=autista,
        passeggeri=passeggeri or [],
        percorso_tappe=tappe or [],
    )


class TestConsoleFormatter:
    def test_init_accepts_config_repo(self):
        repo = DummyConfigRepo()
        formatter = ConsoleFormatter(config_repo=repo)
        assert formatter.config_repo is repo

    def test_format_flotta_vuota_ritorna_messaggio(self):
        formatter = ConsoleFormatter(config_repo=DummyConfigRepo())
        result = formatter.format_flotta([])
        assert result == "Nessuna auto creata."

    def test_format_flotta_una_auto_un_membro(self):
        mapping = {"BERGAMO": "Bergamo", "INGEGNERIA": "Ingegneria"}
        repo = DummyConfigRepo(mapping)
        formatter = ConsoleFormatter(config_repo=repo)

        autista = _make_studente("a@unibg.it", "BERGAMO", "INGEGNERIA")
        eq = _make_equipaggio(1, autista, tappe=["BERGAMO", "DALMINE"])

        result = formatter.format_flotta([eq])

        assert "=== SOLUZIONE FINALE ===" in result
        assert "Auto 1 (1 persone)" in result
        assert "a@unibg.it" in result
        assert "Bergamo" in result
        assert "INGEGNERIA" in result

    def test_format_flotta_ordina_membri_per_localita(self):
        mapping = {"BERGAMO": "Bergamo", "DALMINE": "Dalmine", "TREVIGLIO": "Treviglio"}
        repo = DummyConfigRepo(mapping)
        formatter = ConsoleFormatter(config_repo=repo)

        autista = _make_studente("autista@unibg.it", "TREVIGLIO", "ECONOMIA")
        p1 = _make_studente("p1@unibg.it", "BERGAMO", "INGEGNERIA")
        p2 = _make_studente("p2@unibg.it", "DALMINE", "MEDICINA")
        eq = _make_equipaggio(1, autista, passeggeri=[p1, p2])

        result = formatter.format_flotta([eq])

        # Header auto e tutti e tre i membri (ordinati per località in ordine decrescente)
        assert "Auto 1 (3 persone)" in result
        assert "autista@unibg.it" in result
        assert "p1@unibg.it" in result
        assert "p2@unibg.it" in result

    def test_print_flotta_stampa_su_stdout(self, capsys):
        formatter = ConsoleFormatter(config_repo=DummyConfigRepo())
        autista = _make_studente("x@unibg.it", "BERGAMO", "INGEGNERIA")
        eq = _make_equipaggio(1, autista)

        formatter.print_flotta([eq])

        out, _ = capsys.readouterr()
        assert "=== SOLUZIONE FINALE ===" in out
        assert "x@unibg.it" in out
