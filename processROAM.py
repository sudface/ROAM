import pandas as pd
import json

'''
Input ROAM data was prefiltered with the following to remove opal card segregation
* head -n1 ROAM_20250822.txt > ROAM_20250822_all.psv
* grep "All card types" ROAM_20250822.txt >> ROAM_20250822_all.psv
'''

input_roam = 'ROAM_20250822_all.psv'
output_roam = 'ROAM_20250822_useful.psv'
output_json = 'ROAM_20250822.json'

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

linesMap = {
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
    'T3 Bankstown Line & T3 Liverpool & Inner West Line': 'T3'
}


df = pd.read_csv(input_roam, sep='|', usecols=goodCols)

# If a train doesn't have a departure time (terminates) then fill with arrival time
df['ACT_STN_DPRT_TIME'] = df['ACT_STN_DPRT_TIME'].fillna(df['ACT_STN_ARRV_TIME']).fillna(df['PLN_STN_DPRT_TIME'])

# Remap long line names to line numbers
df['TRIP_ZONE'] = df['TRIP_ZONE'].map(linesMap)

goodCols.remove("ACT_STN_ARRV_TIME")
goodCols.remove("PLN_STN_DPRT_TIME")
df[goodCols].to_csv(output_roam, sep='|', index=False)

# Group by run number and build structure
result = []
for trip_name, group in df.groupby("TRIP_NAME"):
    trip_info = {
        "TRIP_NAME": trip_name,
        "LINE": group["TRIP_ZONE"].iloc[0],
        "ORIG_STN": group["ORIG_STN"].iloc[0], # all origStn in the trip should be the same, so get the first
        "DEST_STN": group["DEST_STN"].iloc[0],
        "TIME": group["ACT_STN_DPRT_TIME"].sort_values().iloc[0],
        "CAPACITY": int(group["SEAT_CAPACITY"].iloc[0]),
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

with open(output_json, "w") as f:
    json.dump(result, f)