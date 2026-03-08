# Car-Sharing-Dalmine-PAC

Questo progetto ottimizza l'organizzazione di un servizio di car-sharing per gli studenti universitari del polo di Dalmine. Il sistema, partendo da un elenco di studenti con le loro località di partenza, calcola la composizione ottimale degli equipaggi e i percorsi per raggiungere la destinazione comune (il polo universitario).

L'obiettivo è duplice:

1. **Minimizzare il numero di auto** utilizzate.
2. **Massimizzare l'occupazione** di ciascun veicolo.

Entrambi cercando di trovare i percorsi migliori.

## Architettura

Il sistema è suddiviso in 4 layer principali:

1. **Data Access Layer**: Gestisce l'accesso a tutte le fonti di dati, sia file locali (configurazioni, cache, input) sia dati salvati in memoria.
2. **Service Layer**: Contiene gli adapter per comunicare con API esterne (OpenRouteService per il routing, Nominatim per il geocoding).
3. **Business Logic Layer**: Il cuore del sistema. Contiene:
   - **Orchestrators**: Coordinano le operazioni per le due modalità principali (`popola`, `ottimizza`).
   - **Optimization/Clustering**: Implementa gli algoritmi di K-Means per raggruppare gli studenti e un ottimizzatore greedy per creare gli equipaggi.
   - **Validators**: Assicurano l'integrità dei dati prima dell'elaborazione.
4. **Presentation Layer**: Gestisce l'interazione con l'utente, dal parsing degli argomenti da linea di comando alla formattazione dell'output in console e alla generazione di mappe HTML.

## Installazione

Per eseguire il progetto, è necessario avere Python 3.10+ installato.

1. **Clonare la repository**:

   ```bash
   git clone https://github.com/AndreaCremonesi4/Car-Sharing-Dalmine-PAC.git
   cd Car-Sharing-Dalmine-PAC
   ```

2. **Creare un ambiente virtuale** (consigliato):

   ```bash
   python -m venv venv
   source venv/bin/activate  # Su Windows: venv\Scripts\activate
   ```

3. **Installare le dipendenze**

   ```bash
   pip install -r requirements.txt
   ```

4. **Installare il progetto**:
   Il progetto è configurato come un pacchetto Python. Per installarlo insieme a tutte le sue dipendenze (incluse quelle per lo sviluppo e i test), usare il seguente comando:

   ```bash
   pip install -e .
   ```

   Questo comando installa il pacchetto in "modalità editabile", il che significa che le modifiche al codice sorgente sono immediatamente disponibili senza bisogno di reinstallare.

## Configurazione

Prima di eseguire il programma, è necessario configurare le proprie chiavi API:

1. Creare un file `.env` nella root del progetto, partendo dal template:
   ```bash
   cp .env.example .env
   ```
2. Aprire il file `.env` e inserire la propria chiave API per **OpenRouteService** alla variabile `ORS_API_KEY`.
   ```env
   # .env
   ORS_API_KEY="la_tua_chiave_api_qui"
   ```

## Funzionamento

Il programma offre due modalità principali, da eseguire in sequenza.

### 1. Popolamento della Cache (`popola`)

Questa modalità richiede una connessione Internet. Svolge le seguenti operazioni:

- **Geocodifica**: Traduce gli indirizzi di partenza degli studenti in coordinate geografiche (latitudine/longitudine) utilizzando Nominatim.
- **Clustering**: Raggruppa gli studenti in base alla loro vicinanza geografica per identificare le aree da servire.
- **Routing**: Per ogni cluster, calcola il percorso ottimale verso il polo di Dalmine utilizzando OpenRouteService.
- **Caching**: Salva tutti i dati ottenuti (coordinate, percorsi, distanze, tempi) in una cache locale su disco. Questo permette di eseguire le successive ottimizzazioni offline, senza ripetere le chiamate alle API.

**Comando:**

```bash
python src/main.py popola
```

### 2. Ottimizzazione degli Equipaggi (`ottimizza`)

Questa modalità lavora **offline** utilizzando i dati presenti in cache.

- **Validazione**: Controlla che la cache contenga tutti i dati necessari.
- **Ottimizzazione**: Esegue un algoritmo greedy per assegnare gli studenti alle auto, cercando di massimizzare il numero di passeggeri e rispettando i vincoli (es. capacità massima del veicolo).
- **Output**:
  - Stampa in console un report dettagliato con la composizione di ogni equipaggio.
  - Genera una **mappa HTML interattiva** (`mappa_equipaggi.html` nella cartella `data/output`) che visualizza i percorsi di tutte le auto.

**Comando:**

```bash
python src/main.py ottimizza
```

## Esecuzione dei Test

Il progetto include una suite di test automatizzati per garantire il corretto funzionamento delle singole unità e l'integrazione tra i componenti.

### Setup

Assicurarsi di aver installato le dipendenze di sviluppo con il comando `pip install -e .`.

### Comandi Principali

1. **Eseguire tutti i test (esclusi quelli di integrazione)**:
   Questo è il comando standard da usare per la maggior parte delle verifiche. È veloce perché non esegue test che richiedono chiamate a API esterne.

   ```bash
   python -m pytest tests/ -m "not integration"
   ```

2. **Eseguire solo i test di integrazione**:
   Questi test verificano la corretta comunicazione con le API esterne (Nominatim, OpenRouteService). Richiedono una connessione Internet e una chiave API valida.

   ```bash
   python -m pytest tests/ -m "integration"
   ```

3. **Eseguire tutti i test**:
   Per lanciare l'intera suite, inclusi i test di integrazione.

   ```bash
   python -m pytest tests/
   ```

### Analisi della Code Coverage

È possibile generare un report per verificare quale percentuale del codice è coperta dai test.

**Comando completo con coverage:**

```bash
python -m pytest tests/ -m "not integration" --cov=src --cov-report=term-missing --cov-report=html:data/output/report/htmlcov --cov-branch
```

**Breakdown del comando:**

| Parte                       | Significato                                                     |
| --------------------------- | --------------------------------------------------------------- |
| `python -m pytest`          | Lancia pytest come modulo Python.                               |
| `tests/`                    | Specifica la cartella dove si trovano i test.                   |
| `-m "not integration"`      | Esclude i test marcati come `integration`.                      |
| `--cov=src`                 | Misura la coverage del codice sorgente nella cartella `src/`.   |
| `--cov-report=term-missing` | Mostra in console quali righe di codice non sono state testate. |
| `--cov-report=html:...`     | Genera un report HTML navigabile nella cartella specificata.    |
| `--cov-branch`              | Misura anche la copertura dei branch (es.`if`/`else`).          |
