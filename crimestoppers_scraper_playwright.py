import os
from datetime import datetime

from playwright.sync_api import sync_playwright
from pymongo import MongoClient
from tqdm import tqdm
import re
from time import sleep

# Connect to MongoDB
mongodb_uri = os.environ.get("MONGODB_URI")
client = MongoClient(mongodb_uri)
db = client["scraped_data"]
collection = db["wanted_persons"]

start_time = datetime.now()
print("Getting the total amount of entries to scrape, please wait...")

final_result = []

with sync_playwright() as p:

    # Scraping with open browser and watching the process in real time:
    # browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    # context = browser.new_context(no_viewport=True)

    # Scraping in headless mode:
    browser = p.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://crimestoppers-uk.org/give-information/most-wanted")

    # Wait for cookies to appear and close them
    try:
        page.wait_for_selector("#onetrust-accept-btn-handler")
        accept_button = page.query_selector("#onetrust-accept-btn-handler")
        accept_button.click()
    except Exception:
        pass

    # Get the total number of pages with entries
    all_pages_list = page.query_selector_all('//li[contains(@class, "page-item")]')

    all_entries_urls = []


    def get_all_entries_urls(pages):
        # Iterate through all the pages with entries and collect URLs
        sleep(3)
        for page_index in range(len(pages)):
            pages = page.query_selector_all('//li[contains(@class, "page-item")]')
            pages[page_index].click()
            entries_on_page = page.query_selector_all(
                '//body/form[1]/div[1]/main[1]/article[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/a[1]'
            )
            all_entries_urls.extend([el.get_attribute("href") for el in entries_on_page])


    get_all_entries_urls(all_pages_list)

    progress_bar = tqdm(total=len(all_entries_urls), desc='Scraping entries')


    def start_scraping(url):
        # Open each URL and collect the necessary data
        page.goto(f"https://crimestoppers-uk.org" + url)
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
            page.wait_for_selector("#main", state='visible', timeout=5000)
        except Exception:
            return None

        # Wait until the photo is loaded
        try:
            page.wait_for_selector("//figure[1]/img[1]", state='visible', timeout=5000)
            image_url = page.locator("//figure[1]/img[1]").get_attribute('src')
            person_data["Photo URL"] = image_url
        except Exception:
            pass

        person_data["Page URL"] = url

        all_content = page.locator(
            "//body/div[@id='main']/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]"
        ).inner_text()

        intro_row_elements = [el.inner_text() for el in page.query_selector_all(
            "//body[1]/div[1]/main[1]/article[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/ul[1]/li"
        )]

        description_elements = [el.inner_text() for el in page.query_selector_all(
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

        # Check if there are forward slashes in the name and replace them
        if "/" in person_data["Suspect name"]:
            person_data["Suspect name"] = person_data.get("Suspect name").replace("/", "-")

        person_data = {
            person_data["Suspect name"]: person_data
        }

        final_result.append(person_data)
        progress_bar.update(1)


    for url in all_entries_urls:
        start_scraping(url)

    progress_bar.close()
    browser.close()


# Load the data in MongoDB after the scraper finishes
collection.drop()
collection.insert_many(final_result)

end_time = datetime.now()
print(f'Execution time: {str(end_time - start_time).split(".")[0]}')
print(f'Collected entries:\n------------------\n{len(final_result)}')
