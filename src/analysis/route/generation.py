import pandas as pd
import requests
import polyline

from src.data.loader import DATA_DIR
from src.config.settings import API_KEY
url = "https://maps.googleapis.com/maps/api/directions/json"

def get_candidate_total_info(trip_no, data):
    rows = []
    for route_no, route in enumerate(data["routes"]):
        for step in route["legs"][0]["steps"]:
            row = {
                "TRIP_NO": trip_no,
                "ROUTE_NO": route_no,
                "DISTANCE": step["distance"]["value"],     # meters
                "DURATION": step["duration"]["value"],     # seconds
                "START_LNG": step["start_location"]["lng"],
                "START_LAT": step["start_location"]["lat"],
                "END_LNG": step["end_location"]["lng"],
                "END_LAT": step["end_location"]["lat"],
                "POLYLINE": step["polyline"]["points"],
                "TRAVEL_MODE": step["travel_mode"],
                "BUS_NAME": None,
                "BUS_TYPE": None
            }
            
            if step["travel_mode"] == "TRANSIT":
                transit = step.get("transit_details", {})
                line = transit.get("line", {})
                row["BUS_NAME"] = line.get("short_name")
                row["BUS_TYPE"] = line.get("name")

            rows.append(row)
    return rows
    
def get_candidate_routes_info(trip_no, data):
    rows = []
    for route_no, route in enumerate(data["routes"]):
        coords = []
        for step in route["legs"][0]["steps"]:
            travel_mode = step["travel_mode"]
            bus_name = None
            bus_type = None

            if travel_mode == "TRANSIT":
                line = step["transit_details"]["line"]
                bus_name = line.get("short_name")
                bus_type = line.get("name")

            decoded_points = polyline.decode(step["polyline"]["points"])
            coords.extend(decoded_points)

        if len(coords) == 0:
            continue
        
        rows.append({
            "TRIP_NO": trip_no,
            "ROUTE_NO": route_no,
            "POINTS": decoded_points  # [(lat, lon), ...]
        })
        
    return rows

def get_bus_candidate_routes(trip_no, origin_lat, origin_lon, dest_lat, dest_lon, departure_time):
    
    params = {
        "origin": f"{origin_lat},{origin_lon}",
        "destination": f"{dest_lat},{dest_lon}",
        "departure_time": f"{departure_time}",
        "mode": "transit",
        "transit_mode": "bus",
        "transit_routing_preference": "fewer_transfers",
        "alternatives": "true",
        "language": "ko",
        "key": API_KEY
    }
    
    res = requests.get(url, params=params)
    data = res.json()
    
    candidate_total_info = get_candidate_total_info(trip_no, data)
    candidate_routes = get_candidate_routes_info(trip_no, data)
    
    return candidate_total_info, candidate_routes
