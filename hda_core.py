"""
hda_core.py

API for Astrology and Human Design information.
"""

import os
import json

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
from contextlib import asynccontextmanager
import googlemaps

import human_design.hd_features as hdf
import human_design.hd_constants as hdconst
from gene_keys import GENE_KEYS, GK_LINES


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


def processTimeOffset(timeOffset: str):
    """
    Convert time offset string into a floating point number.

    Parameters
    ----------
    timeOffset: str
        UTC offset. Should be in the format HH:MM. Optionally HH:MM:SS.

    Returns
    -------
        The time offset as a floating point number. E.g. +2:30 would return 2.5.
    """
    parts = [int(t) for t in timeOffset.split(":")]
    if len(parts) == 2:
        # Was in form HH:MM
        time = parts[0] + parts[1] / 60
    elif len(parts) == 3:
        # Was in form HH:MM:SS
        time = parts[1] + parts[2] / 60
        time += parts[0] + time / 60
    return time


def processPlanets(planet_dict):
    """
    Create lists of personality and design of planet positions.
    
    Includes the gate and line data for each planet.
    """
    # Get relevant entries
    planets = planet_dict["planets"]
    gates = planet_dict["gate"]
    lines = planet_dict["line"]

    # Index to start of design planets
    offset = len(planet_dict["planets"]) // 2

    # Create personality planet list
    personality = {}
    for plan, gate, line in zip(planets[:offset], gates[:offset], lines[:offset]):
        personality[plan] = {"gate": gate,
                             "line": line}
    
    design = {}
    for plan, gate, line in zip(planets[offset:], gates[offset:], lines[offset:]):
        design[plan] = {"gate": gate,
                        "line": line}
        
    return {"personality": personality,
            "design": design}


def getPersonality(gate_dict):
    isStrategic = gate_dict["tone"][0] <= 3
    if isStrategic:
        return "Strategic"
    else:
        return "Receptive"
    
def getBrain(gate_dict):
    offset = len(gate_dict["tone"]) // 2
    isActive = gate_dict["tone"][offset] <= 3
    if isActive:
        return "Active"
    else:
        return "Passive"
    
def getEnvStyle(gate_dict):
    offset = len(gate_dict["tone"]) // 2
    isObserved = gate_dict["tone"][offset+3] <= 3
    if isObserved:
        return "Observed"
    else:
        return "Observer"
    
def getViewPerspective(gate_dict):
    isFocused = gate_dict["tone"][0+3] <= 3
    if isFocused:
        return "Focused"
    else:
        return "Peripheral"
    
def getChannels(channel_dict):
    g = channel_dict["gate"]
    chg = channel_dict["ch_gate"]
    channels = []
    for start, end in zip(g, chg):
        channels.append("{0:{fill}{width}}{1:{fill}{width}}".format(start,
                                                                    end,
                                                                    fill=0,
                                                                    width=2))

    return channels


def get_hd(birthDate: str, birthTime, timeOffset, location):
    """
    Create Human Design information.
    
    Parameters
    ----------
    birthDate: str
        Should be in the format YYYY/MM/DD
    birthTime : str
        Should be in the format HH:MM. Optionally HH:MM:SS.
    timeOffset: str
        UTC offset. Should be in the format HH:MM. Optionally HH:MM:SS.
    """
    # Put date and time into usable format
    date = [int(s) for s in birthDate.split("/")]
    time = [int(t) for t in birthTime.split(":")]
    if len(time) == 2:
        # Was in form HH:MM
        time.append(0)  # Add seconds
    offset = processTimeOffset(timeOffset)
    bt = tuple(date + time + [offset])

    # Calculate Human Design information
    design = hdf.calc_single_hd_features(bt, location)
    gate_dict = design[7]

    # Repackage basic information from design
    info = {"type": design[0],
            "authority": design[1],
            "incarnation cross": design[2],
            "profile": design[3],
            "definition": design[4],
            "strategy": design[5],
            "themes": design[6],
            "personality": getPersonality(gate_dict),
            "brain": getBrain(gate_dict),
            "environment style": getEnvStyle(gate_dict),  # This one is having problems
            "view perspective": getViewPerspective(gate_dict),
            "channels": getChannels(design[9]),
            "active chakras": design[8],
            "planets": processPlanets(gate_dict)}  # Get planets and their gates and lines

    return info 


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
    chart = Chart(date, pos, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_EQUAL)
    info = {}
    planets = const.LIST_OBJECTS

    # This will get every planet except for Lilith and Earth
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

    # Calculate Earth separately using the Sun object
    earth_dict = flatlib.ephem.swe.sweObject(const.SUN, date.jd)
    earth_dict.update({
            'id': "Earth",
            'lon': flatlib.angle.norm(earth_dict['lon'] + 180)
        })
    _signInfo(earth_dict)
    earth_obj = Object.fromDict(earth_dict)
    line = {"sign": earth_obj.sign,
            "house": chart.houses.getObjectHouse(earth_obj).id}
    info[earth_obj.id] = line

    # Get angles separately
    angle_names = {"Asc": "Ascending",
                   "Desc": "Descending",
                   "MC": "Midheaven",
                   "IC": "IC"}
    for ang in const.LIST_ANGLES:
        angle = chart.getAngle(ang)
        info[angle_names[ang]] = {"sign": angle.sign}
    
    return info


def get_gk(planet_gates):
    """
    Create gene keys from Human Design.

    Parameters
    ----------
    planet_gates: dict
        The planets with their associated gates and lines.
    """
    prs = planet_gates["personality"]
    dsn = planet_gates["design"]

    # Life's Work - Personality Sun
    lifework = {**GENE_KEYS[prs["Sun"]["gate"]],
                "line": GK_LINES["lifework"][prs["Sun"]["line"]]}
    # Evolution - Personality Earth
    evolution = {**GENE_KEYS[prs["Earth"]["gate"]],
                 "line": GK_LINES["evolution"][prs["Earth"]["line"]]}
    # Pearl - Personality Jupiter
    pearl = {**GENE_KEYS[prs["Jupiter"]["gate"]],
             "line": GK_LINES["pearl"][prs["Jupiter"]["line"]]}
    # Culture - Design Jupiter
    culture = {**GENE_KEYS[dsn["Jupiter"]["gate"]],
               "line": GK_LINES["culture"][dsn["Jupiter"]["line"]]}
    # Vocation - Design Mars
    vocation = {**GENE_KEYS[dsn["Mars"]["gate"]],
                "line": GK_LINES["vocation"][dsn["Mars"]["line"]]}
    # SQ - Design Venus
    sq = {**GENE_KEYS[dsn["Venus"]["gate"]],
          "line": GK_LINES["sq"][dsn["Venus"]["line"]]}
    # Radiance - Design Sun
    radiance = {**GENE_KEYS[dsn["Sun"]["gate"]],
                "line": GK_LINES["radiance"][dsn["Sun"]["line"]]}
    # Purpose - Design Earth
    purpose = {**GENE_KEYS[dsn["Earth"]["gate"]],
               "line": GK_LINES["purpose"][dsn["Earth"]["line"]]}
    # Attraction - Design Moon
    attraction = {**GENE_KEYS[dsn["Moon"]["gate"]],
                  "line": GK_LINES["attraction"][dsn["Moon"]["line"]]}
    # IQ - Personality Venus
    iq = {**GENE_KEYS[prs["Venus"]["gate"]],
          "line": GK_LINES["iq"][prs["Venus"]["line"]]}
    # EQ - Personality Mars
    eq = {**GENE_KEYS[prs["Mars"]["gate"]],
          "line": GK_LINES["eq"][prs["Mars"]["line"]]}
    # Relating - Personality Mercury
    relating = GENE_KEYS[prs["Mercury"]["gate"]]
    #relating["line"] = GK_LINES[prs["Sun"]["line"]]
    # Stability - Personality Saturn
    stability = GENE_KEYS[prs["Saturn"]["gate"]]
    #stability["line"] = GK_LINES[prs["Sun"]["line"]]
    # Creativity - Design Uranus
    creativity = GENE_KEYS[dsn["Uranus"]["gate"]]
    #creativity["line"] = GK_LINES[prs["Sun"]["line"]]

    return {"Life's Work": lifework,
            "Evolution": evolution,
            "Pearl": pearl,
            "Culture": culture,
            "Vocation": vocation,
            "SQ": sq,
            "Radiance": radiance,
            "Purpose": purpose,
            "Attraction": attraction,
            "IQ": iq,
            "EQ": eq,
            "Relating": relating,
            "Stability": stability,
            "Creativity": creativity}


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
    
    return {"message": msg,
            "human_design": hd_info,
            "gene_keys": gk_info,
            "astrology": a_info}
