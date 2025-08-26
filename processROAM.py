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
    'Stkn Stockton Ferry': 'Stockton Ferry',
    'MFF Manly Fast Ferry': 'MFF',
    'F1 Manly': 'F1',
    'F2 Taronga Zoo': 'F2',
    'F3 Parramatta River': 'F3',
    'F4 Pyrmont Bay': 'F4',
    'F5 Neutral Bay': 'F5',
    'F6 Mosman Bay': 'F6',
    'F7 Double Bay': 'F7',
    'F8 Cockatoo Island': 'F8',
    'F9 Watsons Bay': 'F9',
    'F10 Blackwattle Bay': 'F10',
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
        
        if trip_info["LINE"] == "M1" and trip_info["TRIP_NAME"].endswith(":1000"):
            trip_info["TRIP_NAME"] = trip_info["TRIP_NAME"][9:16]
        elif trip_info["LINE"][0] == "F" and trip_info["LINE"][1].isnumeric():
            run = trip_info["TRIP_NAME"].split("-")
            trip_info["TRIP_NAME"] = run[0] + "-" + run[-1].split(".")[-1]
        
        result.append(trip_info)
    return result


#! ROAM
def ROAM(in_roam, out_roam):
    print(f"Parsing file {in_roam}")
    importedCols = [
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
        'OCCUPANCY_RANGE',
        'REPORTING_LINE'
    ]
    df_roam = pd.read_csv(in_roam, sep='|', usecols=importedCols)

    # remove regional services becaue they aren't opal lol
    BAD_LINES = ["Southern NSW", "North West NSW", "NSW TrainLink North Western Train Services", "NSW TrainLink Southern Train Services", "North Coast NSW", "Western NSW", "Southern NSW", "Southern NSW", "Western NSW", "North Coast NSW", "North West NSW"]
    df_roam = df_roam[~df_roam['REPORTING_LINE'].isin(BAD_LINES)]

    # If a train doesn't have a departure time (terminates) then fill with arrival time
    df_roam['ACT_STN_DPRT_TIME'] = df_roam['ACT_STN_DPRT_TIME'].fillna(df_roam['ACT_STN_ARRV_TIME']).fillna(df_roam['PLN_STN_DPRT_TIME'])
    df_roam['SEAT_CAPACITY'] = df_roam['SEAT_CAPACITY'].fillna(0)

    # Save a PSV with the relevant columns (20MB -> 4MB)
    # clean_df = df_roam
    # cols_keep = [c for c in importedCols if c not in ["ACT_STN_ARRV_TIME", "PLN_STN_DPRT_TIME", "REPORTING_LINE"]]
    # clean_df['TRIP_ZONE'] = clean_df['TRIP_ZONE'].map(LINES_MAP)
    # clean_df[cols_keep].to_csv(out_roam + '.psv', sep='|', index=False)

    roam_parsed = build_trips(df_roam)
    with open(out_roam, "w") as f:
        json.dump(roam_parsed, f)
        print(f"Saved {len(roam_parsed)} trips to {out_roam}")

#! LOAM
def LOAM(in_loam, out_loam, datestring):
    print(f"Parsing file {in_loam} for {datestring} services")
    df_loam = pd.read_csv(in_loam, sep='|')
    df_loam = df_loam[df_loam['SERVICE_DATE'] == datestring]

    # Remap LOAM -> ROAM columns
    loam_remap = {
        "ORIG_STN": "ACT_STOP_STN",
        "DIRECTION": "SEGMENT_DIRECTION",
        "STOP_ID_START_TIME": "TRIP_NAME",
        "ROUTE_ID": "TRIP_ZONE",
        "STOP_SEQ": "NODE_SEQ_ORDER"
    }
    df_loam = df_loam.rename(columns=loam_remap)

    df_loam['ACT_STOP_STN'] = df_loam['ACT_STOP_STN'].map(lambda x: x.replace(" Light Rail", ""))

    # LOAM does not have column for trip start and ends.
    # get ORIG_STN and DEST_STN from first and last stop in each group
    df_loam = df_loam.sort_values(["TRIP_NAME", "NODE_SEQ_ORDER"]).reset_index(drop=True)
    df_loam["ORIG_STN"] = df_loam.groupby("TRIP_NAME")["ACT_STOP_STN"].transform("first")
    df_loam["DEST_STN"] = df_loam.groupby("TRIP_NAME")["ACT_STOP_STN"].transform("last")
    df_loam['SEAT_CAPACITY'] = df_loam['SEAT_CAPACITY'].fillna(0)

    loam_result = build_trips(df_loam)
    with open(out_loam, "w") as f:
        json.dump(loam_result, f)
        print(f"Saved {len(loam_result)} trips to {out_loam}")

#! FOAM
def FOAM(in_foam, out_foam, datestring):
    print(f"Parsing file {in_foam} for {datestring} services")
    df_foam = pd.read_csv(in_foam, sep='|')
    df_foam = df_foam[df_foam['RUN_DATE'] == datestring]

    # Remap FOAM -> ROAM columns
    foam_remap = {
        "RUN_NUMBER": "TRIP_NAME",
        "ROUTE_DESC": "TRIP_ZONE",
        "CAPACITY": "SEAT_CAPACITY",
        "DIRECTION": "SEGMENT_DIRECTION",
        "STOP_SEQ": "NODE_SEQ_ORDER",
        "LOCATION": "ACT_STOP_STN",
        "DEPRT_ACTUAL": "ACT_STN_DPRT_TIME",
    }
    df_foam = df_foam.rename(columns=foam_remap)

    df_foam['ACT_STOP_STN'] = df_foam['ACT_STOP_STN'].map(lambda x: x.split(" Wharf")[0]) # Also catches "Wharf 1" cases

    # largely the same as LOAM
    df_foam = df_foam.sort_values(["TRIP_NAME", "NODE_SEQ_ORDER"]).reset_index(drop=True)
    df_foam["ORIG_STN"] = df_foam.groupby("TRIP_NAME")["ACT_STOP_STN"].transform("first")
    df_foam["DEST_STN"] = df_foam.groupby("TRIP_NAME")["ACT_STOP_STN"].transform("last")
    df_foam['SEAT_CAPACITY'] = df_foam['SEAT_CAPACITY'].fillna(0)

    foam_result = build_trips(df_foam)
    with open(out_foam, "w") as f:
        json.dump(foam_result, f)
        print(f"Saved {len(foam_result)} trips to {out_foam}")


def main():
    import argparse, datetime, os, sys
    assertExists = lambda file: os.path.exists(file) or (print(f"Input file not found: {file}") or sys.exit(1))
    
    parser = argparse.ArgumentParser(description="Process raw LOAM or ROAM files.")

    parser.add_argument('-r', '--roam', action='store_true', help='Process ROAM (Trains)')
    parser.add_argument('-l', '--loam', action='store_true', help='Process LOAM (Light Rail)')
    parser.add_argument('-f', '--foam', action='store_true', help='Process FOAM (Ferry)')
    
    parser.add_argument('date', type=str, help='Date of file in YYYYMMDD format')
    args = parser.parse_args()
    
    if not any([args.roam, args.loam, args.foam]):
        parser.error('You must specify at least one of -r or -l or -f')

    if args.roam:
        in_file = f"ROAM_{args.date}.txt"
        out_file = f"ROAM_{args.date}.json"
        assertExists(in_file)
        ROAM(in_file, out_file)
    if args.loam:
        in_file = f"LOAM_{args.date}.txt"
        out_file = f"LOAM_{args.date}.json"
        date = datetime.datetime.strptime(args.date, "%Y%m%d").strftime("%Y-%m-%d")

        assertExists(os.path.exists(in_file))
        LOAM(in_file, out_file, date)
    if args.foam:
        in_file = f"FOAM_{args.date}.txt"
        out_file = f"FOAM_{args.date}.json"
        date = datetime.datetime.strptime(args.date, "%Y%m%d").strftime("%Y-%m-%d")

        assertExists(os.path.exists(in_file))
        FOAM(in_file, out_file, date)

if __name__ == "__main__":
    main()