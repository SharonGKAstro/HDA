from fastapi import FastAPI
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from flatlib.ephem.eph import _signInfo
from flatlib.object import Object
import swisseph
import flatlib
import os
from contextlib import asynccontextmanager
import googlemaps
import json


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


def get_astro(birthDate, birthTime, timeOffset, location):
    """
    Create the astrology information from the chart.

    Parameters
    ----------
    birthDate: str
        Should be in the format YYYY/MM/DD
    birthTime : str
        Should be in the format HH:MM. Optionally HH:MM:SS.
    timeOffset: str
        UTC offset. Should be in the format HH:MM. Optionally HH:MM:SS.
    location: tuple(str, str) or tuple(float, float)
        Should be in the format (latitude, longitude). Latitude and longitude
        can be either in string form ("32n30") or in numerical form (32.5452).
        Negative numbers in the numerical form correspond to south and west.
    """
    date = Datetime(birthDate, birthTime, timeOffset)
    pos = GeoPos(*location)
    chart = Chart(date, pos, IDs=const.LIST_OBJECTS)
    info = {}
    planets = const.LIST_OBJECTS

    # This will get every planet except for Lilith
    for planet in planets:
        pl = chart.getObject(planet)
        line = {"sign": pl.sign,
                "house": chart.houses.getObjectHouse(pl).id}
        info[pl.id] = line

    # Calculate Lilith separately using the Swiss Ephemera directly
    sweph, _ = swisseph.calc_ut(date.jd, 12)  # 12 is the code for Mean Lunar Apogee
    lilith_dict = {"id": "Lilith",
                   "lon": sweph[0],
                   "lat": sweph[1],
                   "lonspeed": sweph[3],
                   "latspeed": sweph[4]}
    _signInfo(lilith_dict)  # Adds the sign and sign longitude
    lilith_obj = Object.fromDict(lilith_dict)
    line = {"sign": lilith_obj.sign,
            "house": chart.houses.getObjectHouse(lilith_obj).id}
    info[lilith_obj.id] = line

    # Get Midheaven separately
    mc = chart.getAngle(const.MC)
    info["Midheaven"] = {"sign": mc.sign}
    
    return info


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

    # Message to be displayed prior to information
    msg = "<Message here>"

    # Split UTC offset from birth time, if applicable
    birthTime, timeOffset = processBirthTime(data.birthTime)

    # Geolocate place of birth
    gmaps = googlemaps.Client(key=maps_key)
    geocode_result = gmaps.geocode(data.birthPlace)
    location = (geocode_result[0]["geometry"]["location"]["lat"],
                geocode_result[0]["geometry"]["location"]["lng"])
    
    # Get human design info
    hd_info = {"type": "<Type here>",
               "authority": "<Authority here>",
               "profile": "<Profile here>"}
    
    # Get astrology info
    a_info = get_astro(data.birthDate,
                       birthTime,
                       timeOffset,
                       location)
    
    # Get gene key info
    gk_info = {"life_work": "<Life work here>",
               "evolution": "<Evolution here>"}
    
    return {"message": msg,
            "human_design": hd_info,
            "gene_keys": gk_info,
            "astrology": a_info}
