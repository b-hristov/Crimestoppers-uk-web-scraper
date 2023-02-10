import os
import subprocess
from math import ceil
from threading import Thread

import boto3
from flask import *
from pymongo import MongoClient

app = Flask(__name__, static_folder="static")

# Connect to MongoDB
mongodb_uri = os.environ.get("MONGODB_URI")
client = MongoClient(mongodb_uri)
db = client["scraped_data"]
collection = db["wanted-persons"]

# Connect to AWS S3
s3 = boto3.client("s3")
bucket = "scraped-data-most-wanted"
file_name = "scraped_data.json"

token_1 = os.environ.get("TOKEN_1")
token_2 = os.environ.get("TOKEN_2")
token_3 = os.environ.get("TOKEN_3")
token_4 = os.environ.get("TOKEN_4")
token_5 = os.environ.get("TOKEN_5")
AVAILABLE_TOKENS = [token_1, token_2, token_3, token_4, token_5]
ENTRIES_PER_PAGE = 10


@app.route('/', methods=['GET'])
def render_all_persons_data():
    all_documents_in_collection = collection.find({}, {'_id': 0})

    items = list(all_documents_in_collection)
    total_entries = len(items)
    print(f"Total documents in collection: {total_entries}")
    page = int(request.args.get('page', 1))
    pages = ceil(total_entries / ENTRIES_PER_PAGE)
    start = (page - 1) * ENTRIES_PER_PAGE
    end = start + ENTRIES_PER_PAGE
    json_data = items[start:end]
    return render_template('index.html', json_data=json_data, page=page, pages=pages, total_entries=total_entries)


@app.route('/<string:name>/', methods=['GET'])
def render_person_data(name):
    all_documents_in_collection = collection.find({}, {'_id': 0})
    for person in all_documents_in_collection:
        if name in person:
            return render_template('criminal.html', json_data=person[name])


@app.route('/api/wanted-persons/', methods=['POST'])
def get_all_persons_data():
    data = request.get_json()
    auth_token = data.get('token')

    if auth_token not in AVAILABLE_TOKENS:
        return {"Error": "Invalid authentication token!"}
    json_data = collection.find({}, {'_id': 0})
    items = list(json_data)
    return {"Count": len(items), "Entries": items}


@app.route('/api/wanted-persons/search/', methods=['POST'])
def search_for_person():
    data = request.get_json()
    auth_token = data.get('token')
    soi = data.get('SOI')
    json_data = collection.find({}, {'_id': 0})

    if auth_token not in AVAILABLE_TOKENS:
        return {"Error": "Invalid authentication token!"}

    results = []
    for person in json_data:
        # Convert names to lowercase to optimize the search
        converted_name = [k.lower() for k in person.keys()][0]
        if soi.lower() in converted_name:
            results.append(person)

    if results:
        return {"Entries found": results}
    return {"Message": "SOI not found!"}


scraping_in_progress = False


def run_scraper():
    global scraping_in_progress
    scraping_in_progress = True
    subprocess.run(['python', 'crimestoppers_uk_scraper.py'])

    obj = s3.get_object(Bucket=bucket, Key=file_name)
    file_content = obj["Body"].read().decode("utf-8")
    wanted_persons = json.loads(file_content)

    # Delete old data in collection and insert the new one
    collection.drop()
    collection.insert_many(wanted_persons)

    scraping_in_progress = False


@app.route("/run_scraper/", methods=["POST"])
def start_scraping():
    Thread(target=run_scraper).start()
    return "Scraping started."


@app.route("/check_scraper_status/", methods=["GET"])
def check_scraper_status():
    return jsonify({"scraping_in_progress": scraping_in_progress})


@app.route('/erase_all_entries/', methods=['POST'])
def erase_all_entries():
    collection.drop()
    return "Successfully deleted all entries."


if __name__ == "__main__":
    port = os.environ.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)
