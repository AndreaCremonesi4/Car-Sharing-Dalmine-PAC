import pytest
from src.presentation.cli.argument_parser import CLIArgumentParser, ProgramConfig


class TestProgramConfig:
    def test_creazione_con_modo_popola(self):
        cfg = ProgramConfig(mode="popola")
        assert cfg.mode == "popola"

    def test_creazione_con_modo_ottimizza(self):
        cfg = ProgramConfig(mode="ottimizza")
        assert cfg.mode == "ottimizza"


class TestCLIArgumentParser:
    def test_parse_modalita_popola(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["script", "popola"])
        parser = CLIArgumentParser()
        result = parser.parse()
        assert isinstance(result, ProgramConfig)
        assert result.mode == "popola"

    def test_parse_modalita_ottimizza(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["script", "ottimizza"])
        parser = CLIArgumentParser()
        result = parser.parse()
        assert isinstance(result, ProgramConfig)
        assert result.mode == "ottimizza"

    def test_parse_argomento_invalido_solleva_system_exit(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["script", "invalid"])
        parser = CLIArgumentParser()
        with pytest.raises(SystemExit):
            parser.parse()
