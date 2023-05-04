
import math

from constants import PLACE_TYPE_SIZE
from cryptoOperations import sha512HashFromIdPassphrase

# Sort by ID depending on the passphrase
def sortPlaces(places, passphrase):
    for place in places:
        place["sortId"] = sha512HashFromIdPassphrase(place["id"], passphrase)

    places = sorted(places, key=lambda d: d['sortId']) 

    for place in places:
        del place["sortId"]

    return places

# Takes an array of coordinates, and calculate tha maximun capacity
# OUTPUT: number of bytes
def calculateBytesCapacity(places):
    bitsSize = 0
    for place in places: 
        bitsSize += PLACE_TYPE_SIZE[place["type"]]

    maxCipherTextSize = math.floor(bitsSize / 8)

    reduncyRatio = 4/5
    numBlocks = 15
    maxPlainTextSize = maxCipherTextSize * reduncyRatio - 64 + numBlocks

    return math.floor(maxPlainTextSize * 0.8) # A margin is requiered, just in case a point cannot be used to exfiltrate information

