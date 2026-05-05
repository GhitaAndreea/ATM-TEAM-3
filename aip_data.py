#aip_data
#Author : Giulia SOTGIA
#
# ------- READ ME ----------------------------
# ATTENTION : Coordinates are in DMS and limit in ft
# Four Functions implemented :
#       get_all_waypoints() : dictionary containing waypoints
#       get_waypoint( Str : name ) : dictionary of info from the 'name' point
#       get_all_military_aeras() : dictionary containing military aeras
#       get_military_aera( Str : name ) : dictionary of info from the 'name' aera
#
# -------- READ ME ----------------------------------

#Waypoint Catalogue


WAYPOINTS = {
    "SODGO" : {"lat": (44, 52, 2) ,"lon": (22, 50, 51) },
    "BACAM": {"lat": (44, 28, 7) ,"lon": (23, 28, 26)},
    "OVDOT" : {"lat": (44, 32, 2) ,"lon": (22, 58, 37)},
    "REPTO" : {"lat": (47, 38, 11) ,"lon": (24, 0, 0)},
    "TEVSA" : {"lat": (46,52,34) ,"lon": (27,12,12)},
    "URELA" : {"lat": (45,29,48) ,"lon": (26,33,40)},
    "VAMON" : {"lat": (44,23,58) ,"lon": (24,40,47)},
    "ADMEC" : {"lat": (47,7,51) ,"lon": (26,34,48)},
    "BUZZE" : {"lat": (47,38,51) ,"lon": (23,47,37)},
    "DANUL" : {"lat": (44,54,24) ,"lon": (28,27,23)},
    "FOCSA" : {"lat": (45,59,41) ,"lon": (26,41,23)},
}

#Military Airspaces Catalogue
MILITARY_AREAS = {
    "LRTRA104G" : {
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
    "LRTRA103M" : {
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
    },
    "LRTRA101L" : {
        "name" : "LRTRA101L",
        "polygon_dms": [
            {"lat": (44,34,22), "lon": (23,40,4)},
            {"lat": (44,19,12), "lon": (24,17,15)},
            {"lat": (44,26,5), "lon": (24,12,20)},
            {"lat": (44,19,1), "lon": (23,44,51)},
            {"lat": (44,34,22), "lon": (23,40,4)}
        ],
        "lower_limit" : 4500, #Ground
        "upper_limit" : 20000 #Amoung Sea Level (AMSL)
    },
    "LRTRA94G" : {
        "name" : "LRTRA94G",
        "polygon_dms": [
            {"lat": (44,47,4), "lon": (25,31,4)},
            {"lat": (44,45,56), "lon": (25,40,15)},
            {"lat": (44,41,45), "lon": (25,41,26)},
            {"lat": (44,44,21), "lon": (25,26,0)},
            {"lat": (44,47,4), "lon": (25,31,4)}
        ],
        "lower_limit" : 0, #Ground
        "upper_limit" : 2000 #Amoung Sea Level (AMSL)
    },
    "LRTRA73U" : {
        "name" : "LRTRA73U",
        "polygon_dms": [
            {"lat": (44,36,13), "lon": (27,7,24)},
            {"lat": (44,34,48), "lon": (27,31,25)},
            {"lat": (44,9,19), "lon": (27,31,25)},
            {"lat": (44,12,5), "lon": (27,19,8)},
            {"lat": (44,13,21), "lon": (27,8,30)},
            {"lat": (44,36,13), "lon": (27,7,24)}
        ],
        "lower_limit" : 28000, 
        "upper_limit" : 35000 #Amoung Sea Level (AMSL)
    },
    "LRTRA102T" : {
        "name" : "LRTRA102T",
        "polygon_dms": [
            {"lat": (44,19,12), "lon": (24,17,15)},
            {"lat": (44,18,49), "lon": (24,17,30)},
            {"lat": (43,55,3), "lon": (24,5,32)},
            {"lat": (44,7,33), "lon": (23,48,37)},
            {"lat": (44,19,1), "lon": (23,44,51)},
            {"lat": (44,19,12), "lon": (24,17,15)}
        ],
        "lower_limit" : 35000, 
        "upper_limit" : 66000 #Amoung Sea Level (AMSL)
    },
    "LRTRA67T" : {
        "name": "LRTRA67T",
        "polygon_dms": [
            {"lat": (45, 19, 12), "lon": (24, 17, 15)},
            {"lat": (44, 18, 49), "lon": (24, 17, 30)},
            {"lat": (43, 55, 3),  "lon": (24, 5, 32)},
            {"lat": (44, 7, 33),  "lon": (23, 48, 37)},
            {"lat": (44, 19, 1),  "lon": (23, 44, 51)},
            {"lat": (44, 19, 12), "lon": (24, 17, 15)}  
        ],
        "lower_limit": 35000, 
        "upper_limit": 66000 #Amoung Sea Level (AMSL)
    },
    "LRTRA71T" : {
        "name": "LRTRA71T",
        "polygon_dms": [
            {"lat": (44, 26, 24), "lon": (27, 55, 21)},
            {"lat": (44, 13, 55), "lon": (28, 23, 23)},
            {"lat": (44, 4, 21),  "lon": (28, 28, 42)},
            {"lat": (44, 3, 4),   "lon": (28, 29, 24)},
            {"lat": (43, 58, 58), "lon": (28, 31, 41)},
            {"lat": (43, 55, 42), "lon": (28, 33, 30)},
            {"lat": (43, 51, 38), "lon": (28, 35, 46)},
            {"lat": (43, 49, 14), "lon": (28, 33, 36)},
            {"lat": (43, 54, 6),  "lon": (28, 5, 46)},
            {"lat": (44, 3, 33),  "lon": (28, 0, 16)},
            {"lat": (44, 4, 29),  "lon": (27, 55, 21)},
            {"lat": (44, 26, 24), "lon": (27, 55, 21)}  
        ],
        "lower_limit": 35000, # FL350
        "upper_limit": 66000  # FL660
    },
    "LRTRA110B" : {
        "name": "LRTRA110B",
        "polygon_dms": [
            {"lat": (47, 33, 53), "lon": (23, 45, 52)},
            {"lat": (47, 27, 22), "lon": (24, 39, 12)},
            {"lat": (47, 25, 33), "lon": (24, 54, 6)},
            {"lat": (47, 24, 39), "lon": (25, 37, 56)},
            {"lat": (47, 23, 59), "lon": (26, 0, 18)},
            {"lat": (47, 23, 23), "lon": (26, 20, 46)},
            {"lat": (47, 19, 9),  "lon": (26, 22, 29)},
            {"lat": (47, 1, 39),  "lon": (26, 29, 32)},
            {"lat": (46, 41, 27), "lon": (26, 37, 34)},
            {"lat": (46, 38, 45), "lon": (26, 35, 15)},
            {"lat": (46, 35, 51), "lon": (26, 33, 54)},
            {"lat": (46, 34, 48), "lon": (25, 57, 8)},
            {"lat": (46, 33, 35), "lon": (25, 12, 12)},
            {"lat": (46, 33, 6),  "lon": (24, 56, 47)},
            {"lat": (46, 32, 53), "lon": (24, 49, 47)},
            {"lat": (46, 32, 46), "lon": (24, 47, 4)},
            {"lat": (46, 32, 32), "lon": (24, 38, 46)},
            {"lat": (46, 32, 18), "lon": (24, 30, 32)},
            {"lat": (46, 32, 2),  "lon": (24, 21, 10)},
            {"lat": (46, 42, 0),  "lon": (24, 13, 0)},
            {"lat": (46, 45, 51), "lon": (24, 9, 51)},
            {"lat": (47, 0, 43),  "lon": (23, 57, 41)},
            {"lat": (47, 27, 16), "lon": (23, 35, 58)},
            {"lat": (47, 28, 51), "lon": (23, 40, 23)},
            {"lat": (47, 31, 22), "lon": (23, 44, 49)},
            {"lat": (47, 33, 53), "lon": (23, 45, 52)}  
        ],
        "lower_limit": 28000, # FL280
        "upper_limit": 66000  # FL660
    },
}


#Functions to export general data
def get_all_waypoints():
    return WAYPOINTS

def get_all_military_areas():
    return MILITARY_AREAS

#Functions to export particular data
def get_waypoint(name):
    if name:
        return WAYPOINTS.get(name.upper())
    return None

def get_military_area(name):
    if name:
        return MILITARY_AREAS.get(name.upper())
    return None


'''
import unittest

class TestAirspaceCatalogue(unittest.TestCase):


    def test_get_waypoint_valid(self):
        result = get_waypoint("SODGO")
        self.assertIsNotNone(result)
        self.assertEqual(result["lat"], (44, 52, 2))

    def test_get_waypoint_case_insensitive(self):
        result = get_waypoint("sodgo")
        self.assertIsNotNone(result)
        self.assertEqual(result["lat"], (44, 52, 2))

    def test_get_waypoint_invalid(self):
        result = get_waypoint("INEXISTANT")
        self.assertIsNone(result)

    def test_get_military_area_valid(self):
        area = get_military_area("LRTRA110B")
        self.assertIsNotNone(area)
        self.assertEqual(area["name"], "LRTRA110B")
        self.assertEqual(area["lower_limit"], 28000)

    def test_get_military_area_case_insensitive(self):
        area = get_military_area("lrtra71t")
        self.assertIsNotNone(area)
        self.assertEqual(area["upper_limit"], 66000)

    def test_get_military_area_none(self):
        self.assertIsNone(get_military_area(""))
        self.assertIsNone(get_military_area(None))

    def test_all_exports(self):
        self.assertEqual(len(get_all_waypoints()), 3)
        self.assertTrue("LRTRA67T" in get_all_military_areas())

if __name__ == '__main__':
    unittest.main()
'''
