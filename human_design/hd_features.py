"""
hd_features.py

Functions and definitions for calculating human design features from birth date.

Modified from original by MicFell at https://github.com/MicFell/human_design_engine/
from August 2025.
"""

import sys
import itertools

import swisseph as swe
import numpy as np

from human_design import hd_constants


class hd_features:
    ''' 
    Class for calculation of basic human design features based on 
    given time (year, month, day, hour, minute, second, timezone offset)
    
    basic hd_features:
                    date_to_gate_dict [planets,longitude,gate,line,color,tone,base]
                    profile,
                    inner authority,
                    typ(G=Generator,MG=Manifesting,Generator,P=Projector,
                        M=Manifestor,R=Reflector)
                    incranation cross,
                    active chakras,
                    active channels,
                    split
    extended hd_features:
                    composition charts
                    penta analysis
   
    shortcuts used:
        Head Chakra = HD
        Anja Chakra = AA
        Throat Chakra = TT
        G-Centre = GC
        Hearth Chakra = HT
        Spleen Chakra = SN
        Solar Plexus Chakra = SP
        Sakral Chakra = SL
        Root Chakra = RT     
    '''    
    def __init__(self,year,month,day,hour,minute,second,tz_offset):
    
        '''
        Initialization of timestamp attributes for basic calculation 
        hd_constants.py 
        '''
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz_offset = tz_offset
        self.time_stamp = year,month,day,hour,minute,second,tz_offset
        
        '''
        Constant values are stored in hd_constants.py
            SWE_PLANET_DICT:
                calculation is based on swiss epheremis lib #https://github.com/astrorigin/pyswisseph
                    each planet is represented by a number
            IGING_CIRCLE
                order of gates in rave chart
            CHAKRA_LIST 
                list of all chakras, appreveation see above
        '''
        self.SWE_PLANET_DICT = hd_constants.SWE_PLANET_DICT 
        self.IGING_CIRCLE_LIST = hd_constants.IGING_CIRCLE_LIST 
        self.CHAKRA_LIST = hd_constants.CHAKRA_LIST
 
    def timestamp_to_juldate(self):
        ''' 
        Calculate Julian date from given time:
            -uses swiss_ephemeris lib  www.astro.com #astrodienst
            -if historic daylight time saving data is unknown may see below:
                https://www.ietf.org/timezones/tzdb-2018f/tz-link.html
        
        Return: 
            Julian date(float)
        '''
        time_zone = swe.utc_time_zone(*self.time_stamp)
        jdut = swe.utc_to_jd(*time_zone, 1)  # 1 is the Gregorian calendar flag

        return jdut[1]
    
    def calc_create_date(self,jdut):
        ''' 
        Calculate creation date from birth data:
            #->sun position -88° long, aprox. 3 months before (#source -> Ra Uru BlackBook)
        For calculation swiss_ephemeris lib is used 
        Args: 
            julian date(float): timestamp in julian day format
        Return: 
            creation date (float): timestamp in julian day format
        '''
        design_pos = 88 
        sun_long = swe.calc_ut(jdut, swe.SUN)[0][0]
        long = swe.degnorm(sun_long - design_pos)
        tstart = jdut - 100 #aproximation is start - 100°
        res = swe.solcross_ut(long, tstart)
        #print(res)
        create_date = swe.revjul(res)
        #print(create_date)
        create_julday = swe.julday(*create_date)
        #print(create_julday)
        
        return create_julday
    
    def date_to_gate(self,jdut,label):
        '''
        from planetary position (longitude) basic hd_features are calculated:
            features: 
                planets,longitude,gates lines, colors, tone base
        
        uses swiss_ephemeris lib www.astro.com #astrodienst for calculation
        Args:
            julian day(float): timestamp in julian day format
            label(str): indexing for create and birth values
        Return:
            value_dict (dict)
        '''   
        
        """synchronize zodiac and gate-circle (IGING circle) = 58°""" 
        offset= hd_constants.IGING_offset

        result_dict = {k: [] 
                       for k in ["label",
                                 "planets",
                                 "lon",
                                 "gate",
                                 "line",
                                 "color",
                                 "tone",
                                 "base"]
                      }

        for idx,(planet,planet_code) in enumerate(self.SWE_PLANET_DICT.items()):
            xx = swe.calc_ut(jdut,planet_code)
            long = xx[0][0]
            
            #sun position is base of earth position
            if planet =="Earth": 
                long = (long+180) % 360 #Earth is in opp. pos., angles max 360°

            #north node is base for south node position
            elif planet == "South_Node":
                long = (long+180) % 360 #North Node is in opp. pos.,angles max 360°
                
            angle = (long + offset) % 360 #angles max 360°
            angle_percentage = angle/360
            
            #convert angle to gate,line,color,tone,base
            gate = self.IGING_CIRCLE_LIST[int(angle_percentage*64)] 
            line = int((angle_percentage*64*6)%6+1)
            color =int((angle_percentage*64*6*6)%6+1)
            tone =int((angle_percentage*64*6*6*6)%6+1)
            base =int((angle_percentage*64*6*6*6*5)%5+1)

            result_dict["label"].append(label)
            result_dict["planets"].append(planet)
            result_dict["lon"].append(long)
            result_dict["gate"].append(gate)
            result_dict["line"].append(line)
            result_dict["color"].append(color)
            result_dict["tone"].append(tone)
            result_dict["base"].append(base)
            
        return result_dict

    def birth_creat_date_to_gate(self):
        '''
        concatenate birth- and create date_to_gate_dict 
           Args:
                time_stamp(tuple): format(year,month,day,hour,minute,second,timezone_offset)
           Return: 
                date_to_gate_dict(dict): keys->[planets,label,longitude,gate,line,color,tone,base]
        '''
        birth_julday = self.timestamp_to_juldate()
        create_julday = self.calc_create_date(birth_julday)
        birth_planets = self.date_to_gate(birth_julday,"prs")
        create_planets = self.date_to_gate(create_julday,"des")
        date_to_gate_dict = {
            key: birth_planets[key] + create_planets[key] 
            for key in birth_planets.keys()
                            }
        self.date_to_gate_dict = date_to_gate_dict
        self.create_date = swe.jdut1_to_utc(create_julday)[:-1]
        
        return date_to_gate_dict
    
    def day_chart(self):
        '''calculate day chart
           Args:
                time_stamp(tuple): format(year,month,day,hour,minute,second,timezone_offset)
           Return: 
                date_to_gate_dict(dict): keys->[planets,label,longitude,gate,line,color,tone,base] of daychart
        '''
        birth_julday = self.timestamp_to_juldate()
        birth_planets = self.date_to_gate(birth_julday,"prs")
        result_dict = birth_planets

        return result_dict
    
    
#############################################################################
"""calculation functions based on hd_features based-class starts from here"""

def get_inc_cross(date_to_gate_dict):
    ''' 
    get incarnation cross from open gates 
        Args:
            date_to_gate_dict(dict):output of hd_feature class 
                                    keys->[planets,label,longitude,gate,line,color,tone,base]
        Return:
            incarnation cross(tuple): gates of sun and earth from birth and create date 
                                      format e.g. ((1,2),(3,4))
    '''
    df = date_to_gate_dict
    idx = int(len(df["planets"])/2) #start idx of design values 
    inc_cross = (
        (df["gate"][0],df["gate"][1]),#sun&earth gate at birth
        (df["gate"][idx],df["gate"][idx+1])#sun&earth gate at design
                )          
    profile = df["line"][0],df["line"][idx]
    cr_typ = hd_constants.IC_CROSS_TYP[profile]
    inc_cross = cr_typ + " - " + str(inc_cross)
    return inc_cross

def get_profile(date_to_gate_dict):
    ''' 
    profile is calculated from sun line of birth and design date
    Args:
        date_to_gate_dict(dict):output of hd_feature class 
                                    keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        profile(tuple): format e.g. (1,4)
    '''
    df = date_to_gate_dict
    idx = int(len(df["line"])/2) #start idx of design values
    profile = (df["line"][0],df["line"][idx]) #sun gate at birth and design
    #sort lines to known format
    if profile not in hd_constants.PROFILE_TYP.keys():
        profile = profile[::-1]
    
    return str(profile) + " - " + hd_constants.PROFILE_TYP[profile]

def get_variables(date_to_gate_dict):
    '''
    variables are calculated based on tones of sun(birth,design) and 
    Nodes(birth,design), respectively
    If tone 1,2,3-> left arrow, else right arrow
    Args:
        date_to_gate_dict(dict):output of hd_feature class 
                                    keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        variables(dict): keys-> ["right_up","right_down","left_up","left_down"]
    '''
    df = date_to_gate_dict
    idx = int(len(df["tone"])/2) #start idx of design values 
    tones = (
            (df["tone"][0]),#sun at birth
            (df["tone"][3]),#Node at birth
            (df["tone"][idx]),#sun at design
            (df["tone"][idx+3]),#node at design
                ) 
    keys = ["right_up","right_down","left_up","left_down"] #arrows,variables
    variables = {keys[idx]:"left" if tone<=3 else "right" for idx,tone in enumerate(tones)}

    return variables 

def is_connected(active_channels_dict,*args):
    ''' 
    Determine whether chakras are connected through a channel
    Direct and indirect connections are supported (e.g ["TT","AA"],["TT","SN","RT"))
        Params:
           active_channels_dict(dict): all active channels, keys: ["label","planets","gate","ch_gate"]
           given_chakras(str): Chakras that will be checked
    Return:
        bool: returns True if is connected, and false if not
    '''
    #if gate list is emtpy ->Reflector-Typ (no channels at all), return false
    if not len(active_channels_dict["gate"]):
        return False
    else:
        gate_chakras = active_channels_dict["gate_chakra"]
        ch_gate_chakras = active_channels_dict["ch_gate_chakra"]
        for i in range(len(args)-1):
            found = False
            start, end = args[i], args[i+1]
            # Look for start in first set of activated chakras
            for j in range(len(gate_chakras)):
                if start == gate_chakras[j]:
                    if end == ch_gate_chakras[j]:
                        found = True  # Found a connection between these two chakras

            # Look for start in second set of activated chakras
            for j in range(len(ch_gate_chakras)):
                if start == ch_gate_chakras[j]:
                    if end == gate_chakras[j]:
                        found = True  # Found a connection between these two chakras
            
            if not found:
                # Didn't find a connection for these two chakras
                return False  # No path exists
        # If we reach here, then there exists a link for each pair of chakras
        # in the list
        return True


def get_auth(active_chakras,active_channels_dict): 
    ''' 
        get authority from active chakras, 
        selection rules see #https://www.mondsteinsee.de/autoritaeten-des-human-design/
        Args:
            Chakras(set): active chakras
            active_channels_dict(dict): all active channels, keys: ["label","planets","gate","ch_gate"]
        Return:
            authority(str): return inner authority (SP,SL,SN,HT,GC,HT_GC,outer auth)
                HT_GC is referred to as ego projected
    '''
    outer_auth_mask = (("HD" in active_chakras) 
                       | ("AA" in active_chakras) 
                       | ("TT" in active_chakras)
                       )
    if "SP" in active_chakras:
        auth = "Emotional - Solar Plexus"
    elif "SL" in active_chakras:
        auth = "Sacral"
    elif "SN" in active_chakras:
        auth = "Splenic"
    elif (is_connected(active_channels_dict,"HT","TT")): #("HT" in active_chakras) &
        auth= "Ego Manifested"
    elif (is_connected(active_channels_dict,"GC","TT")): #("GC" in active_chakras) &
        auth = "G Center"
    elif ("GC" in active_chakras) & ("HT" in active_chakras):
        auth = "Ego Projected"
    elif outer_auth_mask:
        auth = "Environmental"
    elif (len(active_chakras)==0):
        auth = "Lunar"
    else: auth = "unknown?" #sanity check;-)
    
    return auth

def get_typ(active_channels_dict,active_chakras): 
    ''' 
    get Energy Type from active channels 
        selection rules see (ref.: https://www.mondsteinsee.de/human-design-typen/)
    Args:
        active_channels_dict(dict): all active channels, keys: ["label","planets","gate","ch_gate"]
    Return: 
        typ(str): typ (G=Generator,MG=Manifesting,Generator,P=Projector,
                       M=Manifestor,R=Reflector)
    '''
    # Root is connected with Throat? (direct,indirect)
    RT_TT_isconnected = (is_connected(active_channels_dict,"TT","SN","RT")
                         |is_connected(active_channels_dict,"TT","GC","SN","RT")
                        )
    # Throat is connected with Heart? (direct,indirect)                   
    TT_HT_isconnected = (is_connected(active_channels_dict,"TT","HT")
                         | is_connected(active_channels_dict,"TT","GC","HT")
                         | is_connected(active_channels_dict,"TT","SN","HT")
                        )
    # Throat is connected with Sacral centre? (indirect)
    TT_SL_isconnected = (is_connected(active_channels_dict,"TT","GC","SL")
                         | is_connected(active_channels_dict, "TT", "SL"))
    # Throat connected with energy centres (SP,SL,HT,RT)?
    TT_connects_SP_SL_HT_RT = (TT_HT_isconnected 
                               | TT_SL_isconnected 
                               | is_connected(active_channels_dict,"TT","SP") 
                               | RT_TT_isconnected
                              )

    # If there are no active chakras
    if not active_chakras:
        typ ="Reflector"  # Reflector
    elif ("SL" in active_chakras) and (not TT_connects_SP_SL_HT_RT):
        typ = "Generator"  # Generator
    elif ("SL" in active_chakras) and (TT_connects_SP_SL_HT_RT):
        typ = "Manifesting Generator"  # Manifesting Generator
    elif ("SL" not in active_chakras) and (not TT_connects_SP_SL_HT_RT):
        typ = "Projector"  # Projector
    elif ("SL" not in active_chakras) and (TT_connects_SP_SL_HT_RT):
        typ = "Manifestor"  # Manifestor

    return typ
    
def get_channels_and_active_chakras(date_to_gate_dict,meaning=False):    
    ''' 
    calc active channels:
    take output of hd_features class (date_to_gate_dict) map each gate in col "gate" 
    to an existing channel gate in col "ch_gate" if channel exists, else value=0     
        dict for mapping: full_dict (all possible channels compinations)
    Args:
        date_to_gate_dict(dict):output of hd_feature class 
                                keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        active_channels_dict(dict): all active channels, keys: ["label","planets","gate","ch_gate"]
        active_chakras(set): active chakras
    '''
    df = date_to_gate_dict
    #init lists
    gate_list =  df["gate"]
    ch_gate_list=[0]*len(df["gate"])
    active_chakras = []
    active_channels_dict={}
    gate_label_list=[]
    ch_gate_label_list=[]
    
    #map channel gates to gates, if channel exists and make list of it
    for idx,gate in enumerate(gate_list):

        ch_gate_a = full_dict["full_gate_1_list"]
        ch_gate_b = full_dict["full_gate_2_list"]
        gate_index=np.where(
            np.array(ch_gate_a)==gate
        )
        ch_gate = [ch_gate_b[index] 
                   for index in gate_index[0] 
                   if ch_gate_b[index] in gate_list
                  ]      
        if ch_gate:
            ch_gate_list[idx] = ch_gate[0] 
            active_chakras.append(
                full_dict["full_chakra_1_list"]
                [full_dict["full_gate_1_list"].index(gate)]
            )
            active_chakras.append(
                full_dict["full_chakra_2_list"]
                [full_dict["full_gate_2_list"].index(gate)]
            ) 
    df["ch_gate"]=ch_gate_list

    #filter dict for active channels (ch_gate is not 0)
    mask=np.array(df["ch_gate"])!=0
    
    #duplicate mask remove duplicates (e.g. (1,2) = (2,1))
    sorted_channels = [sorted((df["gate"][i],df["ch_gate"][i])) 
                       for i in range(len(df["gate"]))]
    unique_mask = np.unique(sorted_channels,axis=0,return_index=True)[1]
    dupl_mask = np.zeros(len(sorted_channels),dtype=bool)
    dupl_mask[unique_mask]=True
           
    #filter usefull keys to result dict
    for key in ["label","planets","gate","ch_gate"]: 
        active_channels_dict[key] = np.array(df[key])[dupl_mask&mask]   
    #map chakras to gates in new col["XXX_chakra"]
    active_channels_dict["gate_chakra"] =  [full_dict["full_gate_chakra_dict"][key] 
                                            for key in active_channels_dict["gate"]]
    active_channels_dict["ch_gate_chakra"] =  [full_dict["full_gate_chakra_dict"][key] 
                                               for key in active_channels_dict["ch_gate"]]
    #map labels to open gates and ch_gates
    gate=active_channels_dict["gate"]
    ch_gate=active_channels_dict["ch_gate"]
    
    # convert gates and channel gates to tuple format (1,2)
    for gate,ch_gate in zip(gate,ch_gate):
        idx_gate = np.where(
            np.array(df['gate'])==gate
        )
        idx_ch_gate = np.where(
            np.array(df['gate'])==ch_gate
        )
        gate_label_list.append(
            [df["label"][int(i)] for i in np.nditer(idx_gate)]
        )
        ch_gate_label_list.append(
            [df["label"][int(i)] for i in np.nditer(idx_ch_gate)]
        )
    active_channels_dict["ch_gate_label"] = ch_gate_label_list
    active_channels_dict["gate_label"] = gate_label_list
    
    #if meaning shall be mapped to active channels and returned
    if meaning:      
        #make dict searchable, normal and reversed channels are needed (eg. (1,2) == (2,1))
        meaning_dict = hd_constants.CHANNEL_MEANING_DICT
        full_meaning_dict = {**meaning_dict,**{key[::-1]:value
                                               for key,value in meaning_dict.items()}}
        #get channels in tuple  format
        channels =np.column_stack(
            (active_channels_dict["gate"],active_channels_dict["ch_gate"])
        ) 
        active_channels_dict["meaning"] = [full_meaning_dict[tuple(channel)] 
                                           for channel in channels] 

    return active_channels_dict, set(active_chakras)

def get_split(active_channels_dict,active_chakras):
    """
    calculate split from active channels and chakras
    if 
        connection is circular -> no split -> return:0
        connection is bicircular-> no split -> return:-1
        all chakras are linear connected-> no split ->return:1
        two connected groups-> split -> return:2,
        three connect groups ....
    Args:
        active_channels_dict(dict): all active channels, keys: ["label","planets","gate","ch_gate"]
        active_chakras(set): active chakras
    Return:
        split(int): meaning see above
    """
    #split, remove duplicate tuples (gate,ch_gate chakras) in channels 
    gate_chakra = active_channels_dict["gate_chakra"]
    ch_gate_chakra = active_channels_dict["ch_gate_chakra"]
    sorted_chakras = [sorted((gate_chakra[i],ch_gate_chakra[i])) 
                      for i in range(len(active_channels_dict["gate_chakra"]))]
    unique_mask = np.unique(sorted_chakras,axis=0,return_index=True)[1]
    dupl_mask = np.zeros(len(sorted_chakras),dtype=bool)
    dupl_mask[unique_mask]=True
    len_no_dupl_channel = sum(dupl_mask)
    split = len(active_chakras) - len_no_dupl_channel
    
    return hd_constants.DEFINITION_NAMES[split]
    
def calc_full_gates_chakra_dict(gates_chakra_dict):
    ''' 
    from GATES_CHAKRA_DICT add keys in reversed order ([1,2]==[1,2]) 
    Args:
        gates_chakra_dict(dict): Constants are stored in hd_constants format {(64,47):("HD","AA"),...}
    Return:
        full_dict(dict): dict keys: full_ch_chakra_list,full_ch_list,full_ch_gates_chakra_dict,
                                    full_chakra_1_list,full_chakra_2_list,full_gate_1_list,
                                    full_gate_2_list,full_gate_chakra_dict
    '''
    cols = ["full_ch_chakra_list", #Chakra & Ch_Chakra of all 36*2(with reversed order e.g.["TT","AA"]&["AA","TT"]) channels
             "full_ch_list",       #all 36*2(with reversed order e.g.[1,2]&[2,1]) channels
             "full_ch_gates_chakra_dict", #dict channels:chakra of 36*2(with reversed order e.g.[1,2]&[2,1]) combinations
             "full_chakra_1_list",       #col 1 of full_chakra_list
             "full_chakra_2_list",       #col 2 of full_chakra_list 
             "full_gate_1_list",         #col 1 of full_ch_list
             "full_gate_2_list",         #col 2 of full_ch_list
             "full_gate_chakra_dict",    #dict gate:chakra, map gate to chakra
               ]       
    #init dict            
    full_dict = {k: [] for k in cols}

    #channels in normal and reversed order
    full_dict["full_ch_chakra_list"] = list(gates_chakra_dict.values()) + [item[::-1] 
                                                                           for item in gates_chakra_dict.values()]  
    #channel_chakras in normal and reversed order
    full_dict["full_ch_list"] = list(gates_chakra_dict.keys()) + [item[::-1] 
                                                                  for item in gates_chakra_dict.keys()]  
    #make dict from channels and channel chakras e.g. (1,2):("XX","YY")
    full_dict["full_ch_gates_chakra_dict"] = dict(
        zip(full_dict["full_ch_list"],
            full_dict["full_ch_chakra_list"])
    )
    #select each first chakra, len 72 
    full_dict["full_chakra_1_list"] = [item[0] 
                                       for item in full_dict["full_ch_chakra_list"]] 
    #select each second chakra, len 72
    full_dict["full_chakra_2_list"] = [item[1] 
                                       for item in full_dict["full_ch_chakra_list"]]  
    #select each first gate, len 72
    full_dict["full_gate_1_list"] = [item[0] 
                                     for item in full_dict["full_ch_list"]]  
    #select each second gate(channel_gate), len 72
    full_dict["full_gate_2_list"] = [item[1] 
                                     for item in full_dict["full_ch_list"]]  
    #make dict from first gate and first chakra list, len 72
    full_dict["full_gate_chakra_dict"] = dict(
        zip(full_dict["full_gate_1_list"],
            full_dict["full_chakra_1_list"])
    ) 
    
    return full_dict

#from chakra dict create full_dict (add keys in reversed order) 
full_dict = calc_full_gates_chakra_dict(hd_constants.GATES_CHAKRA_DICT)

def calc_full_channel_meaning_dict():
    """from meaning dict create full dict (add keys in reversed ordere.g. (1,2)/(2,1))"""
    meaning_dict = hd_constants.CHANNEL_MEANING_DICT
    full_meaning_dict = {**meaning_dict,**{key[::-1]:value for key,value in meaning_dict.items()}}
    return full_meaning_dict


def chakra_connection_list(chakra_1,chakra_2):
    ''' 
    from given chakras calc all posible connections (channels)
    list is enlarged by elements in reversed order (e.g. [1,2],[2,1])
    Args:
        chakra_1(str): start chakra 
        chakra_2(str): connecting chakra
    Return: 
        connection list(list): array of lists(gate:ch_gates)
    '''
    #create chakra_dict mask from given chakra and apply it to channel_list
    mask = ((np.array(full_dict["full_chakra_1_list"]) == chakra_1) 
            & (np.array(full_dict["full_chakra_2_list"]) == chakra_2)
           )
    connection_list = np.array(full_dict["full_ch_list"])[mask]
    #if list is not empty
    if len(connection_list): 
        full_connection_list = np.concatenate([connection_list, [item[::-1] 
                                                                 for item in connection_list]])# normal + reverse order   
    else: full_connection_list=[]
           
    return full_connection_list

def get_full_chakra_connect_dict():
    '''
    Get connecting channels between all possible chakras pairs 
    Return:
        connection_dict(dict):array of lists(gate:ch_gates)
    '''
    chakra_connect_dict = {}
    #all posible Chakra pairs of two
    for combination in itertools.combinations(hd_constants.CHAKRA_LIST, 2): 
        connect_channels = chakra_connection_list(*combination)
        chakra_connect_dict.update({combination:connect_channels})
               
    return chakra_connect_dict
        
def calc_single_hd_features(timestamp,report=False,channel_meaning=False,day_chart_only=False):
    '''
    from given timestamp calc basic additional hd_features
    print report if requested
    use hd_features base class
    Parameters
    ---------- 
    timestamp : tuple
        The time of birth. Must be in the format
        (year,month,day,hour,minute,second,tz_offset).
    report : bool
        Prints text report of key features.
    channel_meaning : bool
        add meaning to channels
    day_chart_only : bool
        Only calculate the day chart.

    Returns
    -------
    gate (int), #selected col of planet_df
    active_chakra(set): all active chakras
    typ(str): energy typ [G,MG,P,M,R]
    authority(str): [SP,SL,SN,HT,GC,outher auth]
    incarnation cross(tuple): format ((1,2),(3,4))
    profile(tuple): format (1,2)
    active_channels(dict):  keys [planets,labels,gates and channel gates]
    '''
    ####santity check for input format and values
    if ((len(timestamp)!=7)
    | (len([elem for elem in timestamp[1:6] if elem <0]))
    | (timestamp[1]>12) 
    | (timestamp[2]>31) 
    | (timestamp[3]>24) 
    | (timestamp[4]>60) 
    | (timestamp[5]>60)
        ):
        sys.stderr.write("Format should be:\
        Year,Month,day,hour,min,sec,timezone_offset,\nIs date correct?")
        raise ValueError('check timestamp Format') 
    else:
        instance = hd_features(*timestamp) #create instance of hd_features class

        if day_chart_only:
            date_to_gate_dict = instance.day_chart(instance.time_stamp)
        else:
            date_to_gate_dict = instance.birth_creat_date_to_gate() 
            active_channels_dict,active_chakras = get_channels_and_active_chakras(
                date_to_gate_dict,meaning=channel_meaning)
            typ = get_typ(active_channels_dict,active_chakras)
            auth = get_auth(active_chakras,active_channels_dict)
            inc_cross = get_inc_cross(date_to_gate_dict)
            strategy = hd_constants.STRATEGIES[typ]
            theme = hd_constants.THEMES[typ]
            profile = get_profile(date_to_gate_dict)
            split = get_split(active_channels_dict,active_chakras)
            variables = get_variables(date_to_gate_dict)
            active_chakras = [hd_constants.CHAKRA_NAMES[c] for c in active_chakras]

            if report == True:
                print("birth date: {}".format(timestamp[:-2]))
                print("create date: {}".format(instance.create_date))
                print("energie-type: {}".format(typ))
                print("inner authority: {}".format(auth))
                print("inc. cross: {}".format(inc_cross))
                print("profile: {}".format(profile))
                print("active chakras: {}".format(active_chakras))
                print("split: {}".format(split))
                print("variables: {}".format(variables))
                print(date_to_gate_dict)
                print(active_channels_dict)
         
    if day_chart_only==False:
        return  (typ,                   # 0
                 auth,                  # 1
                 inc_cross,             # 2
                 profile,               # 3
                 split,                 # 4
                 strategy,              # 5
                 theme,                 # 6
                 date_to_gate_dict,     # 7
                 active_chakras,        # 8
                 active_channels_dict)  # 9
    else:
        return date_to_gate_dict

def unpack_single_features(single_result):
    '''
    convert tuple format into dict
    Args:
        single_result(tuple(lists)): hd_key features
    Return:
        return_dict(dict): keys: "typ","auth","inc_cross","profile"
                                 "split,"date_to_gate_dict","active_chakra"
                                 "active_channel"
    '''
    return_dict = {}
    # unpacking multiple calculation values
    return_dict["typ"] = single_result[0]
    return_dict["auth"] = single_result[1] 
    return_dict["inc_cross"] = single_result[2]
    return_dict["inc_cross_typ"] = single_result[3]
    return_dict["profile"] = single_result[4]
    return_dict["split"] = single_result[5]
    return_dict["date_to_gate_dict"] = single_result[6]
    return_dict["active_chakra"] = single_result[7]
    return_dict["active_channel"] = single_result[8]
    
    return return_dict

