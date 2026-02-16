import obspy, os, re
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import numpy as np

# ------------ DIRECTORY NAMES ------------
DATA_DIR = "data"
WAVEFORM_DIR = "data/waveforms_earthquakes_nonoise"
PRED_DIR = "predictions"
VIS_DIR = "visualizations"

# ------------ CSV FILE CONFIGS ------------
# Pick file - Each row is a pick for an earthquake, explosion, or probable explosion 
COLUMNS_PICKS = ["Event id", "SEED string", "Pick type", "Event type", "Pick time"]
FILENAME_PICKS = "picks.csv"

# Windows file - Each row is an earthquake pick with columns window start and window end time 
FILENAME_WINDOWS = "windows.csv"

# Labels file - Each row has the P and S arrival time for a waveform
# The columns names are copied from EQCCTOne's prediction output csv file
COLUMNS_Y = ["file_name", "network", "station", "instrument_type", "station_lat", "station_lon", "station_elv","p_arrival_time", "p_probability", "s_arrival_time", "s_probability"]
FILENAME_Y = "labels.csv"


# ------------ DATA SOURCE CONFIGS  ------------
ISUH_IP_ADDR = "http://128.214.169.201:8080"



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
    df_picks = pd.DataFrame(columns=COLUMNS_PICKS)
    
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
                    row_df = pd.DataFrame([[event_id, seed_string, pick_type, event_type, pick_time]], columns=COLUMNS_PICKS)
                    df_picks = pd.concat([df_picks, row_df], ignore_index=True)
                    
    return df_picks



def plot_traces(
		st, 
		ptime=None, stime=None, 
		title="S/P picks", 
		figname=None, showf=True, figsize=(10, 10), **kwargs
	):
    """Plot all traces in a stream, with P and S arrival times, side-by-side from top to bottom

        Parameters
        ----------
        st : obspy.Stream
            Stream object containing one or more seismic traces to plot.

        ptime : datetime-like or float, optional
            P-wave pick time. If provided, a vertical marker will be drawn at
            this time on all traces.

        stime : datetime-like or float, optional
            S-wave pick time. If provided, a vertical marker will be drawn at
            this time on all traces.

        title : str, default "S/P picks"
            Title of the figure.

        figname : str, optional
            Output filename for saving the figure. If None, the figure is not saved.

        showf : bool, default True
            Whether to display the figure using matplotlib.

        figsize : tuple of float, default (10, 10)
            Size of the matplotlib figure in inches as (width, height).

        **kwargs
            Additional keyword arguments passed to the underlying plotting
            routines (e.g., colors, linewidths, etc.).
    """
	
    ntr=len(st)
    ptimes = [ptime]*len(st)
    stimes = [stime]*len(st)

    fig = plt.figure(figsize=figsize)

    for ii in range(ntr):
        ax = plt.subplot(ntr,1,ii+1)
        nt=len(st[ii].data)
        twin=(nt-1)*1.0/st[ii].stats.sampling_rate
        staname=st[ii].stats.network+'.'+st[ii].stats.station
        t=np.linspace(0,twin,nt)
        plt.plot(t,st[ii].data,color='k',label = st[ii].id, linewidth = 1, markersize=1)
        
        if ii==0:
            plt.title(title,fontsize='large', fontweight='normal')
        
        if ii==ntr-1:
            plt.setp(ax.get_xticklabels(), visible=True)
            ax.set_xlabel("Time (s)",fontsize='large', fontweight='normal')
        else:
            plt.setp(ax.get_xticklabels(), visible=False)
            
        ax.set_xlim(xmin=0)
        ax.set_xlim(xmax=t[-1])
        ymin, ymax = ax.get_ylim()
        
        if ptime is not None:
            tp=ptimes[ii]-st[ii].stats.starttime
            plt.vlines(tp, ymin, ymax, color = 'r', linewidth = 1, label="P pick") #for P
            
        if stime is not None:
            ts=stimes[ii]-st[ii].stats.starttime
            plt.vlines(ts, ymin, ymax, color = 'g', linewidth = 1, label="S pick") #for P
        
        plt.gca().legend(loc='lower right', fontsize = 15/(ntr/4))
        
    if figname is not None:
        plt.savefig(figname,**kwargs)

    if showf:
        plt.show()
    else:
        plt.close()


def load_stream(
    win_start: obspy.UTCDateTime,
    win_end: obspy.UTCDateTime,
    network_code: str,
    station_code: str):
    """
        Extract a waveform stream from the local dataset for an exact time window.

        The requested time window **must exactly match** the start and end time of
        the stored waveform file, with precision up to whole seconds in UTC.
        Partial overlaps or sub-window requests are not supported.
        
        Parameters
        ----------
        win_start : obspy.UTCDateTime
            Start time of the waveform window (UTC). Must match the dataset's waveform start time exactly to second precision.
            
        win_end : obspy.UTCDateTime
            End time of the waveform window (UTC). Must match the dataset's waveform end time exactly to second precision.

        network_code : str
            Network code, according to SEED string format. 
            
        station_code : str
            Station code, according to SEED string format. 
            
        Returns
        -------
        st : obspy.Stream or None
            The extracted waveform stream if available. Returns ``None`` if no matching waveform exists in the dataset.
    """
    
    dir_name = Path(WAVEFORM_DIR) / f'{win_start}_{win_end}' / station_code
    st = None
    
    if os.path.isdir(dir_name):
        st = obspy.Stream()
        for filename in os.listdir(dir_name):
            st += obspy.read(dir_name / filename)

    else:
        print(f"No waveform data for {network_code}.{station_code}.. {win_start}")
        
    return st


def parse_label_filename(file_name:str):
    """Parse the `file_name` field of dataset labels.

    The expected filename format is:
        "{SEED_STRING} | {WIN_START} - {WIN_END}"

    Parameters
    ----------
    file_name : str
        Label filename string containing SEED identifier and time window.

    Returns
    -------
    network_code : str
        Network identifier extracted from the SEED string. (e.g HE, FN)
    station_code : str
        Station identifier extracted from the SEED string. (e.g. OUL, KLF)
    win_start : str
        Window start time formatted as "%Y%m%dT%H%M%SZ".
    win_end : str
        Window end time formatted as "%Y%m%dT%H%M%SZ".
    """
    
    match = re.split(r" [|-] ", file_name)
    seed_string = match[0]
    win_start = obspy.UTCDateTime(match[1]).strftime("%Y%m%dT%H%M%SZ")
    win_end = obspy.UTCDateTime(match[2]).strftime("%Y%m%dT%H%M%SZ")

    network_code, station_code, *_ = seed_string.split(".")
    
    return network_code, station_code, win_start, win_end


def to_utc_or_none(utc_str):
    """Convert to UTC datetime format if valid.
    """
    return obspy.UTCDateTime(utc_str) if not pd.isnull(utc_str) else None