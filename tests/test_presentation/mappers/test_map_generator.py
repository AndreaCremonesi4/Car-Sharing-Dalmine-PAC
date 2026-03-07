import pytest
from unittest.mock import MagicMock, patch
from src.data.models import Studente, Equipaggio
from src.presentation.mappers.map_generator import MapGenerator


def _make_studente(email: str, localita: str, corso: str) -> Studente:
    return Studente(email=email, localita=localita, corso=corso)


def _make_equipaggio(eid: int, autista: Studente, passeggeri=None, tappe=None):
    return Equipaggio(
        id=eid,
        autista=autista,
        passeggeri=passeggeri or [],
        percorso_tappe=tappe or [],
    )


class TestMapGeneratorInit:
    def test_jitter_factor_default(self):
        gen = MapGenerator()
        assert gen.jitter_factor == pytest.approx(0.0003)

    def test_jitter_factor_custom(self):
        gen = MapGenerator(jitter_factor=0.001)
        assert gen.jitter_factor == pytest.approx(0.001)

    def test_colori_elenco_non_vuoto(self):
        gen = MapGenerator()
        assert len(gen.colori) > 0
        assert "red" in gen.colori
        assert "blue" in gen.colori


class TestMapGeneratorGenerate:
    def test_generate_crea_directory_e_salva_file(self, tmp_path, monkeypatch):
        output_path = tmp_path / "out" / "mappa.html"

        mock_map = MagicMock()
        mock_folium = MagicMock()
        mock_folium.Map.return_value = mock_map

        coord_cache = MagicMock()
        coord_cache.get.return_value = (45.695, 9.67)

        percorsi_cache = MagicMock()
        percorsi_cache.get.return_value = None

        cache_repo = MagicMock()
        cache_repo.coordinate_cache = coord_cache
        cache_repo.percorsi_cache = percorsi_cache

        gen = MapGenerator(jitter_factor=0.0001)

        with patch("src.presentation.mappers.map_generator.folium", mock_folium):
            gen.generate([], output_path, cache_repo)

        coord_cache.get.assert_called_with("DALMINE")
        mock_folium.Map.assert_called_once()
        mock_map.save.assert_called_once_with(str(output_path))
        assert output_path.parent.exists()

    def test_generate_fallback_coords_se_dalmine_mancante(self, tmp_path, monkeypatch):
        output_path = tmp_path / "mappa.html"
        mock_map = MagicMock()
        mock_folium = MagicMock()
        mock_folium.Map.return_value = mock_map

        coord_cache = MagicMock()
        coord_cache.get.return_value = None  # DALMINE non in cache

        cache_repo = MagicMock()
        cache_repo.coordinate_cache = coord_cache
        cache_repo.percorsi_cache = MagicMock()
        cache_repo.percorsi_cache.get.return_value = None

        gen = MapGenerator()

        with patch("src.presentation.mappers.map_generator.folium", mock_folium):
            gen.generate([], output_path, cache_repo)

        # Fallback (45.695, 9.67) usato per Map (passato come location=)
        call_args = mock_folium.Map.call_args
        assert call_args.kwargs.get("location") == (45.695, 9.67)

    def test_generate_aggiunge_marker_destinazione_e_equipaggi(
        self, tmp_path, monkeypatch
    ):
        output_path = tmp_path / "mappa.html"
        mock_map = MagicMock()
        mock_folium = MagicMock()
        mock_folium.Map.return_value = mock_map
        mock_folium.Marker = MagicMock(return_value=MagicMock())
        mock_folium.PolyLine = MagicMock(return_value=MagicMock())
        mock_folium.Icon = MagicMock(return_value=MagicMock())

        coord_cache = MagicMock()
        coord_cache.get.side_effect = lambda loc: (
            (45.7, 9.6) if loc == "BERGAMO" else (45.695, 9.67)
        )

        percorsi_cache = MagicMock()
        percorsi_cache.get.return_value = None

        cache_repo = MagicMock()
        cache_repo.coordinate_cache = coord_cache
        cache_repo.percorsi_cache = percorsi_cache

        autista = _make_studente("a@unibg.it", "BERGAMO", "INGEGNERIA")
        eq = _make_equipaggio(1, autista, tappe=["BERGAMO", "DALMINE"])

        gen = MapGenerator(jitter_factor=0.0)

        with (
            patch("src.presentation.mappers.map_generator.folium", mock_folium),
            patch(
                "src.presentation.mappers.map_generator.random.uniform",
                lambda a, b: 0.0,
            ),
        ):
            gen.generate([eq], output_path, cache_repo)

        # Almeno Marker (destinazione + membri) chiamati
        assert mock_folium.Marker.call_count >= 1
        mock_map.save.assert_called_once()
