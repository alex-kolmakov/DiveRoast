import xml.etree.ElementTree as ET

import pandas as pd

from src.parsers.base import DiveLogParser


def time_to_minutes(time_str):
    """Convert a time string (MM:SS or raw minutes) to total seconds as float."""
    if ":" in time_str:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    return float(time_str)


def extract_all_dive_profiles_refined(root):
    """Extract dive profiles for all dives from a Subsurface XML root element.

    Returns a DataFrame with per-sample rows containing dive_number, trip_name,
    dive_site_name, time, depth, temperature, pressure, rbt, ndl, sac_rate, rating.
    """
    dive_data = []

    # Create a map of divesite UUIDs to their names
    divesites = {
        ds.attrib["uuid"]: ds.attrib.get("name", "N/A")
        for ds in root.findall(".//site")
    }
    # Track dive sites outside of trip tags
    trip_map = {}
    for trip in root.findall(".//trip"):
        trip_name = trip.attrib.get("location", "N/A")
        for dive in trip.findall("dive"):
            dive_number = dive.attrib.get("number", "N/A")
            trip_map[dive_number] = trip_name
    # Extract dive profiles
    for dive in root.findall(".//dive"):
        dive_number = dive.attrib.get("number", "N/A")
        trip_name = trip_map.get(dive_number, "N/A")
        dive_site_uuid = dive.attrib.get("divesiteid", "N/A")
        dive_site_name = divesites.get(dive_site_uuid, "N/A")

        sac_rate = dive.attrib.get("sac", "N/A").replace(" l/min", "")
        rating = dive.attrib.get("rating", "N/A")
        for sample in dive.findall(".//sample"):
            time = sample.attrib.get("time", "N/A").replace(" min", "")
            depth = sample.attrib.get("depth", "N/A").replace(" m", "")
            temperature = (
                sample.attrib.get("temp", "N/A").replace(" C", "")
                if "temp" in sample.attrib
                else None
            )
            pressure = (
                sample.attrib.get("pressure", "N/A").replace(" bar", "")
                if "pressure" in sample.attrib
                else None
            )
            rbt = (
                sample.attrib.get("rbt", "N/A").replace(":00 min", "")
                if "rbt" in sample.attrib
                else None
            )
            ndl = (
                sample.attrib.get("ndl", "N/A").replace(":00 min", "")
                if "ndl" in sample.attrib
                else None
            )

            if time != "N/A" and depth != "N/A":
                data_point = {
                    "dive_number": dive_number,
                    "trip_name": trip_name,
                    "dive_site_name": dive_site_name,
                    "time": time_to_minutes(time),
                    "depth": float(depth),
                    "temperature": float(temperature) if temperature else None,
                    "pressure": float(pressure) if pressure else None,
                    "rbt": float(rbt) if rbt else None,
                    "ndl": float(ndl) if ndl else None,
                    "sac_rate": float(sac_rate) if sac_rate != "N/A" else None,
                    "rating": int(rating) if rating else None,
                }
                dive_data.append(data_point)
    return pd.DataFrame(dive_data)


class SubsurfaceParser(DiveLogParser):
    def parse(self, file_path: str) -> pd.DataFrame:
        tree = ET.parse(file_path)
        root = tree.getroot()
        return extract_all_dive_profiles_refined(root)

    def supported_extensions(self) -> list[str]:
        return [".ssrf", ".xml"]
