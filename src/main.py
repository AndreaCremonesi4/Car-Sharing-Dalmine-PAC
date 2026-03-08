import sys
import traceback
import time

from data.repositories import ConfigRepository, CacheRepository, StudentiRepository
from business.clustering import KMeansClusteringService
from business.optimization import GreedyOptimizer
from business.orchestrators import (
    OptimizationFacade,
    PopulateOrchestrator,
    OptimizeOrchestrator,
)
from business.validators import DataValidator
from services.api import GeocodingService, RoutingService
from services import ExternalAPIFacade
from presentation.cli import CLIArgumentParser
from presentation.mappers import MapGenerator
from presentation.formatters import ConsoleFormatter
from config import PathConfig, AppConfig


def initialize_layer1_data():
    """
    Inizializza Layer 1: Data Access Layer

    Returns:
        tuple: (config_repo, cache_repo, studenti_repo)
    """

    config_repo = ConfigRepository(PathConfig.config_dir())
    cache_repo = CacheRepository(PathConfig.cache_dir())
    studenti_repo = StudentiRepository(PathConfig.studenti_file(), config_repo)

    return config_repo, cache_repo, studenti_repo


def initialize_layer2_services(app_config: AppConfig, config_repo, cache_repo):
    """
    Inizializza Layer 2: Service Layer (API adapters)

    Args:
        app_config: Configurazione applicazione
        config_repo: Repository configurazioni
        cache_repo: Repository cache

    Returns:
        ExternalAPIFacade: Facade per accesso API esterne
    """

    geocoding = GeocodingService(config_repo, app_config.nominatim_user_agent)
    routing = RoutingService(app_config.ors_api_key)
    api_facade = ExternalAPIFacade(geocoding, routing, cache_repo)

    return api_facade


def initialize_layer3_business(
    app_config: AppConfig, studenti_repo, cache_repo, api_facade
):
    """
    Inizializza Layer 3: Business Logic Layer

    Args:
        app_config: Configurazione applicazione
        studenti_repo: Repository studenti
        cache_repo: Repository cache
        api_facade: Facade API esterne

    Returns:
        tuple: (populate_orchestrator, optimize_orchestrator)
    """

    # Componenti algoritmici
    clustering = KMeansClusteringService(n_clusters=app_config.numero_cluster)

    optimizer = GreedyOptimizer(
        capacita_auto=app_config.capacita_macchina,
        bonus_corso_laurea=app_config.bonus_corso_laurea,
        max_deviazione_sec=app_config.max_deviazione_sec,
        comune_destinazione=app_config.comune_destinazione,
    )

    # Facade che coordina clustering + optimization
    optimization_facade = OptimizationFacade(clustering, optimizer)

    # Orchestratori per le due modalità
    populate_orch = PopulateOrchestrator(
        studenti_repo, api_facade, clustering, app_config.comune_destinazione
    )

    optimize_orch = OptimizeOrchestrator(
        studenti_repo,
        cache_repo,
        DataValidator(app_config.comune_destinazione),
        optimization_facade,
    )

    return populate_orch, optimize_orch


def initialize_layer4_presentation(app_config: AppConfig, config_repo):
    """
    Inizializza Layer 4: Presentation Layer

    Args:
        app_config: Configurazione applicazione
        config_repo: Repository configurazioni

    Returns:
        tuple: (cli_parser, map_generator, console_formatter)
    """

    cli_parser = CLIArgumentParser()
    map_generator = MapGenerator(jitter_factor=app_config.jitter_factor)
    console_formatter = ConsoleFormatter(config_repo)

    return cli_parser, map_generator, console_formatter


def execute_populate_mode(populate_orchestrator, app_config: AppConfig):
    """
    Esegue modalità 'popola': download dati da API e popolamento cache.

    Args:
        populate_orchestrator: Orchestratore modalità popola
        app_config: Configurazione applicazione
    """
    print("\n" + "=" * 60)
    print("MODALITÀ: POPOLA")
    print("=" * 60 + "\n")

    print("Questa modalità:")
    print("  • Geocodifica le località degli studenti")
    print("  • Identifica i percorsi necessari tramite clustering")
    print("  • Scarica i percorsi da OpenRouteService")
    print(f"  • Salva tutto in cache (batch: {app_config.batch_size_chiamate})")
    print("\n⚠  Richiede connessione Internet attiva\n")

    try:
        populate_orchestrator.execute(batch_size=app_config.batch_size_chiamate)
        print("\n" + "=" * 60)
        print("✓ POPOLAMENTO COMPLETATO")
        print("=" * 60)
        print("\nProssimo passo:")
        print("  python src/main.py ottimizza")

    except KeyboardInterrupt:
        print("\n\n⚠  Operazione interrotta dall'utente")
        print("I dati già scaricati sono stati salvati in cache.")
        print("Riesegui lo stesso comando per riprendere.\n")
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ ERRORE durante popolamento: {e}")

        traceback.print_exc()
        sys.exit(1)


def execute_optimize_mode(
    optimize_orchestrator, console_formatter, map_generator, cache_repo
):
    """
    Esegue modalità 'ottimizza': calcolo equipaggi da cache offline.

    Args:
        optimize_orchestrator: Orchestratore modalità ottimizza
        console_formatter: Formatter per output console
        map_generator: Generatore mappe HTML
        cache_repo: Repository cache (per map generator)
    """
    print("\n" + "=" * 60)
    print("MODALITÀ: OTTIMIZZA")
    print("=" * 60 + "\n")

    print("Questa modalità:")
    print("  • Carica i dati dalla cache (offline)")
    print("  • Esegue clustering geografico")
    print("  • Calcola gli equipaggi ottimali")
    print("  • Genera mappa interattiva\n")

    try:
        # Esecuzione ottimizzazione
        start_time = time.perf_counter()

        flotta = optimize_orchestrator.execute()

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Output console
        print("\n" + "=" * 60)
        console_formatter.print_flotta(flotta)
        print("=" * 60)

        # Statistiche
        totale_studenti = sum(eq.capacita_utilizzata for eq in flotta)
        avg_occupazione = totale_studenti / len(flotta) if flotta else 0

        print("\n📊 STATISTICHE:")
        print(f"  • Totale studenti:      {totale_studenti}")
        print(f"  • Auto create:          {len(flotta)}")
        print(f"  • Occupazione media:    {avg_occupazione:.1f} persone/auto")
        print(f"  • Tempo elaborazione:   {elapsed:.2f} secondi")

        # Generazione mappa
        print("\n🗺️  Generazione mappa HTML...")
        output_path = PathConfig.mappa_html_file()
        map_generator.generate(flotta, output_path, cache_repo)

        print("\n" + "=" * 60)
        print("✓ OTTIMIZZAZIONE COMPLETATA")
        print("=" * 60)
        print(f"\n📄 Mappa generata: {output_path}")
        print("   Apri il file nel browser per visualizzare i percorsi\n")

    except ValueError as e:
        # Errore di validazione cache
        print("\n✗ ERRORE DI VALIDAZIONE:\n")
        print(str(e))
        print("\nLa cache è incompleta o mancante.")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ ERRORE durante ottimizzazione: {e}")

        traceback.print_exc()
        sys.exit(1)


def main():
    """
    Entry point principale con Dependency Injection.

    Struttura:
    1. Validazione ambiente
    2. Caricamento configurazione
    3. Inizializzazione layer (1->2->3->4)
    4. Routing alla modalità richiesta
    """

    # ASCII art banner
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   CARSHARING DALMINE - Sistema di Ottimizzazione          ║
║                                                           ║
║   Università degli Studi di Bergamo                       ║
║   Polo di Dalmine                                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # === FASE 1: CARICAMENTO CONFIGURAZIONE ===
    try:
        app_config = AppConfig.from_env_and_file()
        app_config.print_summary()
    except ValueError as e:
        print(f"ERRORE CONFIGURAZIONE: {e}\n")
        sys.exit(1)

    # === FASE 2: INIZIALIZZAZIONE LAYER ===
    print("=== INIZIALIZZAZIONE COMPONENTI ===\n")

    # Layer 1: Data Access
    print("Layer 1: Data Access...")
    config_repo, cache_repo, studenti_repo = initialize_layer1_data()
    print("  ✓ Repositories inizializzati")

    # Layer 2: Services
    print("Layer 2: Services...")
    api_facade = initialize_layer2_services(app_config, config_repo, cache_repo)
    print("  ✓ API adapters inizializzati")

    # Layer 3: Business Logic
    print("Layer 3: Business Logic...")
    populate_orch, optimize_orch = initialize_layer3_business(
        app_config, studenti_repo, cache_repo, api_facade
    )
    print("  ✓ Orchestrators inizializzati")

    # Layer 4: Presentation
    print("Layer 4: Presentation...")
    cli_parser, map_generator, console_formatter = initialize_layer4_presentation(
        app_config, config_repo
    )
    print("  ✓ Presentation layer inizializzato")

    print("\n✓ Tutti i componenti pronti\n")

    # === FASE 3: PARSING ARGOMENTI E ROUTING ===
    try:
        program_config = cli_parser.parse()
    except SystemExit:
        # argparse ha già stampato l'help
        sys.exit(1)

    # === FASE 5: ESECUZIONE MODALITÀ ===
    if program_config.mode == "popola":
        execute_populate_mode(populate_orch, app_config)

    elif program_config.mode == "ottimizza":
        execute_optimize_mode(
            optimize_orch, console_formatter, map_generator, cache_repo
        )

    else:
        print(f"Modalità sconosciuta: {program_config.mode}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠  Programma interrotto dall'utente\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ ERRORE FATALE: {e}\n")

        traceback.print_exc()
        sys.exit(1)
