from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os
import time
import pickle
import shutil
from threading import Thread
from threading import Lock

import pandas as pd
import numpy as np
from unidecode import unidecode

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from seleniumwire import webdriver

from .collector import Collector

class Xractor(Collector):
    def __init__(self, workers=1, headless=False, manual_signin=False,
                 base_url="https://www.amazon.com", sign_in_url="https://www.amazon.com/gp/sign-in.html",
                 cookies_file="cookies.pkl", fname_in_file="file", link_in_file="link",
                 meta_file="log.csv",
                 overwrite_old_movie_dirs=True, retries=3):
        """
        Initializes a Xray collector with customizable options and number of workers.

        Args:
            workers (int): Number of workers to initialize for parallelization.
            headless (bool): If True, runs the browser in headless mode.
            manual_signin (bool): If True, the user will be asked to manually add credentials, else a env file must be provided with Amazon username and password.
            base_url (str): Base URL of the website to collect.
            sign_in_url (str): URL of the sign-in webpage.
            cookies_file (str): File to save cookies in.
            fname_in_file (str): Column name of unique filenames in the input file.
            link_in_file (str): Column name of movie links in the input file.
            meta_file (str): File to save metadata in.
            overwrite_old_movie_dirs (bool): If True, overwrites old movie directories if already downloaded in the downloaded xrays directory.
            retries (int): Number of times to retry getting the resources which may fail because of network issues or other unexpected errors.
        """
        super().__init__(headless, fast_load=True)
        self.wire_options = {
            'disable_encoding': True  # Ask the server not to compress the response
        }
        self.BASE_URL = base_url
        self.sign_in_url = sign_in_url
        self.cookies_file = cookies_file

        self.fname_in_file = fname_in_file
        self.link_in_file = link_in_file

        self.meta_file = meta_file

        self.overwrite_old_movie_dirs = overwrite_old_movie_dirs
        self.retries = retries

        self.lock = Lock()

        load_dotenv()

        if os.getenv("USER") == None or os.getenv("PASS") == None:
            raise Exception("""env file not configured with username and password.
                            Expected `USER` and `PASS`.
                            """)

        self.WORKERS = workers
        self.wait_time = 60

        self.manual_signin = manual_signin
        
        if not os.path.exists(os.path.join(os.getcwd(), self.cookies_file)):
            print("No cookies found, signing in first.")
            print("Loading the driver for signin.")
            signin_driver = self.get_driver()
            self.sign_in(self.sign_in_url, signin_driver)
            signin_driver.quit()

    def get_driver(self):
        """
        Returns the webdriver with necessary driver options. 
        
        Sets the driver scopes to look for the "Playback Resources" and "Xray" files. 
       
        """
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options, seleniumwire_options=self.wire_options)
        
        chrome_install = ChromeDriverManager().install()

        folder = os.path.dirname(chrome_install)
        chromedriver_path = os.path.join(folder, "chromedriver.exe")

        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=self.options, seleniumwire_options=self.wire_options)
        
        driver.scopes = [
            "https://atv-ps.amazon.com/cdp/catalog/GetPlaybackResources",
            "https://atv-ps.amazon.com/swift/page/xrayVOD"
        ]
        self.driver = driver
        return driver

    def get_element_with_id(self, id):
        """
        Waits for the presence of an HTML element with the specified ID on the page.

        Args:
            element_id (str): The ID attribute of the HTML element to locate.

        Returns:
            selenium.webdriver.remote.webelement.WebElement: The located WebElement.
        
        Raises:
            selenium.common.exceptions.TimeoutException: If the element is not found within the specified wait time.
        """
        return WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located((By.ID, id))
        )

    def sign_in(self, address, driver):
        """
        Signs into the given address using a driver.

        Uses `USER` and `PASS` keys from a `.env` file for username and password.

        Args:
            address (str): URL of the sign-in webpage
            driver (webdriver.Chrome): Associated webdriver
        """
        if os.path.exists(os.path.join(os.getcwd(), self.cookies_file)):
            print("Found old session, loading cookies...")
            self.load_session(driver)
            return
        
        load_dotenv()

        # Go to the sign in page
        driver.get(address)
        
        if not self.manual_signin:
            # Enter username and password
            uname_el = self.get_element_with_id("ap_email")
            uname_el.send_keys(os.getenv("USER"))
            
            self.get_element_with_id("continue").click()

            password_el = self.get_element_with_id("ap_password")
            password_el.send_keys(os.getenv("PASS"))
            remember_me = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            remember_me.click()

            self.get_element_with_id("signInSubmit").click()
            
        input("Please sign in, fill any OTP if present, and press enter...")

        try:
            print("Saving Cookies...")
            pickle.dump(driver.get_cookies(), open(self.cookies_file, "wb"))
        except:
            raise Exception("Couldn't save cookies.")
    
    def load_session(self, driver):
        """
        Loads the cookies from locally saved cookies file.

        Args:
            driver (webdriver.Chrome): Associated webdriver
        """
        driver.get("https://www.amazon.com/404")
        cookies = pickle.load(open(self.cookies_file, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
    
    def check_captcha(self, driver):
        """
        Checks for captcha and saves the cookies if found.

        Args:
            driver (webdriver.Chrome): Associated webdriver
        """
        try:
            driver.find_element(By.XPATH, '//button[text()="Continue shopping"]')
            input("Captcha detected. Fill in and press enter...")
            time.sleep(5)

            pickle.dump(driver.get_cookies(), open(self.cookies_file, "wb"))
        except:
            pass

    def check_for_ad(self, driver):
        """
        Check if we have a Prime Video intro before a movie

        Args:
            driver (webdriver.Chrome): Associated webdriver
        """
        try:
            skipbtn = WebDriverWait(driver, self.wait_time * 2).until(
                EC.presence_of_element_located((By.XPATH, "//div[text()='Skip']"))
            )
            
            actions = ActionChains(driver)
            actions.move_to_element(skipbtn)
            actions.click(skipbtn).perform()
        except:
            pass
    
    def check_for_freevee(self, driver):
        """
        Check if we have a Freevee ad before a movie

        Args:
            driver (webdriver.Chrome): Associated webdriver
        """
        counter = 0
        # we are sure that the content is freevee so we'll try to skip at least 3 times
        while counter <= 1:
            try:
                text = WebDriverWait(driver, self.wait_time * 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "atvwebplayersdk-adtimeindicator-text"))
                )
                # print("Found text")
                
                playbtn = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "atvwebplayersdk-playpause-button"))
                )
                # print("Found play button")

                actions = ActionChains(driver)
                # print("moving to element")
                # try:
                actions.move_to_element(text).perform()
                # except:
                #     print("problem moving to element")
                
                # print("clicking element")
                # Interestingly, clicking on the text instead of the play button seems to remove the block
                actions.click(text).perform()
                break
            except:
                print("Couldn't find freevee ad intro")
                pass
            counter += 1
        
    def capture_resources(self, driver, dir_name, is_freevee):
        """
        Captures the Xray and PlaybackResources files for the current movie.

        Args:
            driver (webdriver.Chrome): Associated webdriver
            dir_name (str): Directory name to save the files in
            is_freevee (bool): If True, the movie is a Freevee movie
        """
        add_meta = {'playback': None, 'xray': None, 'all_resource': False}
        
        # Number of times to try getting the resources
        counter = 0
        while True:
            try:
                # gathering the playback resources
                req_pb = driver.wait_for_request("https://atv-ps.amazon.com/cdp/catalog/GetPlaybackResources", timeout=self.wait_time * 2)
                with open(os.path.join(dir_name, "PlaybackResources.json"), 'wb') as f:
                    f.write(((req_pb.response.body)))
                    add_meta['playback'] = "yes"
            except:
                print("Timeout in getting the playback resources")
                add_meta['playback'] = "error"
            
            if is_freevee:
                t = Thread(target=self.check_for_freevee, args=(driver,), daemon=True)
            else:
                t = Thread(target=self.check_for_ad, args=(driver,), daemon=True)
            t.start()

            try:
                # print("Looking for xray...")
                # get the xray data
                req_xray = driver.wait_for_request("https://atv-ps.amazon.com/swift/page/xrayVOD", timeout=self.wait_time * 2)
                with open(os.path.join(dir_name, "Xray.json"), 'wb') as f:
                    f.write(((req_xray.response.body)))
                # print("Got all resources")
                add_meta['xray'] = "yes"
                add_meta['all_resource'] = True

                # print("Finishing up search for skip...")
                t.join()
                break
            except:
                add_meta['xray'] = "no"
                counter += 1
                if counter >= self.retries: 
                    break 
                driver.refresh()
                # print("Error in getting the xray data")
                # print("Finishing up search for skip...")
                t.join()
        
        return add_meta


    def extract_xray_and_playbackresources(self, df, driver, SAVE_DIR):
        """
        Handler for each thread to extract resources

        Args:
            df (pandas.DataFrame): Dataframe containing the movie data
            driver (webdriver.Chrome): Associated webdriver
            SAVE_DIR (str): Directory to save the files in
        """
        self.sign_in(self.sign_in_url, driver)

        # create the save directory
        if not os.path.exists(f"{SAVE_DIR}/"): os.mkdir(f"{SAVE_DIR}/")
        meta_file = os.path.join(f"{SAVE_DIR}/", self.meta_file)

        for index, row in df.iterrows():
            # print current file
            print(f"\nCollecting data for: {index}, {row[self.fname_in_file]}\n")

            meta = {}
            meta['fname'] = row[self.fname_in_file]
            meta['link'] = row[self.link_in_file]
            meta['xray_present'] = None
            meta['playable'] = None
            meta['playback'] = None
            meta['xray'] = None
            meta['all_resource'] = False

            link = "https://www.amazon.com" + row[self.link_in_file]
            title = row[self.fname_in_file]
            driver.get(link)
            
            # print("Looking for Xray button")
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@aria-label='x-ray-badge']"))
                )
                meta['xray_present'] = True
            except TimeoutException:
                print(f"TimeoutException: X-Ray Tag not found on movie profile ({title}).")
                meta['xray_present'] = False

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "dv-dp-node-playback"))
                )
                meta['playable'] = "yes"
            except TimeoutException:
                print(f"TimeoutException: Play button not found {title}.")
                # Handle the exception as needed (e.g., log the error, take alternative actions, etc.)
                meta['playable'] = "no"
            
            # In any of these two cases, skip looking for the files
            if meta['xray_present'] == "no_tag" or meta['playable'] == "no":
                with self.lock:
                    pd.DataFrame(meta, index=[0]).to_csv(meta_file, mode='a', index=False, header=not os.path.exists(meta_file))
                
                # reset the requests for next movie
                del driver.requests
                continue
            
            # you can sometimes be interrupted by captcha checks in the middle at times
            # this will check for it, you'll have to manually resolve it then
            # after that, the new cookies will be saved
            self.check_captcha(driver)
            
            # create the directory for the movie
            dir_name = f"{SAVE_DIR}/" + unidecode(row[self.fname_in_file])

            try:
                # if the directory already exists, remove it (overwrite)
                if self.overwrite_old_movie_dirs and os.path.exists(dir_name):
                    shutil.rmtree(dir_name)
                # create directory for each movie
                os.mkdir(dir_name)
            except:
                print("Error in handling the directory")
            
            # Check for Free with ads on Freevee content
            is_freevee = False
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Free with ads on Freevee']"))
                )
                print("Freeve content")
                is_freevee = True
            except:
                is_freevee = False

            # get the resources
            add_meta = self.capture_resources(driver, dir_name, is_freevee)
            with self.lock:
                meta['playback'] = add_meta['playback']
                meta['xray'] = add_meta['xray']
                meta['all_resource'] = add_meta['all_resource']
                pd.DataFrame(meta, index=[0]).to_csv(meta_file, mode='a', index=False, header=not os.path.exists(meta_file))
            
            # reset the requests in each iteration
            del driver.requests
            
        print("Collection done for this chunk")

    # https://medium.com/geekculture/introduction-to-selenium-and-python-multi-threading-module-aa5b1c4386cb
    def run_workers(self, main_df, SAVE_DIR):
        """
        Runs the workers to collect the data.

        Args:
            main_df (pandas.DataFrame): Dataframe containing the movie data
            SAVE_DIR (str): Directory to save the files in
        """
        files = np.array_split(main_df, self.WORKERS)

        print("LOADING DRIVERS...")
        drivers = [self.get_driver() for _ in range(self.WORKERS)]

        with ThreadPoolExecutor(max_workers=self.WORKERS) as executor:
            handler = self.extract_xray_and_playbackresources
            executor.map(handler, files, drivers, [SAVE_DIR]*self.WORKERS)
        
        [driver.quit() for driver in drivers]
