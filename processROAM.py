import pandas as pd
import json

'''
Input ROAM data was prefiltered with the following to remove opal card segregation
* head -n1 ROAM_20250822.txt > ROAM_20250822_all.psv
* grep "All card types" ROAM_20250822.txt >> ROAM_20250822_all.psv
'''

LINES_MAP = {
    'T7 Olympic Park Line': 'T7',
    'T8 Airport & South Line': 'T8',
    'T4 Eastern Suburbs & Illawarra Line': 'T4',
    'Hunter Line': 'HUN',
    'T2 Inner West & Leppington Line & T2 Leppington & Inner West Line': 'T2',
    'Metro North West & Bankstown Line': 'M1',
    'Southern Highlands Line': 'SHL',
    'Blue Mountains Line': 'BMT',
    'T9 Northern Line': 'T9',
    'South Coast Line': 'SCO',
    'Central Coast & Newcastle Line': 'CCN',
    'T1 North Shore Line': 'T1 North Shore',
    'T5 Cumberland Line': 'T5',
    'T1 Western Line': 'T1 Western',
    'T6 Lidcombe & Bankstown Line': 'T6',
    'T3 Bankstown Line & T3 Liverpool & Inner West Line': 'T3',
    'IWLR-191': 'L1',
    '1001_L2': 'L2',
    '1001_L3': 'L3',
    '1001_LX': 'LX',
    'ISD-17-6720_L4': 'L4',
    'NT_NLR': 'NLR',
}

mapLines = lambda x: LINES_MAP.get(x, x)

# Group by run number and build structure
def build_trips(df):
    result = []
    for trip_name, group in df.groupby("TRIP_NAME"):
        trip_info = {
            "TRIP_NAME": trip_name,
            "LINE": mapLines(group["TRIP_ZONE"].iloc[0]), # Remap long line names to line numbers
            "ORIG_STN": group["ORIG_STN"].iloc[0], # all origStn in the trip should be the same, so get the first
            "DEST_STN": group["DEST_STN"].iloc[0],
            "TIME": group["ACT_STN_DPRT_TIME"].sort_values().iloc[0],
            "SEAT_CAPACITY": int(group["SEAT_CAPACITY"].iloc[0]),
            "SEGMENT_DIRECTION": group["SEGMENT_DIRECTION"].iloc[0],

            "STOPS": group.sort_values("NODE_SEQ_ORDER")[
                ["NODE_SEQ_ORDER", "ACT_STOP_STN", "ACT_STN_DPRT_TIME", "OCCUPANCY_RANGE"]
            ].values.tolist()
        }
        
        # floor the occupancy range
        for stop in trip_info["STOPS"]:
            stop[3] = int(stop[3].split("-")[0])   
            if stop[3]:
                stop[3] -= 1
        
        result.append(trip_info)
    return result


#! ROAM
IN_ROAM_FILE = 'ROAM_20250822_all.psv'
OUT_ROAM_PSV = 'ROAM_20250822_useful.psv'
OUT_ROAM_JSON = 'ROAM_20250822.json'

def ROAM(in_roam, out_roam):
    print("roaming")
    goodCols = [
        'ACT_STOP_STN',
        'ACT_STN_ARRV_TIME',
        'ACT_STN_DPRT_TIME',
        'PLN_STN_DPRT_TIME',
        'SEGMENT_DIRECTION',
        'TRIP_NAME',
        'TRIP_ZONE',
        'ORIG_STN',
        'DEST_STN',
        'NODE_SEQ_ORDER',
        'SEAT_CAPACITY',
        'OCCUPANCY_RANGE'
    ]

    df_roam = pd.read_csv(in_roam, sep='|', usecols=goodCols)

    # If a train doesn't have a departure time (terminates) then fill with arrival time
    df_roam['ACT_STN_DPRT_TIME'] = df_roam['ACT_STN_DPRT_TIME'].fillna(df_roam['ACT_STN_ARRV_TIME']).fillna(df_roam['PLN_STN_DPRT_TIME'])

    # Save a PSV with the relevant columns (20MB -> 4MB)
    # df_roam['TRIP_ZONE'] = df_roam['TRIP_ZONE'].map(linesMap)
    # cols_keep = [c for c in goodCols if c not in ["ACT_STN_ARRV_TIME", "PLN_STN_DPRT_TIME"]]
    # df_roam[cols_keep].to_csv(OUT_ROAM_PSV, sep='|', index=False)

    roam_parsed = build_trips(df_roam)
    with open(out_roam, "w") as f:
        json.dump(roam_parsed, f)

ROAM(IN_ROAM_FILE, OUT_ROAM_JSON)

#! LOAM

IN_LOAM_FILE = 'LOAM_20250823.txt'
OUT_LOAM_JSON = 'LOAM_20250823.json'

def LOAM(in_loam, out_loam):
    print("loaming")
    df_loam = pd.read_csv(IN_LOAM_FILE, sep='|')

    # Remap LOAM -> ROAM columns
    loam_remap = {
        "ORIG_STN": "ACT_STOP_STN",
        "DIRECTION": "SEGMENT_DIRECTION",
        "STOP_ID_START_TIME": "TRIP_NAME",
        "ROUTE_ID": "TRIP_ZONE",
        "STOP_SEQ": "NODE_SEQ_ORDER"
    }
    df_loam = df_loam.rename(columns=loam_remap)

    # LOAM does not have column for trip start and ends.
    # get ORIG_STN and DEST_STN from first and last stop in each group
    df_loam = df_loam.sort_values(["TRIP_NAME", "NODE_SEQ_ORDER"]).reset_index(drop=True)
    df_loam["ORIG_STN"] = df_loam.groupby("TRIP_NAME")["ACT_STOP_STN"].transform("first")
    df_loam["DEST_STN"] = df_loam.groupby("TRIP_NAME")["ACT_STOP_STN"].transform("last")

    loam_result = build_trips(df_loam)
    with open(OUT_LOAM_JSON, "w") as f:
        json.dump(loam_result, f)

LOAM(IN_LOAM_FILE, OUT_LOAM_JSON)