
import requests

API_URL = "https://overpass-api.de/api/interpreter"
selected_place = None


def buildOverpassQuery(areaInfo):
    return {"data":
        '[out:json][timeout:120];('+
            'node["place"="town"]' + areaInfo + ';'+
            'node["place"="village"]' + areaInfo + ';'+
            'node["place"="city"]' + areaInfo + ';'+
        ');out body;'
    }

def processOverpassQuery(information):
    x = requests.post(API_URL, data=information)

    placesRetrieved = x.json()

    places = []
    for place in placesRetrieved["elements"]:
        place_object = {
            "type": place["tags"]["place"],
            "coords": {
                "lat": "{:.6f}".format(round(place["lat"], 6)),
                "lon": "{:.6f}".format(round(place["lon"], 6))
            },
            "id": place["id"]
        }
        places.append(place_object)

    return places

# Input, place: coordinates, radius: number (km)
# Returns [{type: village/town/city, coords: {lat: LAT (7 digits), lon: LON (7 digits)}, id: ID}, {}]
def overpassApiCallRadius(place, radius): # Radius or number of places 
    radius_info = "(around:" + str(radius * 1000) + "," + str(place["lat"]) + "," + str(place["lon"]) + ")"

    information = buildOverpassQuery(radius_info)

    return processOverpassQuery(information)

def overpassApiCallBox(mostSouthWestCoord, mostNorthEastCoord):
    box_info = "(" + str(mostSouthWestCoord[0]) + "," + str(mostSouthWestCoord[1]) + "," + str(mostNorthEastCoord[0]) + "," + str(mostNorthEastCoord[1]) + ")"

    information = buildOverpassQuery(box_info)

    return processOverpassQuery(information)

# Query initial coordinates
def queryInitialPlaceCoordinates(place):

    information = {"data":
        '[out:json][timeout:25];('+
            'node["name"="'+ place +'"]["place"="town"];'+
            'node["name"="'+ place +'"]["place"="village"];'+
            'node["name"="'+ place +'"]["place"="city"];'+
        ');out body;'
    }

    x = requests.post(API_URL, data=information)

    placesRetrieved = x.json()

    numElements = len(placesRetrieved["elements"]) 
    
    if numElements == 0:
        exit("No place found with name: " +  place)
    elif numElements == 1:
        return placesRetrieved["elements"][0]
    else:
        locationIndex = 0
        print("Several places with", place, "name were found, select one")
        for place in placesRetrieved["elements"]:
            add = ""
            if "wikipedia" in place["tags"]:
                add += place["tags"]["wikipedia"]
            print("   [" + str(locationIndex) + "]",  "->", place["lat"], place["lon"], add)

            locationIndex += 1

        index = int(input())
        return placesRetrieved["elements"][index]

