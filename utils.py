import obspy, os, re, random
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import numpy as np
from obspy.clients.fdsn import Client

# ------------ DIRECTORY NAMES ------------
DATA_DIR = "data"
WAVEFORM_EQ_DIR = "data/waveforms_earthquakes_nonoise"
WAVEFORM_EX_DIR = "data/waveforms_explosions_nonoise"
WAVEFORM_NOISE_DIR = "data/waveforms_noise_only"

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
FILENAME_Y_EQ = "eq_labels.csv" # Earthquake labels
FILENAME_Y_EX = "ex_labels.csv" # Explosions labels
FILENAME_Y_NOISE = "noise_labels.csv" # Noise labels for earthquakes and explosions

# ------------ DATA SOURCE CONFIGS  ------------
ISUH_IP_ADDR = "http://128.214.169.201:8080"


# ------------ DATA EXTRACTION CONFIGS  ------------
WIN_SIZE = 60               # Window size in seconds. Same window size used in EQCCT paper
PRE_EVENT_BUFFER = 5        # Number of seconds from start of window until first pick
POST_EVENT_BUFFER = 5       # Number of seconds from last pick until end of window
LIST_EVENT_TYPES = ["explosions", "earthquakes"] # List of event types to use when generating windows

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


def print_pick_summary(df_picks):
    """
    Reports the number of P and S picks per event-station.

    Parameters
    ----------
    df_picks : pandas.DataFrame
        DataFrame containing phase picks, station, and their event id.

    Returns
    -------
    pandas.DataFrame
        A summary table with two columns:
        - "(num P picks, num S picks)": tuple of P and S pick counts
        - "Number of event-station": number of event-stations exhibiting that P/S pick combination
    """

    num_PS_picks = []
    for (_, _), df_group in df_picks.groupby(["Event id", "SEED string short"]):
        num_P_picks = int(df_group["Pick type"].str.startswith("P").sum())
        num_S_picks = int(df_group["Pick type"].str.startswith("S").sum())
        num_PS_picks.append((num_P_picks, num_S_picks))
    df_summary = pd.Series(num_PS_picks).value_counts().to_frame("Number of event-stations").reset_index()
    df_summary = df_summary.rename(columns={"index": "(num P picks, num S picks)"})
    print("----------- PICK SUMMARY -----------" )
    print(df_summary)
    print(f"Total number of event-stations: {df_summary['Number of event-stations'].sum()}", end="\n\n")


def print_far_pair_summary(df_windows):
    """
    Print a summary of event–station windows where the S arrival falls within the configured 
    post-event buffer or outside the window. (i.e., “far pairs”).

    In these cases, the window is too short to contain both the P and S picks
    for that event–station pair. The function identifies such windows, computes
    the P–S time difference for inspection, and prints a summary including:

    - The maximum P–S duration across all events
    - The number of event–station windows classified as far pairs
    - The number of individual picks belonging to far pairs

    Parameters
    ----------
    df_windows : pandas.DataFrame
        DataFrame containing event–station windows and pick metadata.
        Must include the following columns:
        - "Event id": unique identifier for the seismic event
        - "SEED string short": station identifier (channel removed)
        - "Pick time": Manually-identified S or P pick arrival time
        - "Win index": For the same event-station, an indexing of windows

    Note 
    ----------
    Far pairs should have already been separated into their individual windows. That is,
    "Win start" should be different for each pick in a far pair.
    """

    df_copy = df_windows.copy()

    df_groupby = df_copy.groupby(["Event id", "SEED string short"])
    num_far_pairs = (df_groupby["Win index"].nunique() > 1).sum()
    max_diff = (df_groupby["Pick time"].max() - df_groupby["Pick time"].min()).max()

    print("----------- FAR PAIR SUMMARY -----------" )
    print(f"Max duration between P and S arrivals: {max_diff}s")
    print(f"The window size of {WIN_SIZE}s is too short to contain some P, S pairs:")
    print(f"  * Number of event-stations with far pairs: {num_far_pairs}")
    print(f"  * Number of picks affected: {num_far_pairs*2}", end="\n\n")


def print_overlap_summary(df_windows):
    """
    Print a summary of event–station windows that contain picks
    belonging to other events.

    Parameters
    ----------
    df_windows : pandas.DataFrame
        Must contain:
        - "Has overlap": boolean indicating whether the window contains
          picks from other events
        - "Event id": event identifier
        - "SEED string short": station identifier
    """

    df_overlaps = df_windows[df_windows["Has overlap"]]
    num_windows = len(df_overlaps.value_counts(["Event id", "SEED string short"]))
    print("----------- OVERLAP SUMMARY -----------" )
    print(f"Number of windows containing picks from other events: {num_windows}", end="\n\n") 


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


def load_stream(win_start, win_end, network_code, station_code, dir):
    """
        Extract a waveform stream from the local dataset for an exact time window.

        The requested time window **must exactly match** the start and end time of
        the stored waveform file, with precision up to whole seconds in UTC.
        Partial overlaps or sub-window requests are not supported.
        
        Parameters
        ----------
        win_start : str
            Start time of the waveform window (UTC). Must match the dataset's waveform start time exactly to second precision.
            
        win_end : str
            End time of the waveform window (UTC). Must match the dataset's waveform end time exactly to second precision.

        network_code : str
            Network code, according to SEED string format. 
            
        station_code : str
            Station code, according to SEED string format. 

        dir : str
            Directory storing the waveforms
            
        Returns
        -------
        st : obspy.Stream or None
            The extracted waveform stream if available. Returns ``None`` if no matching waveform exists in the dataset.
    """
    
    dir_name = Path(dir) / f'{win_start}_{win_end}' / station_code
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


def query_stations(starttime, endtime):
    """ Get from ISUH FDSNWS a list of stations that were active between starttime and endtime
        Returned in <network>.<station> format.
    """
    client = Client(ISUH_IP_ADDR)
    inventory = client.get_stations(starttime=starttime, endtime=endtime)
    stations = inventory.get_contents()["stations"]
    stations = [string.split(" ")[0] for string in stations]

    return stations


def download_window(network_code, station_code, win_start, win_end, dir):
    """
    Download waveform data for a specified station and time window using
    `create_dataset.py`.

    This function builds a wildcard stream selector
    (<network>.<station>.*.*), invokes `create_dataset.py` via subprocess,
    and saves the retrieved waveforms to the provided output directory.
    The download status is determined by inspecting the command output for
    HTTP status codes.

    Parameters
    ----------
    network_code : str
        Seismic network code (e.g., "FN", "HE").

    station_code : str
        Station code within the network (e.g. "KLF", "OUL")

    win_start : obspy.UTCDatetime or str
        Start time of the requested window. Must be convertible to string
        for command-line usage.

    win_end : obspy.UTCDatetime or str
        End time of the requested window.

    dir : str or pathlib.Path
        Output directory where downloaded waveform files will be written.

    Returns
    -------
    bool
        True if waveform data was successfully downloaded.
        False if the request completed but returned no matching data
        (HTTP 204 or 404 detected in command output).
    """

    location_code = "*" # Wildcard to select all locations 
    stream_code = "*"   # Wildcard to select all streams

    stream = f"{network_code}.{station_code}.{location_code}.{stream_code}"

    print(f"Querying for {network_code}.{station_code}\t{win_start}\t", end="")

    # create_dataset.py can only be used via command line
    cmd = ["python", "create_dataset.py", 
                    "--start", str(win_start), "--end", str(win_end), 
                    "--streams", stream,
                    "--host", ISUH_IP_ADDR,
                    "--output", dir,
                    "--chunk", "1"] # chunk size (minutes)

    # Check query status of create_dataset.py commands
    ret = subprocess.run(cmd, capture_output=True)
    ret_str = ret.stdout.decode("utf-8")

    # If query yields no waveforms, command output will contain HTTP code 204 or 404
    http_match = re.search(r"HTTP Status code:\s*(\d+)", ret_str)
    if http_match:
        http_code = http_match.group(1)
        print(f"HTTP {http_code}: No matched data, request successful")
        return False # Report failure
    else:
        print("waveform downloaded!")
        return True # Report success


def generate_noise_win(win_sample_start, win_sample_end, station, df_window):
    """
    Randomly sample a WIN_SIZE-length noise window that does not overlap any labeled
    event windows for a given station.

    This function performs rejection sampling: it repeatedly draws a random
    candidate window within the provided sample range until a window is found
    that does not intersect any existing labeled event intervals associated
    with the specified station.

    Parameters
    ----------
    win_sample_start : obspy.UTCDatetime
        Start of the allowable sampling range.

    win_sample_end : obspy.UTCDatetime
        End of the allowable sampling range.

    station : str
        Station identifier. The first two fields of a SEED string (e.g. FN.KLF, HE.ALAJF)

    df_labels : pandas.DataFrame
        DataFrame containing a `file_name` column. Should be read from the labels file. 

    Returns
    -------
    tuple (obspy.UTCDatetime, obspy.UTCDatetime)
        Corresponds to (start of noise window, end of noise window).
    """

    def generate_random_window(win_sample_start, total_seconds):
        offset = np.random.uniform(0, total_seconds-WIN_SIZE) # Uniformly sample from the entire time period
        cand_start = win_sample_start + offset      # Candidate start of window
        cand_end = cand_start + WIN_SIZE      # Candidate end of window
        return cand_start, cand_end

    total_seconds = win_sample_end - win_sample_start

    # Get picks for the specified station  
    df_station = df_window[df_window["SEED string"] == station]

    # If the given station does not have any picks, skip overlap checks and return a random window
    if df_station.empty:
        cand_start, cand_end = generate_random_window(win_sample_start, total_seconds)
        return cand_start, cand_end

    # Convert picks to NumPy arrays for fast broadcasting
    pick_times = df_station["Pick time"].apply(to_utc_or_none).to_numpy()

    while True:
        cand_start, cand_end = generate_random_window(win_sample_start, total_seconds)

        # If candidate window contains any picks, we reject and find a new window
        overlaps = ((cand_start < pick_times) & (pick_times < cand_end)).any()

        if not overlaps:
            return cand_start, cand_end