import pandas as pd
from collections import defaultdict
goodcols = [
    "ROUTE",
    "ROUTE_VARIANT",
    "TRIP_ID",
    "DIRECTION",
    "TRANSIT_STOP_SEQUENCE",
    "SCHD_ARRIVE_TIME",
    "ACTUAL_ARRIVE_TIME",
    "TRANSIT_STOP",
    "TRANSIT_STOP_DESCRIPTION",
    "DEPOT",
    "SUBURB",
    "BUS_CONFIGURATION",
    # "SEATED_CAPACITY",
    # "STANDING_CAPACITY",
    "TOTAL_CAPACITY",
    "OCCUPANCY_RANGE",
    "LATITUDE", 
    "LONGITUDE"
]

types = defaultdict(lambda: str)
for i in ["TRANSIT_STOP_SEQUENCE", "SEATED_CAPACITY", "STANDING_CAPACITY", "TOTAL_CAPACITY"]:
    types[i] = int

print("\t Loading BOAM file...")
df = pd.read_csv("BOAM_20250819.txt", sep='|', usecols=goodcols, dtype=types)

df['ROUTE'] = df['ROUTE'].fillna(df['ROUTE_VARIANT'])
df = df.dropna(subset=['ROUTE'])
df = df.drop(columns="ROUTE_VARIANT")
df['ROUTE'] = df['ROUTE'].str.split("-", n=1).str[0]
# If a bus has unknown depot then it's probably not from Sydney.
# If it has 0-20 patronage anyway then it's not useful. Drop these rows.
df = df[~((df["DEPOT"] == "UNKNOWN") & (df["OCCUPANCY_RANGE"] == "0-20"))]
df['BUS_CONFIGURATION'] = df['BUS_CONFIGURATION'].fillna("Unknown")

print("\t Loading routes.txt GTFS file...")
# Only include public routes
routes_df = pd.read_csv("routes.txt", usecols=["route_short_name", "route_type"])
publicRoutes = set(routes_df.loc[routes_df["route_type"] == 700, "route_short_name"])
publicRoutes -= set(["SW1", "SW2", "SW3"])
df = df[df["ROUTE"].isin(publicRoutes)]

# Generate dict of stops
df_uniqstops = df.drop_duplicates(subset=['TRANSIT_STOP'])

print("\t Processing stops...")
stops = dict(
    zip(
        df_uniqstops['TRANSIT_STOP'],
        zip(
            df_uniqstops['TRANSIT_STOP_DESCRIPTION'].str.split(',', n=1).str[0].str.split(" - ", n=1).str[1],
            df_uniqstops['SUBURB'],
            zip(df_uniqstops['LATITUDE'], df_uniqstops['LONGITUDE'])
        )
    )
)
import json
with open("BOAM_stoplist.json", "w") as f:
        json.dump(stops, f)
        print(f"\t Saved {len(stops)} stops.")

print("\t Processing trip metas...")

# drop rows with same ID and stop seq number (ie. ARR/DEP stops) and keep the not-NaN one
df = df.sort_values(
    ["TRIP_ID", "TRANSIT_STOP_SEQUENCE", "SCHD_ARRIVE_TIME"],
    na_position="last"
).drop_duplicates(subset=["TRIP_ID", "TRANSIT_STOP_SEQUENCE"], keep="first")

# floor and clip occupancy at zero
def floorOccupancy(oRange):
    lower_bound = pd.to_numeric(oRange.str.split("-", n=1, expand=True)[0], errors='coerce').astype(int) - 1
    lower_bound[lower_bound < 0] = 0
    return lower_bound
df["OCCUPANCY_FLOOR"] = floorOccupancy(df["OCCUPANCY_RANGE"])

# other info
trip_time = df.groupby("TRIP_ID")["ACTUAL_ARRIVE_TIME"].min()
peak_load = df.groupby("TRIP_ID")["OCCUPANCY_FLOOR"].max()
trip_summary = df.groupby("TRIP_ID").agg({
    "ROUTE": "first",
    "TOTAL_CAPACITY": "first",
    "DIRECTION": "first",
    "DEPOT": "first",
    "BUS_CONFIGURATION": "first"
})

print("\t Processing trip stops...")
stops_info = (df.groupby("TRIP_ID")
    .apply(lambda g: g[["TRANSIT_STOP_SEQUENCE", "TRANSIT_STOP", "SCHD_ARRIVE_TIME",
"ACTUAL_ARRIVE_TIME", "OCCUPANCY_FLOOR"]].values.tolist()))

# avengers assemble result
result = []
for trip_id in trip_summary.index:
    trip_info = {
        "TRIP_ID": trip_id,
        "ROUTE": trip_summary.at[trip_id, "ROUTE"],
        "TIME": trip_time.at[trip_id],
        "CAPACITY": int(trip_summary.at[trip_id, "TOTAL_CAPACITY"]),
        "DIRECTION": trip_summary.at[trip_id, "DIRECTION"],
        "DEPOT": trip_summary.at[trip_id, "DEPOT"],
        "BUS_TYPE": trip_summary.at[trip_id, "BUS_CONFIGURATION"],
        "PEAK_LOAD": int(peak_load.at[trip_id]),
        "STOPS": stops_info[trip_id]
    }
    result.append(trip_info)

print("\t Saving trips...")
with open("BOAM_20250819.json", "w") as f:
        json.dump(result, f)
        print(f"\t Saved {len(result)} trips.")