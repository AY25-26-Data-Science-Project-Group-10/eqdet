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
└── waveforms_noise_only/           # Miniseed waveforms of noise (no events)
docs/                               # Meeting minutes, bibliography
stalta/                             # Replica of ISUH's STA/LTA algorithm
extract_data.py                     # Script to download waveforms
create_dataset.py                   # Utility script from EQCCT for organising dataset
eq_labels.csv                       # Ground truth labels (manual picks) for earthquakes
ex_labels.csv                       # Ground truth labels (manual picks) for explosions
noise_labels.csv                    # Ground truth labels for noise

```

## Setup the Python environment (notebooks + scripts)

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

## Example use
WIP

TODO: 
* Convert data_extraction.ipynb into a single .py script
* Provide example code