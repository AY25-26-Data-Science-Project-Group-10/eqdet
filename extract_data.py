import obspy, tqdm, utils, os, random, math, sys
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd 
import numpy as np


# ------ 1. EXTRACT PICKS FROM ALL QUAKEML FILES ------
print("====== 1. EXTRACT PICKS FROM ALL QUAKEML FILES ======")
dict_paths = defaultdict(list)
dict_paths["earthquakes"] = [Path(utils.QKML_EQ_DIR) / fn for fn in os.listdir(utils.QKML_EQ_DIR) if fn.lower().endswith(".qkml")]
dict_paths["explosions"] = [Path(utils.QKML_EX_DIR) / fn for fn in os.listdir(utils.QKML_EX_DIR) if fn.lower().endswith(".qkml")]

catalogs = {}

for event_type, paths in dict_paths.items():
    print(f"\n----------- LOAD {event_type.upper()} -----------")

    if not paths:
        raise FileNotFoundError(f"No files found for {event_type}")
    
    catalog = obspy.Catalog()
    total = len(paths)

    for i, path in enumerate(paths, start=1):
        print(f"[File {i}/{total}] Loading {path.name}", end="", flush=True)
        sub_cat = obspy.read_events(path)
        catalog.extend(sub_cat)
        print(f"\t\t\t {len(sub_cat)} events loaded")
    catalogs[event_type] = catalog

# Dataframe of all earthquake, explosion and probable_explosion picks               
df_picks = utils.extract_picks(catalogs)
df_picks.to_csv(utils.FILENAME_PICKS, index=False) # Export to csv for possible debugging
print(f"\n----------- CATALOG SUMMARY -----------")
print(df_picks.groupby("Event type").agg(
    **{"Number of picks": ("Pick time", "count")},
    **{"First pick time": ("Pick time", "min")},
    **{"Last pick time": ("Pick time", "max")},).reset_index().to_string(index=False))
print(f"Total number of picks: {len(df_picks)}\n")
print(f"Picks saved to {utils.FILENAME_PICKS}\n\n")




# ------ 2. CREATE WINDOWS FOR QUERYING ------
print("====== 2. CREATE WINDOWS FOR QUERYING ======")
# Select picks for specified event types (i.e. earthquakes, explosions)
df_picks = df_picks[df_picks["Event type"].isin(utils.LIST_EVENT_TYPES)]

# Remove channel ID from the SEED string, so that the shortened SEED string can identify stations
df_picks["SEED string short"] = df_picks["SEED string"].str.rsplit(".", n=2).str[0] 

# Report how many P and S picks per event
utils.print_pick_summary(df_picks)

win_size_no_buff = utils.WIN_SIZE - utils.POST_EVENT_BUFFER - utils.PRE_EVENT_BUFFER # Window size without buffers
df_pick_groups = df_picks.groupby(["Event id", "SEED string short"])

# # Generate windows
all_windows = []
print(f"\n----------- GENERATING WINDOWS -----------")
for (event_id, seed_short), group in tqdm.tqdm(df_pick_groups, total=len(df_pick_groups), ncols=120):
    tP = group[group["Pick type"].str.startswith("P")]["Pick time"].min()
    tS = group[group["Pick type"].str.startswith("S")]["Pick time"].min()

    picks = []
    if not math.isnan(tP): picks.append(("P", tP))
    if not math.isnan(tS): picks.append(("S", tS))

    pick_times = [p[1] for p in picks]

    # --- CASE 1: Picks fit into one window ---
    if max(pick_times) - min(pick_times) <= win_size_no_buff:

        span = max(pick_times) - min(pick_times)
        max_offset = win_size_no_buff - span
        offset = np.random.uniform(0, max_offset)

        win_start = min(pick_times) - utils.PRE_EVENT_BUFFER - offset
        win_end = win_start + utils.WIN_SIZE

        for pick_type, pick_t in picks:
            all_windows.append({
                "Event id": event_id,
                "SEED string": group["SEED string"].iloc[0],
                "Pick type": pick_type,
                "Event type": group["Event type"].iloc[0],
                "Pick time": pick_t,
                "SEED string short": seed_short,
                "Win index": 0,
                "Win start": win_start,
                "Win end": win_end,
            })
    # --- CASE 2: Picks too far apart → separate windows ---
    else:
        separation = tS - tP

        max_offset_p = min(separation - utils.POST_EVENT_BUFFER, # when S is closer to win_end
                           win_size_no_buff) # window length constraints
        win_end_p = tP + utils.POST_EVENT_BUFFER + np.random.uniform(0, max_offset_p)
        all_windows.append({
                "Event id": event_id,
                "SEED string": group["SEED string"].iloc[0],
                "Pick type": "P",
                "Event type": group["Event type"].iloc[0],
                "Pick time": tP,
                "SEED string short": seed_short,
                "Win index": 1,
                "Win start": win_end_p - utils.WIN_SIZE,
                "Win end": win_end_p
            })
        
        max_offset_s = min(separation - utils.PRE_EVENT_BUFFER, # when P is closer to win_start
                           win_size_no_buff)    # window length constraints
        win_start_s = tS - utils.PRE_EVENT_BUFFER - np.random.uniform(0, max_offset_s)
        all_windows.append({
                "Event id": event_id,
                "SEED string": group["SEED string"].iloc[0],
                "Pick type": "S",
                "Event type": group["Event type"].iloc[0],
                "Pick time": tS,
                "SEED string short": seed_short,
                "Win index": 2,
                "Win start": win_start_s,
                "Win end": win_start_s + utils.WIN_SIZE
            })
        
df_windows = pd.DataFrame(all_windows)

# Report the number of far pairs i.e. event–station windows where the S arrival falls outside window
print()
utils.print_far_pair_summary(df_windows)

# Tag windows that contain picks from other events.
# We do not query these windows but keep them to accurately identify noise windows
def window_contains_other_event(row):
    others = df_windows[(df_windows["Event id"] != row["Event id"]) & \
                        (df_windows["SEED string short"] == row["SEED string short"])] 
    return ((others["Pick time"] >= row["Win start"]) & (others["Pick time"] <= row["Win end"])).any()

df_windows["Has overlap"] = df_windows.apply(window_contains_other_event, axis=1)

# Report the number of windows that contain picks from other events.
utils.print_overlap_summary(df_windows)
print(f"Number of earthquake windows: {len(df_windows[df_windows['Event type'] == 'earthquakes'].drop_duplicates(['Event id', 'SEED string short', 'Win index']))}")
print(f"Number of explosion windows: {len(df_windows[df_windows['Event type'] == 'explosions'].drop_duplicates(['Event id', 'SEED string short', 'Win index']))}")

# Save windows to CSV for possible debugging
df_windows.to_csv(utils.FILENAME_WINDOWS, index=False)
print(f"Windows saved to {utils.FILENAME_WINDOWS}\n\n")




# ------ 3. DOWNLOAD EVENT WAVEFORMS ------
print("====== 3. DOWNLOAD EVENT WAVEFORMS AND LABELS======")

# Get all windows generated from catalog
df_windows = df_windows[~df_windows["Has overlap"]] # Ignore windows that contain picks from other events
df_windows["Win start"] = df_windows["Win start"].apply(obspy.UTCDateTime)
df_windows["Win end"] = df_windows["Win end"].apply(obspy.UTCDateTime)
df_windows["Pick time"] = df_windows["Pick time"].apply(obspy.UTCDateTime)
df_windows = df_windows.sort_values(["Pick time"]) # Sort pick time from earliest to latest

# Each window is uniquely identified by event id, station id (SEED string short), and window index
df_win_groups = df_windows.groupby(["Event id", "SEED string short", "Win index"])

# Define accumulators
df_y_eq = pd.DataFrame(columns=utils.COLUMNS_Y) # Dataframe to accummulate earthquake labels
df_y_ex = pd.DataFrame(columns=utils.COLUMNS_Y) # Dataframe to accummulate explosion labels
no_resp_seeds = [] # Accumulate SEED strings which returned an empty query on the FDSNWS

map_output = {"earthquakes": (utils.WAVEFORM_EQ_DIR, df_y_eq),
              "explosions": (utils.WAVEFORM_EX_DIR, df_y_ex)}

# Generate labels for each window. Each window has either both P and S times, or only one of them
pbar = tqdm.tqdm(df_win_groups, total=len(df_win_groups), ncols=120)
no_resp_seeds = set() # Stations which had failed waveform downloads
failed_summary_bar = tqdm.tqdm(total=0, bar_format='{desc}', position=1) # Hack for printing no. of seeds with failed requests 
failed_seeds_bar = tqdm.tqdm(total=0, bar_format='{desc}', position=2) # Hack for printing seeds with failed requests 
failed_waveforms_count = 0 # Number of windows/waveforms that failed to download

for (event_id, seed_str_s, win_idx), df_group in pbar:
    
    win_start = df_group["Win start"].iloc[0]
    win_end = df_group["Win end"].iloc[0]
    seed_string = df_group["SEED string"].iloc[0]
    event_type = df_group["Event type"].iloc[0]

    network_code, station_code = seed_str_s.split(".")[:2]

    dir, df_y = map_output[event_type]
    pbar.set_postfix_str(f"Station: {network_code}.{station_code}\t Window start: {win_start}")
    status = utils.download_window(network_code, station_code, 
                                   win_start, win_end, 
                                   dir=dir, print=False)

    #  If the waveform can be downloaded, save the label
    if status:
        # If the event-station has multiple P (S) picks, choose the arrival time of the first P (S) pick
        p_time = df_group.loc[df_group["Pick type"].str.startswith("P"), "Pick time"].min() # np.nan if pick is absent
        s_time = df_group.loc[df_group["Pick type"].str.startswith("S"), "Pick time"].min() # np.nan if pick is absent
        
        seed_string = seed_string.replace("..", ".00.") # Fill in missing fields in SEED string with 00 to match eqcct's prediction output format
        
        file_name = seed_string + " | " + str(win_start) + " - " + str(win_end)
        row_df = pd.DataFrame([[file_name, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 
                                p_time, np.nan, s_time, np.nan]], columns=utils.COLUMNS_Y)
        df_y.loc[len(df_y)] = row_df.iloc[0] # append to the df this way because pd.concat is not helpful here

    # If download failed, record seed string for our inspection
    else:
        failed_waveforms_count += 1
        no_resp_seeds.add(seed_str_s)
        failed_summary_bar.set_description_str(f"  Failed queries ({failed_waveforms_count} waveforms, {len(no_resp_seeds)} unique stations):")
        failed_seeds_bar.set_description_str("  "+", ".join(sorted(no_resp_seeds)))

failed_summary_bar.close()  # Prevent bars from printing again
failed_seeds_bar.close()    # Prevent bars from printing again

print(f"Number of earthquake labels (waveforms): {len(df_y_eq)}")
print(f"Number of explosion labels (waveforms): {len(df_y_ex)}\n")

df_y_eq.to_csv(utils.FILENAME_Y_EQ, index=False)
df_y_ex.to_csv(utils.FILENAME_Y_EX, index=False)
print(f"Earthquake labels saved to {utils.FILENAME_Y_EQ}")
print(f"Explosion labels saved to {utils.FILENAME_Y_EX}\n\n")




# ------ 4. DOWNLOAD NOISE WAVEFORMS ------
print("====== 4. DOWNLOAD NOISE WAVEFORMS AND LABELS ======")
# Get the range of dates to sample the noise waveforms fromm
df_windows["Pick time"] = df_windows["Pick time"].apply(utils.to_utc_or_none)

# Get the time range where we have full knowledge of event (non)-occurrence,
# this is the time range to sample noise windows from
first_picks = df_windows.groupby("Event type")["Pick time"].min()
last_picks  = df_windows.groupby("Event type")["Pick time"].max()
win_sample_start = first_picks.max()   # latest first pick
win_sample_end   = last_picks.min()    # earliest last pick

# Get stations that were active during that event time range
station_list = utils.query_stations(win_sample_start, win_sample_end)

# Accummulate labels for noise windows
df_y_noise = pd.DataFrame(columns=utils.COLUMNS_Y)

# Clear the noise waveform directory
os.system(f'rm -rf ./{utils.WAVEFORM_NOISE_DIR}/*')

# Download the same number of noise windows as positive classes
num_win = len(df_windows.drop_duplicates(["Event id", "SEED string short", "Win index"]))
pbar_noise = tqdm.tqdm(range(num_win), ncols=120)

# Download the noise window and store locally, equal to the number of labels
for i in pbar_noise:
    # If no waveform available, requery until one is available 
    while True:
        cand_station = station_list[random.randrange(0, len(station_list)-1)] # Network.Station format (i.e'HE.SUF')

        # Generate a window which does not overlap with any event window
        win_start, win_end = utils.generate_noise_win(win_sample_start, win_sample_end, cand_station, df_windows)

        network_code, station_code = cand_station.split(".")

        pbar_noise.set_postfix_str(f"Station: {network_code}.{station_code}\t Window start: {win_start}")
        status = utils.download_window(network_code, station_code, 
                                        win_start, win_end, 
                                        dir=utils.WAVEFORM_NOISE_DIR,
                                        print=False)
        
        if status: # If download successful, record the waveform in the noise label file
            file_name = f"{cand_station}.00.00 | {str(win_start)} - {str(win_end)}"
            row_df = pd.DataFrame([[file_name, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 
                            np.nan, np.nan, np.nan, np.nan]], columns=utils.COLUMNS_Y)
            df_y_noise = pd.concat([df_y_noise, row_df])
            break

print(f"Number of noise labels (waveforms): {len(df_y_noise)}\n")

df_y_noise.to_csv(utils.FILENAME_Y_NOISE, index=False)
print(f"Noise labels saved to {utils.FILENAME_Y_NOISE}\n\n")




print("========== DATA EXTRACTION COMPLETE ==========")