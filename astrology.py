"""
astrology.py

Functions for creating astrology birth information.
"""
import swisseph
import flatlib
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from flatlib.ephem.eph import _signInfo
from flatlib.object import Object

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

