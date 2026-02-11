import obspy, io
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import numpy as np

PICK_COLUMNS = ["Event id", "SEED string", "Pick type", "Event type", "Pick time"]


def extract_picks(catalogs):
    """Extract picks from catalogs of all event types (earthquakes, explosions, probable_explosions) into a dataframe. Ignores non P and S picks.

        Parameters
        ----------
        catalogs : dict
            Dict of obspy Catalogs of all event types
            
        Returns
        -------
        DataFrame
            A DataFrame of picks from all events types
    """
    
    # Dataframe of all earthquake, explosion and probable_explosion picks
    df_picks = pd.DataFrame(columns=PICK_COLUMNS)
    
    for catalog_name, catalog in catalogs.items():
        for event in catalog:
            for pick in event.picks:
                if pick.phase_hint and pick.phase_hint.startswith(("P", "S")):  # Only store S and P picks, avoid MSG picks
                    event_id = event.resource_id.id                             # To uniquely identify a seismic event. An event can have multiple picks from multiple stations
                    seed_string = pick.waveform_id.get_seed_string()            # SEED waveform string in the form network.station.location.channel, e.g. BW.FUR..EHZ
                    # pick_type = pick.phase_hint[0]                              # Get first char (P or S)
                    pick_type = pick.phase_hint                                 # Get full phase type (P* or S*)

                    event_type = catalog_name                                   # Earthquakes, explosions, or probable_explosions
                    pick_time = pick.time                                       # Time of S or P pick, in UTC datetime format
                    row_df = pd.DataFrame([[event_id, seed_string, pick_type, event_type, pick_time]], columns=PICK_COLUMNS)
                    df_picks = pd.concat([df_picks, row_df], ignore_index=True)
                    
    return df_picks