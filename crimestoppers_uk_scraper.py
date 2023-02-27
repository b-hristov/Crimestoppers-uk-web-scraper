import os
import re
from datetime import datetime

from pymongo import MongoClient
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

# Connect to MongoDB
mongodb_uri = os.environ.get("MONGODB_URI")
client = MongoClient(mongodb_uri)
db = client["scraped_data"]
collection = db["wanted_persons"]

start_time = datetime.now()

options = Options()
options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')

service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://crimestoppers-uk.org/give-information/most-wanted")
actions = ActionChains(driver)

final_result = []

# Wait for cookies to appear and close them
try:
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "onetrust-accept-btn-handler"))).click()
except TimeoutException:
    pass

# Get the total number of pages with entries
all_pages = driver.find_elements(By.XPATH, '//li[contains(@class, "page-item")]')

progress_bar = tqdm(total=len(all_pages), desc='Scraping pages')


def load_list_items_into_dict(list_items):
    for el in list_items:
        key, value = el.split(":", 1)
        if value.strip() != "" and value.strip() != "N/A":
            all_info_for_person[key] = value.strip()


for page_index in range(len(all_pages)):
    # Get the elements in each iteration to avoid stale element exception
    all_pages = driver.find_elements(By.XPATH, '//li[contains(@class, "page-item")]')

    # Click on each element
    actions.move_to_element(all_pages[page_index]).perform()
    all_pages[page_index].click()

    # Get the total entries per page
    all_urls = driver.find_elements(By.XPATH, '//figure[1]/a[1]')

    for entry_index in range(len(all_urls)):
        # Create dict to store all scraped info
        all_info_for_person = {}

        # Click on each element
        try:
            all_urls = driver.find_elements(By.XPATH, '//figure[1]/a[1]')
            actions.move_to_element(all_urls[entry_index]).perform()
            all_urls[entry_index].click()
        except Exception:
            continue

        # Wait until elements are visible and start scraping them
        try:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "main")))
        except TimeoutException:
            continue

        try:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//figure[1]/img[1]")))
            image_url = driver.find_element(By.XPATH, "//figure[1]/img[1]").get_attribute('src')
            all_info_for_person["Photo URL"] = image_url
        except TimeoutException:
            pass

        all_content = driver.find_element(
            By.XPATH,
            "//body/div[@id='main']/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]"
        ).text

        list_of_intro_row_elements = [el.text for el in driver.find_elements(
            By.XPATH,
            "//body[1]/div[1]/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/ul[1]/li"
        )]

        list_of_description_elements = [el.text for el in driver.find_elements(
            By.XPATH,
            "//body[1]/div[1]/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]/ul[1]/li"
        )]

        load_list_items_into_dict(list_of_intro_row_elements)
        load_list_items_into_dict(list_of_description_elements)

        summary = re.search("Summary(.+?)Full Details", all_content, re.DOTALL).group(1)
        all_info_for_person["Summary"] = summary
        full_details = re.search("Full Details(.+?)Suspect description", all_content, re.DOTALL).group(1)
        all_info_for_person["Full Details"] = full_details

        # Handle the missing Additional information for some entries
        try:
            add_info = re.search("Additional Information(.+?)Recognise", all_content, re.DOTALL).group(1)
            if add_info:
                all_info_for_person["Additional Information"] = add_info
        except AttributeError:
            pass

        # Create dict with the name of the person as a key and append it to the final result
        person_data = {
            all_info_for_person["Suspect name"]: [all_info_for_person]
        }
        final_result.append(person_data)

        driver.back()

    progress_bar.update(1)
    driver.back()

progress_bar.close()
driver.quit()

# Load the data in MongoDB after the scraper finishes
collection.drop()
collection.insert_many(final_result)

end_time = datetime.now()
print(f'Execution time: {str(end_time - start_time).split(".")[0]}')
print(f'Collected entries:\n------------------\n{len(final_result)}')
