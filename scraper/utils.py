import argparse
import requests
import os
import re
import sys
import time
from constants import LOGGER
from calendar import calendar

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait


def is_italian_location(location):
    location = location.lstrip().rstrip().replace(" ", "+") + "+wikipedia"

    LOGGER.debug("Testing location {}".format(location))

    try:
        query = requests.get("https://www.google.com/search?q={}".format(location))

        wikipedia_page = requests.get(re.search('https://it.wikipedia.org/.+?(?=&amp)', query.text).group())
        LOGGER.debug("wikipedia page {}".format(wikipedia_page))

    except Exception as e:

        LOGGER.debug("Error while locating nation")
        LOGGER.debug("wikipedia page {}".format(wikipedia_page))

    is_italian = ('<span style="white-space:nowrap"><a href="/wiki/File:Flag_of_Italy.svg" class="image" title="Italia">'
            in wikipedia_page.text)

    LOGGER.debug("Location {} is italian? {}".format(location, is_italian))
    return is_italian

# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def create_folder(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)


# -------------------------------------------------------------
# Helper functions for Page scrolling
# -------------------------------------------------------------
# check if height changed
def check_height(driver, selectors, old_height):
    new_height = driver.execute_script(selectors.get("height_script"))
    return new_height != old_height


# helper function: used to scroll the page
def scroll(total_scrolls, driver, selectors, scroll_time):
    global old_height
    current_scrolls = 0

    while True:
        try:
            if current_scrolls == total_scrolls:
                return
            old_height = driver.execute_script(selectors.get("height_script"))
            driver.execute_script(selectors.get("scroll_script"))
            WebDriverWait(driver, scroll_time, 0.05).until(
                lambda driver: check_height(driver, selectors, old_height)
            )
            current_scrolls += 1
        except TimeoutException:
            break

    return


def scroll_to_end(driver):
    SCROLL_PAUSE_TIME = 1

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def safe_find_elements_by_xpath(driver, xpath):
    try:
        return driver.find_elements_by_xpath(xpath)
    except NoSuchElementException:
        return None


def safe_find_element_by_id(driver, elem_id):
    try:
        return driver.find_element_by_id(elem_id)
    except NoSuchElementException:
        return None