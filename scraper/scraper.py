import json
import os
import sys
import urllib.request
import yaml
import scraper.utils as utils
import argparse
import constants
import time
import repository
import string
import re

from selenium.webdriver.common.action_chains import ActionChains
from constants import LOGGER
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

constants.LOGGER.debug("Starting scraper")



scroll_time = 100
post_da_scrap = 30
total_scrolls = post_da_scrap
current_scrolls = 0
old_height = 0

driver = None
with open(constants.PATH_TO_SELECTORS) as a, open(constants.PATH_TO_PARAMS) as b:
    selectors = json.load(a)
    params = json.load(b)

firefox_profile_path = selectors.get("firefox_profile_path")
facebook_https_prefix = selectors.get("facebook_https_prefix")
facebook_link_body = selectors.get("facebook_link_body")

def get_comments(element, tasto):
    comments = []
    try:

        while True:
            actions = ActionChains(driver)

            time.sleep(0.5)

            if len(element.find_elements_by_xpath(".//a[@class='_4sxc _42ft']")) == 0:
                break
            else:
                tasto = element.find_elements_by_xpath(".//a[@class='_4sxc _42ft']")

            actions.move_to_element(tasto[0]).perform()
            tasto[0].click()

        element = element.find_element_by_xpath(selectors.get("comment_section"))
        element = element.find_elements_by_xpath(".//div[@class='_72vr']")

        cont = 0
        cont_php = 0

        for elem in element:

            try:

                cont += 1
                href_commenti = elem.find_element_by_xpath(selectors.get("comment_author")).get_attribute('href')
                author = elem.find_element_by_xpath(selectors.get("comment_author")).text
                text = elem.find_element_by_xpath(selectors.get("comment_text")).text
                href_finale = href_account(href_commenti)

                if ".php" not in href_finale:
                    comments.append({"author": author, "text": text, "linkToProfile": href_finale})
                else:
                    cont_php += 1

            except Exception as e:
                LOGGER.debug("{}".format(e))

        print(str(cont) + "commenti")
        print(str(cont_php) + "profili.php")

    except Exception as e:
        LOGGER.debug("{}".format(e))

    return comments


def scrap_pag():
    utils.scroll(total_scrolls, driver, selectors, scroll_time)

    #utils.scroll_to_end(driver)

    data = []
    data += driver.find_elements_by_xpath("//div[@class='_4-u2 _3xaf _3-95 _4-u8']")
    data += driver.find_elements_by_xpath("//div[@class='_4-u2 _4-u8']")
    dati_post = []
    testo_pagine = {"postText": "", "comments": [], "location": ""}
    commenti_lista = []
    contatore = 0

    for element in data:
        try:
            if contatore == post_da_scrap:
                break

            LOGGER.debug("post {} of {}".format(contatore, post_da_scrap))
            LOGGER.debug("scraping {}".format(element))

            contatore += 1
            time.sleep(0.5)
            tasto = element.find_elements_by_xpath(".//a[@class='_4sxc _42ft']")

            try:
                luogo = element.find_element_by_class_name("_1dwg._1w_m._q7o")\
                    .find_element_by_xpath(".//span[@class='fcg']/a").text

                if not utils.is_italian_location(luogo):
                    continue
                    
            except Exception as e:
                LOGGER.debug("location not found {}".format(e))
                continue

            try:
                testo = element.find_elements_by_xpath(".//div[@data-testid='post_message']/p")[0].text
            except Exception as e:
                LOGGER.debug("Post has no text")


            LOGGER.debug("Retrieving comments")
            commenti = get_comments(element, tasto)

            LOGGER.debug("appending comments")
            commenti_lista.append(commenti)

            LOGGER.debug("retrieved comments")
            print({"postText": testo, "comments": commenti, "location": luogo})

            dati_post.append({"postText": testo, "comments": commenti, "location": luogo})

        except Exception as e:
            LOGGER.debug("{}".format(e))

    LOGGER.debug("{} inserting to db ".format(dati_post))

    for x in dati_post:

        LOGGER.debug("Inserting post {} num comments {}".format(x, len(x["comments"])))
        repository.insert_post(x)


    scrap_account_commenti()

def scrap_account_commenti():
    scrap = repository.get_users_not_visited()
    if len(scrap)>0:
        for y in scrap:
            try: 
                y = y[0]
                print("href account")
                print(y)
                time.sleep(2)
                href_finale = facebook_https_prefix + facebook_link_body + y
                driver.get(href_finale)
                scrap_profile(y)
            except Exception as e:
                print("com in commenti_lista")
                print(e)


def href_account(href):
    Indice = 0
    try:
        while Indice < len(href):
            if href[Indice] == "?":
               break
            Indice = Indice + 1 
           
    except Exception as e:
        print(e)
    Indice_1 = href.rindex("/")
    href_finale = href[Indice_1+1:Indice]
    return href_finale

def scrape_data(url, scan_list, section, elements_path, save_status,href_account):
    if len(href_account)>0:
        
        output = {"sex": "","cityName": "","contacts": [],"jobs": []}
        tasti=[".//a[@class='_5pwr _84vh']",
               ".//a[@class='_5pwr _84vg']",
               ".//a[@class='_5pwr _84vf']"]

        contatore = ""
        for i in tasti:
            try:
                driver.find_element_by_xpath(".//a[@data-tab-key='about']").click()
                contatore = i
                time.sleep(0.5)
                driver.find_element_by_xpath(i).click()
                time.sleep(1)
                info = driver.find_element_by_xpath("//div[@class='_4ms4']")
                data=[]
                if contatore == tasti[2]:
                    data.append(info.find_element_by_xpath("//div[@id='pagelet_contact']"))
                    data.append(info.find_element_by_xpath("//div[@id='pagelet_basic']"))
                elif contatore == tasti[0]:
                    data = info.find_elements_by_xpath("//div[@class='_4qm1']")
                else:
                    data.append(info.find_element_by_xpath("//div[@id='pagelet_hometown']"))
                print("data")
                print(len(data))
                time.sleep(8)
                for elem in data: 
                    print("ELEMENTO:")
                    print(elem)
                    sezione = elem.find_element_by_xpath(".//div[@class='clearfix _h71']/span").text
                    LOGGER.debug(str(sezione) +  " sezione")
                    if contatore == tasti[0]:
                       try:
                           if "LAVORO" in sezione:
                               output["jobs"] = check_lavori(elem)
                       except Exception as e:
                                print(str(e) + " lavoro exception")

                    if contatore == tasti[1] :
                        try:
                            output["cityName"] = check_citta(elem)
                        except Exception as e:
                                print(str(e) + " citta exception")
                    if contatore == tasti[2]:
                        try:
                            if "BASE" in sezione:
                                output["sex"] = check_sesso(elem)
                        except Exception as e:
                                print(str(e) + " sesso exception")
                            
                        try:
                            if "CONTATTO" in sezione:
                                output["contacts"] = check_contatti(elem)
                        except Exception as e:
                            print(str(e) + " contatto exception")

            except Exception as e:
                print(
                    "Exception (scrape_data)",
                    str(i),
                    "Status =",
                    str(save_status),
                    sys.exc_info()[0],e
                )      
        LOGGER.debug("Insert post")
        print("output per db")
        print(output)
        repository.insert_personal_data(href_account,output)
    else:
        print("href non valido")

def check_lavori(elem):
    lavori = elem.find_elements_by_xpath(".//li[@class='_43c8 _5f6p fbEditProfileViewExperience experience']")
    jobs=[]
    if len(lavori)>0:
       for lavoro in lavori:
           job = lavoro.find_element_by_xpath(".//div[@class='_2lzr _50f5 _50f7']/a").text
           jobs.append(job)
    LOGGER.debug("jobs")
    LOGGER.debug(jobs)
    return jobs

def check_sesso(elem):
    genere = elem.find_element_by_xpath(".//li[@class='_3pw9 _2pi4 _2ge8 _3ms8']")
    sesso = genere.find_element_by_xpath(".//div[@class='clearfix']/div/span").text
    LOGGER.debug(str(sesso) + " sesso")
    sex ="NULL"
    if len(sesso)>0:
        if sesso == "Uomo":
            sex = 1
        if sesso == "Donna":
            sex = 0
    return sex

def check_citta(elem):
    citta = elem.find_elements_by_xpath(".//div[@class='_6a _6b']/span/a")
    city = "NULL"
    if len(citta)>0:
       city = citta[0].text
    LOGGER.debug(city)
    return city

def check_contatti(elem):
    con = driver.find_element_by_xpath(".//li[@class='_3pw9 _2pi4 _2ge8']")
    contatti = con.find_elements_by_xpath(".//div[@class='_50f7']/span[1]")
    contacts=[]
    c=[]
    if len(contatti)>0:
       for x in contatti:
          c.append(x.text)
       contacts=check_regex(c)
    return contacts

def check_mail(email,regex):  
    if(re.search(regex,email)):  
        return "EMAIL" 
          
    else:  
        return ""
def check_num(num,regex):
    if(re.search(regex,num)):  
        return "NUMERO" 
          
    else:  
        return ""

def check_regex(cont):
    try:
        time.sleep(1)
        contacts = []
        for x in cont:
            regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
            type_mail = check_mail(x,regex)
            if type_mail == "EMAIL":
                type = type_mail
            else:
                regex = '((([+]|00)(\\s|\\s?\\-\\s?)?[0-9]{1,3})?([-\\s\\.])?([(]?[0-9]{1,3}[)])?([-\\s\\.])?)([0-9]{3,4})(\\/)?[-\\s\\.]?([0-9]{2,3})[-\\s\\.]?([0-9]{2,3})[-\\s\\.]?([0-9]{1,4})'
                type_num = check_num(x,regex)
                type = type_num

            contacts.append({"contact":x,"type":type})

    except Exception as e:
        print(e)
    return contacts

def scrap_profile(href_account):
    # execute for all profiles given in input.txt file
    url = driver.current_url
    user_id = create_original_link(url)

    print("\nScraping:", user_id)
    print("----------------------------------------")
    print("Scraping {}..".format("About"))
    scan_list = [None] * 4
    section = params["About"]["section"]
    elements_path = params["About"]["elements_path"]
    save_status = params["About"]["save_status"]
    time.sleep(1)
    scrape_data(user_id, scan_list, section, elements_path, save_status,href_account)

    print("{} Done!".format("About"))

    print("Finished Scraping Profile " + str(user_id) + ".")
    
def login(email, password):
    """ Logging into our own profile """

    try:
        global driver

        options = Options()

        #  Code to disable notifications pop up of Chrome Browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        # options.add_argument("headless")

        try:
            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=options
            )
        except Exception:
            print("Error loading chrome webdriver " + sys.exc_info()[0])
            exit(1)

        fb_path = facebook_https_prefix + facebook_link_body
        driver.get(fb_path)
        driver.maximize_window()

        # filling the form
        driver.find_element_by_name("email").send_keys(email)
        driver.find_element_by_name("pass").send_keys(password)

        try:
            # clicking on login button
            driver.find_element_by_id("loginbutton").click()
        except NoSuchElementException:
            # Facebook new design
            driver.find_element_by_name("login").click()

        # if your account uses multi factor authentication
        mfa_code_input = utils.safe_find_element_by_id(driver, "approvals_code")

        if mfa_code_input is None:
            return

        mfa_code_input.send_keys(input("Enter MFA code: "))
        driver.find_element_by_id("checkpointSubmitButton").click()

        # there are so many screens asking you to verify things. Just skip them all
        while (
            utils.safe_find_element_by_id(driver, "checkpointSubmitButton") is not None
        ):
            dont_save_browser_radio = utils.safe_find_element_by_id(driver, "u_0_3")
            if dont_save_browser_radio is not None:
                dont_save_browser_radio.click()

            driver.find_element_by_id("checkpointSubmitButton").click()

    except Exception:
        print("There's some error in log in.")
        print(sys.exc_info()[0])
        exit(1)


def create_original_link(url):
    print(str(url) + " url Original link")
    if url.find(".php") != -1:
        original_link = (
            facebook_https_prefix + facebook_link_body + ((url.split("="))[1])
        )
   
        if original_link.find("&") != -1:
            original_link = original_link.split("&")[0]

    elif url.find("fnr_t") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + ((url.split("/"))[-1].split("?")[0])
        )
    elif url.find("_tab") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + (url.split("?")[0]).split("/")[-1]
        )
    else:
        original_link = url
    print(str(original_link) + " url Original link")
    return original_link


def scrape():
    
    urls = [
        line
        for line in open(constants.PATH_TO_INPUT, newline="\r\n")
        if not line.lstrip().startswith("#") and not line.strip() == ""
    ]
    print(urls)
    if len(urls) > 0:
        print("\nStarting Scraping...")
        login("m.marcuzzi@outlook.it", "scraper")
        for url in urls:
            driver.get(url)
            print("url:" +url)
            scrap_pag()

        driver.close()
    else:
        print("Input file is empty.")



# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------