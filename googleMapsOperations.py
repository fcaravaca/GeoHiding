import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import subprocess
import os
import platform
import time

class ListAlreadyCreated(Exception):
    pass

class PlaceAlreadySavedOnAnotherList(Exception):
    pass


def initialize():
    print("Starting")
    chrome_path = None
    # Detect the operating system
    if platform.system() == 'Windows':
        # Search for the Chrome executable in the PATH environment variable on Windows
        for path in os.environ.get("PATH", "").split(os.pathsep):
            chrome_executable = os.path.join(path, "chrome.exe")
            if os.path.exists(chrome_executable):
                chrome_path = chrome_executable
                break
        if not chrome_path: # Windows default
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    else:
        # Use the which command to find the location of the Chrome executable on Linux
        chrome_executable = subprocess.check_output(['which', 'google-chrome']).decode('utf-8').strip()
        chrome_path = chrome_executable

    if os.path.isfile(chrome_path):
        # Launch Chrome
        chrome_args = ['--remote-debugging-port=9222']
        subprocess.Popen([chrome_path] + chrome_args)
    else:
        input("Chrome Executable was not found. Open Google Chrome with --remote-debugging-port=9222, press any key to continue")

    # Create a ChromeOptions object
    chrome_options = webdriver.ChromeOptions()

    # Set the remote debugging port to connect to the existing browser session
    
    chrome_options.debugger_address = "localhost:9222"
    time.sleep(1)
    # Create the driver with the ChromeOptions object
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://maps.google.com")
    driver.implicitly_wait(5)

    return driver

def load_list(list_url):
    driver = initialize()
    print("Going to Google Maps")
    driver.get(list_url)

    # identify scrolling element first i.e. the sidebar
    scrolling_element_xpath = '//div[@role="main"]/div[@tabindex]'
    wait = WebDriverWait(driver, 10)
    scrolling_element = wait.until(EC.visibility_of_element_located((By.XPATH, scrolling_element_xpath)))

    # use height of element to determine if need to scroll 
    prev_height = driver.execute_script("return arguments[0].scrollHeight", scrolling_element)
    

    PAUSE_TIME = 0.8
    sameHeight = 0
    scrollDownCount = 0

    while True:
        # Scroll down
        driver.execute_script('arguments[0].scrollTo(0, arguments[0].scrollHeight)', scrolling_element)

        time.sleep(PAUSE_TIME)
       
        next_height = driver.execute_script("return arguments[0].scrollHeight", scrolling_element)

        if next_height == prev_height:
            if sameHeight == 5: # Wait up to PAUSE_TIME * 5 seconds to scroll down
                break
            else:
                sameHeight += 1
        else:
            sameHeight = 0
            scrollDownCount += 1
        if scrollDownCount > 20:
            time.sleep(scrollDownCount/20)
        prev_height = next_height


    ## obtain the html
    htmlDownloaded = BeautifulSoup(driver.page_source, 'html.parser')
    selector = "div.m6QErb.DxyBCb.kA9KIf.dS8AEf > div> div.WHf7fb > div.IMSio > div.l1KL8d > div.tSVUtf > div:nth-child(1) > span"
    items = htmlDownloaded.select(selector)
    print(f'Number of elements retrieved: {len(items)}')

    #conver the coordinates to dictionary
    coordinates = []

    # extraction the latitude and longitude values
    for i in range(0, len(items)):
        lat_lon_str = str(items[i]).replace('<span>', '').replace('</span>', '')
        match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+)\)', lat_lon_str)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            coordinates.append({'lat': "{:.6f}".format(lat), 'lon':  "{:.6f}".format(lon)})

    driver.close()

    return coordinates

def search_location(location, driver):
    print(location, end=", ")
    inputElement = driver.find_element(By.ID, "searchboxinput")
    inputElement.clear()
    inputElement.send_keys(location)
    inputElement.send_keys(Keys.ENTER)
 
def save_location(list_name, driver, firstElement):
    wait = WebDriverWait(driver, 8)

    try:
        save_button = wait.until(EC.visibility_of_element_located((By.XPATH, '//img[contains(@src,"bookmark_border_gm_blue_18")]')))
        save_button.click()
    except:
        print("save button not found")
        try:
            is_button_already_saved = wait.until(EC.visibility_of_element_located((By.XPATH, '//img[contains(@src,"saved-custom")]')))
            raise PlaceAlreadySavedOnAnotherList()
        except:
            raise Exception("No save buttons were found")
    
    action_menu = wait.until(EC.visibility_of_element_located((By.ID, "action-menu")))
    
    divs = action_menu.find_elements(By.XPATH, "./div")
    
    element = None

    for option in divs:
        if option.text == list_name:
            print("found location", end=" -> ")
            element = option
            break

    if element:
        if firstElement:
            raise ListAlreadyCreated()
        else:
            element.click()
    else:
        if not firstElement:
            raise Exception("List was not found")
        print("list not created. Creating new list", end=" -> ")
        createListButton = divs[-2]
        createListButton.click()

        time.sleep(1)
        listInput = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@id='modal-dialog']//input")))
        listInput.send_keys(list_name)
        time.sleep(1)

        createButton =  wait.until(EC.visibility_of_element_located((By.ID, "last-focusable-in-modal")))
        createButton.click()
        time.sleep(4)


    popup = wait.until(EC.visibility_of_element_located((By.XPATH, '//div[@jsaction="mouseover:snackbar.hover;mouseout:snackbar.hover"]')))
    
    if popup:
        print("element was saved sucessfully", end = " ") 
        xButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//button[@jsaction="snackbar.dismiss"]')))
        xButton.click()
  

def share_list(list_name, driver):
    wait = WebDriverWait(driver, 10)
    try:
        savedButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//button[@jsaction="navigationrail.saved"]')))

        savedButton.click()
    except:
        menuButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//button[contains(@jsaction,"settings.open")]')))
        menuButton.click()
        
        savedButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//button[contains(@jsaction,"settings.yourplaces")]')))
        savedButton.click()


    listButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//button[@aria-label="' + list_name  +'"]')))
    listButton.click()

    time.sleep(3)

    shareButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//button[@jsaction="pane.savedPlaceList.share; focus:pane.focusTooltip; blur:pane.blurTooltip"]')))
    shareButton.click()

    privateButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//button[@jsaction="pane.placeListShareSelector.change"]')))
    privateButton.click()

    publicButton = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="hovercard"]/div/div[3]')))
    publicButton.click()

    urlContainer = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@jsaction="pane.copyLink.clickInput"]')))

    print("Link:", urlContainer.get_attribute("value"))
    return urlContainer.get_attribute("value")


def putPlaceAndSave(loc, driver, list_name, firstElement):
    try:
        search_location(loc, driver)
        save_location(list_name, driver, firstElement)
    except ListAlreadyCreated:
        exit("\n" + "===" * 25 + "\n" * 2 + f"The list {list_name}, was already created, you cannot reuse lists to hide information" + "\n" * 2 + "===" * 25 )
    except PlaceAlreadySavedOnAnotherList:
        exit("\n" + "===" * 25 + "\n" * 2+ f"The location {loc} was already used in another list, remove that list or choose another place" + "\n" * 2+ "===" * 25 )
    except Exception:
        try:
            print("Waiting 6 seconds due to failure")
            time.sleep(2)
            driver.get("https://maps.google.com")
            time.sleep(4)
            search_location(loc, driver)
            save_location(list_name, driver, firstElement)
        except Exception as e:
            exit("\n" + "===" * 25 + "\n" * 2+ f"The program could not save location {loc}, due to: {str(e)}" + "\n" * 2+ "===" * 25 )



def putPlacesOnMaps(coords, list_name):

    driver = initialize()
    amount = 0
    firstElement = True
    for loc in coords:
        putPlaceAndSave(loc, driver, list_name, firstElement)
        amount += 1
        print("- Progress:", str(round(amount * 100/len(coords),2)))
        firstElement = False

    link = share_list(list_name, driver)
    driver.close()
    return link




