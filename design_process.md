# Design Decisions
This document aims to explain the steps taken to build the Finnish dataset in `data/`.

## Overview
The required files for building the Finnish dataset are the manual picks in QuakeML (.qkml) format. This file contains the ground truth P and S pick times of seismic events. 

These were the steps taken obtain the dataset from the QuakeML files
1. Extract pick information from QuakeML files
2. Generate event windows from the picks
3. Download event windows from the Finnish FDSN Web service
3. Download noise windows from the Finnish FDSN Web service


## 1. Extract pick information
Create a dataframe of picks from the QuakeML files and clean the data. 

Only P and S picks were kept; MSG picks were avoided because they were used for magnitude calculations. The suffixes of phases such as ’PG’, ’PB’, ’PN’, ’SG’, ’SB’, and ’SN’ indicated the depth of the crust at which the waves had travelled. These phases were treated simply as P or S picks.

Manual picks were extracted from `earthquakes2025.qkml` and `explosions2025.qkml` while `probable_explosions2025.qkml` was excluded due to the low confidence in the label.

The quakeML files contain picks for:
* Earthquake (`earthquakes2025.qkml`): 01.01.2025 to 31.12.2025
* Explosions (`explosions2025.qkml` ): 01.01.2025 to ___28.02.2025___ (Shorter time range!)

## 2. Generate event windows

The STEAD dataset was used in training and benchmarking EQCCT and EQTransformer, so we (largely) follow its window specifications. 

About events:
* A seismic event can be detected by $\geq$ 1 station
* A station has zero or more P picks , and zero or more S-picks

Window definition:
* The STEAD dataset uses 60s windows.
* Number of picks per window
    * In almost all cases, a window contains one P pick and one S pick, similar to STEAD. 
    * In cases where a window contains one pick, it is either because it is a far pick, or there is only one manual pick identified for that event 
* Picks arrive $\geq$ 5s after window start (defined  as `PRE_EVENT_BUFFER`) and $\geq$ 5s before window end (defined as `POST_EVENT_BUFFER`)  
* Far picks
    * But if P and S arrival times are too far from each other, each pick will be put in its own separate window to be queried.
    * If both picks can be contained in a window while avoiding the buffers, this window has `win_index` of 0  
    * P-wave far-pick window has a `win_index` of 1
    * S-wave far-pick window has a `win_index` of 2
* While STEAD has windows that begin 5-10 seconds before the first pick, we allow picks to arrive 5-55 seconds after the window onset, so that the model does not spuriously anticipate waves to arrive the 5-10 second mark in its detection window.
* Each window contains pick(s) for only one event

A window is identified by its event-station-window index tuple (`Event id`, `SEED string short`, `win_index`)

## 3. Download event windows
Wavforms are downloaded in miniSEED (.mseed) format and were  left unprocessed in case the candidate phase pickers had their specific pre-processing procedures.

Labels are stored in CSV files with the same columns as EQCCT's prediction output CSV file. 

EQCCTPro's `create_dataset.py` utility is used by the function `utils.download_window()` to download the waveforms. However, `create_dataset.py` does not have a callable function, so we invoke it using command line. Note that the `create_dataset.py` file is just copied from eqcct's repository.


## 4. Download noise windows
The QuakeML files span different time ranges, so the event catalog is only complete over the interval where all files overlap. We therefore define the valid noise‑sampling window as the intersection of all event time spans: the maximum of all first‑pick times and the minimum of all last‑pick times. This ensures that noise windows are drawn from a period where the presence or absence of events is fully known.

In addition, stations for noise windows were uniformly sampled from those active within the same time period. Only station-window combinations free of events were retained.