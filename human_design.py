"""
human_design.py

Function to create a human design chart from birth data.
"""
import human_design_lib.hd_features as hdf
import human_design_lib.hd_constants as hdconst


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