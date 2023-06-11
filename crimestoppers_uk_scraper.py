import os
import re
from datetime import datetime

from pymongo import MongoClient
from selenium import webdriver
from selenium.common import TimeoutException
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
print("Getting the total amount of entries to scrape, please wait...")

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

final_result = []

# Wait for cookies to appear and close them
try:
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "onetrust-accept-btn-handler"))).click()
except TimeoutException:
    pass

# Get the total number of pages with entries
all_pages_list = driver.find_elements(By.XPATH, '//li[contains(@class, "page-item")]')

all_entries_urls = []


def get_all_entries_urls(pages):
    # Get the elements in each iteration to avoid stale element exception
    for page_index in range(len(pages)):
        pages = driver.find_elements(By.XPATH, '//li[contains(@class, "page-item")]')
        # Click on each page item
        pages[page_index].click()
        entries_on_page = driver.find_elements(
            By.XPATH,
            '//body/form[1]/div[1]/main[1]/article[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/a[1]'
        )
        all_entries_urls.extend([(el.get_attribute("href")) for el in entries_on_page])


get_all_entries_urls(all_pages_list)

progress_bar = tqdm(total=len(all_entries_urls), desc='Scraping entries')


def start_scraping(url):
    driver.get(url)
    person_data = {}

    def load_list_items_into_dict(list_items):
        for el in list_items:
            key, value = el.split(":", 1)
            if value.strip() == "" or value.strip() == "N/A":
                person_data[key] = "Unknown"
            else:
                person_data[key] = value.strip()

    # Wait until the main content of the page is loaded
    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "main")))
    except TimeoutException:
        return None

    # Wait until the photo is loaded
    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//figure[1]/img[1]")))
        image_url = driver.find_element(By.XPATH, "//figure[1]/img[1]").get_attribute('src')
        person_data["Photo URL"] = image_url
    except TimeoutException:
        pass

    all_content = driver.find_element(
        By.XPATH,
        "//body/div[@id='main']/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]"
    ).text

    intro_row_elements = [el.text for el in driver.find_elements(
        By.XPATH,
        "//body[1]/div[1]/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/ul[1]/li"
    )]

    description_elements = [el.text for el in driver.find_elements(
        By.XPATH,
        "//body[1]/div[1]/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]/ul[1]/li"
    )]

    load_list_items_into_dict(intro_row_elements)
    load_list_items_into_dict(description_elements)

    summary = re.search("Summary(.+?)Full Details", all_content, re.DOTALL).group(1)
    person_data["Summary"] = summary.strip()
    full_details = re.search("Full Details(.+?)Suspect description", all_content, re.DOTALL).group(1)
    person_data["Full Details"] = full_details.strip()

    # Handle the missing Additional information for some entries
    try:
        add_info = re.search("Additional Information(.+?)Recognise", all_content, re.DOTALL).group(1)
        person_data["Additional Information"] = add_info.strip()
    except AttributeError:
        pass

    # Check if there are forward slashes in the name
    if "/" in person_data["Suspect name"]:
        person_data["Suspect name"] = person_data.get("Suspect name").replace("/", "-")

    # Create dict with the name of the person as a key and append it to the final result
    person_data = {
        person_data["Suspect name"]: person_data
    }

    final_result.append(person_data)
    progress_bar.update(1)


for url in all_entries_urls:
    start_scraping(url)

# Load the data in MongoDB after the scraper finishes
collection.drop()
collection.insert_many(final_result)

end_time = datetime.now()
print(f'Execution time: {str(end_time - start_time).split(".")[0]}')
print(f'Collected entries:\n------------------\n{len(final_result)}')
