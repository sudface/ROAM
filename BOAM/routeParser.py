import pandas as pd
import json

# Save all route names
routes_df = pd.read_csv("routes.txt", usecols=["route_short_name", "route_type", "route_long_name"])
publicRoutes = routes_df[routes_df["route_type"] == 700]
route_dict = publicRoutes.set_index("route_short_name")["route_long_name"].to_dict()

with open("busroutes.json", "w") as f:
    json.dump(route_dict, f)