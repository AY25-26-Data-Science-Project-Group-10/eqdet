# Training an ML-algorithm for real-time earthquake detection in Finland

University of Helsinki course: Data Science Project

Developers: Teemu Ruokokoski, Tom Cordruwisch, De Qi Ng, Ceren Sahin, Tuula Salmi


## Description
The **eqdet** repository contains scripts for building the Finnish dataset, as well as our best attempt at replicating the Short-term Average/Long-term Average (STA/LTA) automatic phase-picker used at the Institute of Seismology at the University of Helsinki (ISUH) for use as the baseline for comparison against deep learning-based phase pickers.

## Project Structure
The repository is as organised as follows:
```
data/                               # Dataset
├── waveforms_earthquakes_nonoise/  # Miniseed waveforms of earthquakes 
├── waveforms_explosions_nonoise/   # Miniseed waveforms of explosions
├── waveforms_noise_only/           # Miniseed waveforms of noise (no events)
├── qkml_earthquakes/               # Directory for earthquake QuakeML files
│   └── earthquakes2025.qkml        # QuakeML of earthquakes from 01.01.2025 to 31.12.2025
└── qkml_explosions/                # Directory for explosion QuakeML files
    └── explosions2025.qkml         # QuakeML of explosions from 01.01.2025 to to 28.02.2025
docs/                               # Meeting minutes, bibliography
stalta/                             # Replica of ISUH's STA/LTA algorithm
design_process.md                   # Explanation of design process of dataset constructor
extract_data.py                     # Script to download waveforms
create_dataset.py                   # Utility script from EQCCT for organising and downloading dataset
examples.ipynb                      # Example code on using utility functions
eq_labels.csv                       # Ground truth labels (manual picks) for earthquakes
ex_labels.csv                       # Ground truth labels (manual picks) for explosions
noise_labels.csv                    # Ground truth labels for noise
```

## Set up the Python environment (notebooks + scripts)

Run these commands from the repository root (works on Linux/macOS).

### 1. Create a virtual environment
```bash
python3 -m venv .venv
```

### 2. Activate the virtual environment
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Register the environment as a Jupyter kernel (for notebooks)
```bash
python -m ipykernel install --user --name "eq-venv" --display-name "Python (eqdet)"
```

### 5. Select the kernel in your notebook UI

## Build the dataset 
1. Put .qkml files for earthquake events in `data/qkml_earthquakes`
2. Put .qkml files for explosion events in `data/qkml_explosions` 
3. In terminal, run
    ```
    python extract_data.py
    ``` 
4. Wait for waveform to be downloaded. Profit. Example output
    ```
    ====== 1. EXTRACT PICKS FROM ALL QUAKEML FILES ======

    ----------- LOAD EARTHQUAKES -----------
    [File 1/1] Loading earthquakes2025.qkml                  328 events loaded

    ----------- LOAD EXPLOSIONS -----------
    [File 1/1] Loading explosions2025.qkml                   599 events loaded

    ----------- CATALOG SUMMARY -----------
    Event type  Number of picks             First pick time              Last pick time
    earthquakes             7133 2025-01-01T09:22:01.256470Z 2025-12-30T11:44:31.096080Z
    explosions            14281 2025-01-02T09:17:15.776090Z 2025-02-28T20:10:20.680000Z
    Total number of picks: 21414

    Picks saved to picks.csv


    ====== 2. CREATE WINDOWS FOR QUERYING ======
    ----------- PICK SUMMARY -----------
    (num P picks, num S picks)  Number of event-stations
    0                     (1, 1)                      8712
    1                     (0, 1)                      2896
    2                     (1, 0)                      1056
    3                     (1, 2)                         6
    4                     (0, 2)                         4
    5                     (2, 1)                         4
    Total number of event-stations: 12678


    ----------- GENERATING WINDOWS -----------
    100%|█████████████████████████████████████████████| 12678/12678 [00:11<00:00, 1147.51it/s]

    ----------- FAR PAIR SUMMARY -----------
    Max duration between P and S arrivals: 86.70201s
    The window size of 60s is too short to contain some P, S pairs:
    * Number of event-stations with far pairs: 40
    * Number of picks affected: 80

    ----------- OVERLAP SUMMARY -----------
    Number of windows containing picks from other events: 165

    Number of earthquake windows: 4286
    Number of explosion windows: 8432
    Windows saved to windows.csv


    ====== 3. DOWNLOAD EVENT WAVEFORMS AND LABELS======
    100%|████████████| 29/29 [00:25<00:00,  1.14it/s, Station: HE.VUOS     Window start: 2025-01-02T09:16:58.730100Z]
    Failed queries (8 waveforms, 5 unique stations):
    NO.ARA0, UP.ERTU, UP.KALU, UP.LANU, UP.PAJU
    Number of earthquake labels (waveforms): 10
    Number of explosion labels (waveforms): 11

    Earthquake labels saved to eq_labels.csv
    Explosion labels saved to ex_labels.csv


    ====== 4. DOWNLOAD NOISE WAVEFORMS AND LABELS ======
    100%|████████████| 20/20 [00:26<00:00,  1.34s/it, Station: FN.RANF     Window start: 2025-01-18T10:31:25.907942Z]
    Number of noise labels (waveforms): 20

    Noise labels saved to noise_labels.csv


    ========== DATA EXTRACTION COMPLETE ==========
    ```