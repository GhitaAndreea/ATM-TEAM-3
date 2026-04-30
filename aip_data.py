#aip_data
#Author : Giulia SOTGIA
# ATTENTION : Coordinates are in DMS 

#Waypoint Catalogue
WAYPOINTS = {
    "SODGO" : {"lat": (44, 52, 2) ,"lon": (22, 50, 51) },
    "BACAM": {"lat": (44, 28, 7) ,"lon": (23, 28, 26)},
    "OVDOT" : {"lat": (44, 32, 2) ,"lon": (22, 58, 37)},
}

#Data on the Military Airspace
MIILITARY_AREAS = [
    {
        "name" : "LRTRA104G",
        "polygon_dms": [
            {"lat": (44,59,41), "lon": (22,55,12)},
            {"lat": (44,56,45), "lon": (23,18,23)},
            {"lat": (44,35,22), "lon": (23,25,22)},
            {"lat": (44,36,58), "lon": (23,4,6)},
            {"lat": (44,59,41), "lon": (22,55,12)}
        ],
        "lower_limit" : 0, #Ground
        "upper_limit" : 4500 #Amoung Sea Level (AMSL)
    },
    {
        "name" : "LRTRA103M",
        "polygon_dms": [
            {"lat": (44,29,4), "lon": (23,4,10)},
            {"lat": (44,28,31), "lon": (23,27,31)},
            {"lat": (43,59,14), "lon": (23,37,2)},
            {"lat": (44,2,26), "lon": (23,17,25)},
            {"lat": (44,29,4), "lon": (23,4,10)}
        ],
        "lower_limit" : 20000, 
        "upper_limit" : 28000 #Amoung Sea Level (AMSL)
    }
]


#Functions to export data
def get_waypoints(name):
    return WAYPOINTS.get(name)

def get_military_areas():
    return MIILITARY_AREAS