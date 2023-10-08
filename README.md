# Simple Flask web application with a scraper functionality

## Description:
- Scraper created with Playwright
- Uses MongoDB for database
- Main app uses Flask and Jinja2 to render the collected data in the website
- Deployed to Heroku cloud platform

### There are also two API endpoints created for POST requests to retrieve the collected data:

- **/api/wanted-persons/** - To get data for all wanted persons

Sample request:
```json
{
    "token": "<token>"
}
```

Sample response:
```json
{
    "Count": 2,
    "Entries": [
        {
            "Jon Smith": [
                {
                    "Age": "30 - 35",
                    "Crime location": "England",
                    "Crime type": "Trafficking in Controlled Drugs",
                    "Full Details": "Alleged to be a regional distributor of drugs across the south west of England",
                    "Height": "180 - 185 cm",
                    "Photo URL": "https://website.com/photo.jpg",
                    "Sex": "Male",
                    "Summary": "Wanted for supply of class A drugs",
                }
            ]
        },
        {
            "George Davis": [
                {
                    "Age": "25 - 30",
                    "Crime location": "Scotland",
                    "Crime type": "Fraud",
                    "Full Details": "Suspected of running an online phishing scam that defrauded thousands of people out of their personal information",
                    "Height": "165 - 170 cm",
                    "Photo URL": "https://website.com/photo.jpg",
                    "Sex": "Male",
                    "Summary": "Wanted for identity theft and fraud",
                }
            ]
        }
    ]
}
```
------------

- **/api/wanted-persons/search/** - To search for particular person

Sample request:
```json
{
    "token": "<token>",
    "name": "<name>"
}
```

Sample response:
```json
{
    "Entries found": [
        {
            "Jon Smith": [
                {
                    "Age": "30 - 35",
                    "Crime location": "England",
                    "Crime type": "Trafficking in Controlled Drugs",
                    "Full Details": "Alleged to be a regional distributor of drugs across the south west of England",
                    "Height": "180 - 185 cm",
                    "Photo URL": "https://website.com/photo.jpg",
                    "Sex": "Male",
                    "Summary": "Wanted for supply of class A drugs",
                }
            ]
        }
    ]
}
```
