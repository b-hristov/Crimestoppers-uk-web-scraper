import os
import subprocess
from datetime import datetime
from math import ceil
from threading import Thread

from flask import *
from pymongo import MongoClient

app = Flask(__name__, static_folder="static")

# Connect to MongoDB and set collections
mongodb_uri = os.environ.get("MONGODB_URI")
client = MongoClient(mongodb_uri)
db = client["scraped_data"]
collection = db["wanted_persons"]

global_vars_collection = db["globals"]
global_vars = {"scraper_in_progress": False, "last_update_message": ""}
if not global_vars_collection.find_one({}):
    global_vars_collection.insert_one(global_vars)

# Access tokens for the API
token_1 = os.environ.get("TOKEN_1")
token_2 = os.environ.get("TOKEN_2")
token_3 = os.environ.get("TOKEN_3")
token_4 = os.environ.get("TOKEN_4")
token_5 = os.environ.get("TOKEN_5")
AVAILABLE_TOKENS = [token_1, token_2, token_3, token_4, token_5]
ENTRIES_PER_PAGE = 10


@app.route('/', methods=['GET'])
def render_all_persons_data():
    scraper_in_progress = global_vars_collection.find_one({})["scraper_in_progress"]
    last_update_message = global_vars_collection.find_one({})["last_update_message"]
    all_entries_in_db = collection.find({}, {'_id': 0})

    items = list(all_entries_in_db)
    total_entries = len(items)
    print(f"Total entries: {total_entries}")
    page = int(request.args.get('page', 1))
    pages = ceil(total_entries / ENTRIES_PER_PAGE)
    start = (page - 1) * ENTRIES_PER_PAGE
    end = start + ENTRIES_PER_PAGE
    json_data = items[start:end]
    return render_template(
        'index.html',
        json_data=json_data,
        page=page,
        pages=pages,
        total_entries=total_entries,
        last_update_message=last_update_message,
        scraper_in_progress=scraper_in_progress
    )


@app.route('/<string:name>/', methods=['GET'])
def render_person_data(name):
    query = {f"{name}.Suspect name": name}
    person_info = collection.find_one(query)
    return render_template('criminal.html', json_data=person_info[name])


@app.route('/api/wanted-persons/', methods=['POST'])
def get_all_persons_data():
    data = request.get_json()
    auth_token = data.get('token')

    if auth_token not in AVAILABLE_TOKENS:
        return {"Error": "Invalid authentication token!"}, 401

    json_data = collection.find({}, {'_id': 0})
    items = list(json_data)
    if not items:
        return {"Message": "No wanted persons found!"}, 200
    return {"Count": len(items), "Entries": items}, 200


@app.route('/api/wanted-persons/search/', methods=['POST'])
def search_for_person():
    data = request.get_json()
    auth_token = data.get('token')
    subject_of_inquiry = data.get('name')
    json_data = collection.find({}, {'_id': 0})

    if len(data) <= 1:
        return {"Error": "Missing required parameters!"}, 400
    if auth_token not in AVAILABLE_TOKENS:
        return {"Error": "Invalid authentication token!"}, 401
    if not subject_of_inquiry:
        return {"Error": f"Incorrect parameter '{list(data.keys())[1]}'!"}, 400

    results = []
    for person in json_data:
        # Convert names to lowercase for a broader search
        converted_name = [k.lower() for k in person.keys()][0]
        if subject_of_inquiry.lower() in converted_name:
            results.append(person)

    if results:
        return {"Entries found": results}
    return {"Message": "Subject of inquiry not found!"}, 200


def run_scraper():
    # Scraping started
    global_vars_collection.update_one({}, {"$set": {"scraper_in_progress": True}})
    subprocess.run(['python', 'crimestoppers_uk_scraper.py'])

    # Scraping finished
    global_vars_collection.update_one({}, {"$set": {"scraper_in_progress": False}})
    date_and_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    global_vars_collection.update_one({}, {"$set": {"last_update_message": f"Last update: {date_and_time} (UTC+2)"}})


@app.route("/run_scraper/", methods=["POST"])
def start_scraping():
    Thread(target=run_scraper).start()
    return "Scraping started.", 200


@app.route("/check_scraper_status/", methods=["GET"])
def check_scraper_status():
    scraper_in_progress = global_vars_collection.find_one({})["scraper_in_progress"]
    return jsonify({"scraping_in_progress": scraper_in_progress}), 200


@app.route('/erase_all_entries/', methods=['POST'])
def erase_all_entries():
    collection.drop()
    return "Successfully deleted all entries.", 200


if __name__ == "__main__":
    port = os.environ.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)
