"""
hda_core.py

API for Astrology and Human Design information.
"""
import os

from fastapi import FastAPI
from pydantic import BaseModel
import swisseph
import flatlib
from contextlib import asynccontextmanager
import googlemaps

from gene_keys import get_gk
from astrology import get_astro
from human_design import get_hd


class BirthDataModel(BaseModel):
    """
    Model of information received from the chatbot

    Parameters
    ----------
    birthDate : str
        Should be in the format YYYY/MM/DD
    birthTime : str
        Should be in the format HH:MM. Optionally may include seconds as HH:MM:SS.
        Potentially may include UTC offset as format HH:MM+HH:MM,
        HH:MM:SS+HH:MM:SS, HH:MM-HH:MM, HH:MM:SS-HH:MM:SS.
    birthPlace : str
        Should be in the format City, State, Country. State can be omitted. If
        country is omitted, it will be assumed as the United States of America.
    """
    birthDate: str
    birthTime: str
    birthPlace: str


def processBirthTime(birthTime: str):
    """
    Identifies and separates UTC offsets from the birth time string.
    """
    # Determine whether there is a UTC offset
    if "+" in birthTime:
        # Have positive offset
        time, offset = birthTime.split("+")
        offset = "+" + offset
    elif "-" in birthTime:
        # Have negative offset
        time, offset = birthTime.split("-")
        offset = "-" + offset
    else:
        # No offset
        time = birthTime
        offset = "+00:00"  # Use UTC+00 as offset
        
    return time, offset


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles any startup and shutdown processes.
    """
    # Start up processes
    global maps_key
    maps_key = os.environ.get("MAPS_API_KEY")
    yield
    # Shutdown processes


# The API key for Google Maps
maps_key = None

# The application to define behaviors for
app = FastAPI(lifespan=lifespan)


@app.post("/generate-details")
def generate_details(data: BirthDataModel):
    # Connect to extra ephemeris files (for Chiron)
    swisseph.set_ephe_path(os.path.join(flatlib.PATH_RES, "swefiles"))

    # Split UTC offset from birth time, if applicable
    birthTime, timeOffset = processBirthTime(data.birthTime)

    # Geolocate place of birth
    gmaps = googlemaps.Client(key=maps_key)
    geocode_result = gmaps.geocode(data.birthPlace)
    location = (geocode_result[0]["geometry"]["location"]["lat"],
                geocode_result[0]["geometry"]["location"]["lng"])
    # location = (30.5254, -97.666)  # Dummy location for testing
    
    # Get human design info
    hd_info = get_hd(data.birthDate, birthTime, timeOffset, location)
    
    # Get astrology info
    a_info = get_astro(data.birthDate,
                       birthTime,
                       timeOffset,
                       location)
    
    # Get gene key info
    gk_info = get_gk(hd_info["planets"])
    
    return {"human_design": hd_info,
            "gene_keys": gk_info,
            "astrology": a_info}
