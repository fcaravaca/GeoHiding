import math

from constants import PLACE_TYPE_SIZE

def get_distance(coords1, coords2):
    """
    Calculate the distance between two sets of latitude and longitude coordinates using the Haversine formula.
    """
    lat1, lon1 = coords1
    lat2, lon2 = coords2
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    R = 6371  # Radius of the earth in km
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

# Takes a coords object, and get the closest point
# This has to be used to recover the original place? 
# Returns closest place
def getClosestPlace(coords, places):
    """
    Given a set of latitude and longitude coordinates and a list of places, return the closest place to the coordinates.
    """
    closest_place = None
    closest_distance = float("inf")
    for place in places:
        distance = get_distance((coords["lat"], coords["lon"]), (place["coords"]["lat"], place["coords"]["lon"]))
        if distance < closest_distance:
            closest_place = place
            closest_distance = distance
    return closest_place

# Takes a place object and change them with data.
def alterCoordsWithData(place, data):
    numberOfBits = PLACE_TYPE_SIZE[place["type"]]
    max_decimals = len(str(2**numberOfBits))
    
    # Change binary to decimal
    decimal = int(data,base=2)

    # Pad with 0s if not maximum digits
    decimal = "0" * (max_decimals - len(str(decimal))) + str(decimal)

    lat = place["coords"]["lat"][:int(-max_decimals/2)] + decimal[:int(max_decimals/2)]
    lon = place["coords"]["lon"][:int(-max_decimals/2)] + decimal[int(max_decimals/2):]

    # Insert data (bits) into coords (binary to decimal)
    modified_coords = {"lat": lat, "lon": lon}
    
    return modified_coords

# Habría que comprobar que el closest place a estas coordenadas modificadas sigue siendo el
# de antes

def extractBinaryFromCoords(place):
    numberOfBits = PLACE_TYPE_SIZE[place["type"]]
    max_decimals = len(str(2**numberOfBits))

    firstDec = place["coords"]["lat"][int(-max_decimals/2):]
    lastDec = place["coords"]["lon"][int(-max_decimals/2):]

    extractedData = int(firstDec + lastDec)

    # Change decimal to binary
    binary = str(bin(extractedData)[2:])

    # Pad with 0s if not maximum digits
    extended_binary = "0" * (numberOfBits - len(binary)) + str(binary)
    
    return extended_binary

def find_bounds(coords):
    lats = [float(coord['lat']) for coord in coords]
    longs = [float(coord['lon']) for coord in coords]
    most_south_west = (min(lats) - 0.02, min(longs) - 0.02)
    most_north_east = (max(lats) + 0.02, max(longs) + 0.02)
    return most_south_west, most_north_east
