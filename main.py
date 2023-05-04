import placesOperations
import overpassApiCalls
import googleMapsOperations
import coordinatesOperations
import cryptoOperations

from constants import PLACE_TYPE_SIZE

import argparse

def parse_arguments():

    parser = argparse.ArgumentParser(description='Exfiltrate or recover a message using Google Maps.')
    subparsers = parser.add_subparsers(dest='command')

    # Exfiltrate/Hide command
    hide_parser = subparsers.add_parser('exfiltrate', help='Hide a message within a radius from a location')
    hide_group = hide_parser.add_mutually_exclusive_group(required=True)
    hide_group.add_argument('-m', '--message', type=str, help='The message to hide')
    hide_group.add_argument('-i', '--input', type=str, help='The input file')

    hide_parser.add_argument('-p', '--passphrase', type=str, required=True, help='A passphrase should be provided')
    hide_parser.add_argument('-n', '--name', type=str, required=True, help='The name of the list')
    hide_parser.add_argument('-l', '--location', type=str, required=True, help='The location to search')
    hide_parser.add_argument('-R', '--radius', type=float, default=50, help='The radius from the location')

    # Recover command
    recover_parser = subparsers.add_parser('recover', help='Recover a message from a Google Maps link')
    recover_parser.add_argument('-p', '--passphrase', type=str, required=True, help='A passphrase should be provided')
    recover_parser.add_argument('-o', '--output', type=str, help='The output file name')
    recover_parser.add_argument('google_maps_link', type=str,  help='The Google Maps link')


    args = parser.parse_args()

    if args.command == 'exfiltrate' or args.command == 'recover':
        return args
    else:
        parser.print_help()
        return None


def populatePlacesWithData(places, binary, passphrase):

    binary = cryptoOperations.transformBinaryToSecret(binary, passphrase)

    initialBinaryPosition = 0

    altered_coords_array = []

    for place in places:
        numberOfBits = PLACE_TYPE_SIZE[place["type"]]
        try:
            altered_coords = coordinatesOperations.alterCoordsWithData(place, binary[initialBinaryPosition: initialBinaryPosition + numberOfBits])
            
            # Do not save place if it changes the location
            if coordinatesOperations.getClosestPlace(altered_coords, places)["id"] is not place["id"]:
                continue

            altered_coords_array.append(
                altered_coords
            )
            initialBinaryPosition += numberOfBits
            if initialBinaryPosition > len(binary):
                break
        except:
            pass
    return altered_coords_array

def insertSecret(secret, places, passphrase, list_name):
    new_places = populatePlacesWithData(places, secret, passphrase)

    print(f"{len(new_places)} places to insert")
    if len(new_places) > 1000:
        print("More than 1000 places, the input is too big and might not be recoverable")
        user_input = input("Follow? [y/N]: ")
        if user_input.lower() != "y":
            exit()

    array_to_inject_in_maps = []
    for place in new_places:
        array_to_inject_in_maps.append(place["lat"] + " " + place["lon"])

    link = googleMapsOperations.putPlacesOnMaps(array_to_inject_in_maps, list_name)
    return link



def getSecret(link, passphrase): # link
    new_coords = googleMapsOperations.load_list(link)

    new_places = []

    mostSouthWestCoord, mostNorthEastCoord = coordinatesOperations.find_bounds(new_coords)

    places = overpassApiCalls.overpassApiCallBox(mostSouthWestCoord, mostNorthEastCoord)

    for coords in new_coords:
        original_place = coordinatesOperations.getClosestPlace(coords, places)
        original_place["coords"]["lat"] = coords["lat"]
        original_place["coords"]["lon"] = coords["lon"]
        new_places.append(original_place)


    new_places = placesOperations.sortPlaces(new_places, passphrase)

    binary = ""
    for place in new_places[:-1]:
        bin_string = coordinatesOperations.extractBinaryFromCoords(place)
        binary += bin_string

    remaining = 160 - (len(binary) % 160) # As information is encrypted, it should always be BLOCK_SIZE length, so the last place, may have not useful bits

    binary += coordinatesOperations.extractBinaryFromCoords(new_places[-1])[-remaining:]
    binary = cryptoOperations.transformSecretToBinary(binary, passphrase)

    return binary


def recoverTextFromBinary(binary):
    ascii_string = ""
    for i in range(0, len(binary), 8): # Recover text
        byte = binary[i:i+8]
        decimal = int(byte, 2)
        ascii_char = chr(decimal)
        ascii_string += ascii_char

    return ascii_string



if __name__ == "__main__":

    arguments = parse_arguments()
    
    if arguments is None:
       exit()

    if arguments.command == "recover":
        binary = getSecret(arguments.google_maps_link, arguments.passphrase)
        if arguments.output:
            with open(arguments.output, "wb") as fh:
                fh.write(bytes(int(binary[i:i+8], 2) for i in range(0, len(binary), 8)))
        else:
            print("===" * 25)
            print("Output:")
            print(recoverTextFromBinary(binary))
            print("===" * 25)

    elif arguments.command == "exfiltrate":
        places = None
        capacity = 0
        index = 0

        binary_str = None
        if arguments.message:
            print("Saving message")
            binary_str = ''.join(format(ord(c), '08b') for c in arguments.message)

        elif arguments.input:
            try:
                with open(arguments.input, "rb") as fh:
                    fileBinary = fh.read()
            except FileNotFoundError:
                exit("===" * 25 + "\n"*2 + f"File {arguments.input} was not found" + "\n"*2 + "===" * 25)
            binary_str = ''.join(['{:08b}'.format(x) for x in fileBinary])


        initialPlaceCoordinates = overpassApiCalls.queryInitialPlaceCoordinates(arguments.location)

        while capacity*8 < len(binary_str):
            places = overpassApiCalls.overpassApiCallRadius(initialPlaceCoordinates, arguments.radius + index * 25)
            capacity = placesOperations.calculateBytesCapacity(places)
            print("Capacity:", capacity)
            index += 1
        places = placesOperations.sortPlaces(places, arguments.passphrase)
        
        link = insertSecret(binary_str, places, arguments.passphrase, arguments.name)


