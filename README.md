# Simple Flask web application with a scraper functionality

## **[Website URL](https://crimestoppers-uk-most-wanted.herokuapp.com/ "Website URL")**

## Description:
- Scraper created with Selenium Webdriver
- Uses MongoDB for database
- Main app uses Flask and Jinja2 to render the collected data in the website
- Deployed to Heroku cloud platform

### There are also two API endpoints created for POST requests to retrieve the collected data:
- /api/wanted-persons/ - To get data for all wanted persons
- /api/wanted-persons/search/ - To search for particular person

Sample request for '/api/wanted-persons/' endpoint:
```json
{
    "token": "<token>"
}
```

Sample request for '/api/wanted-persons/search/' endpoint:
```json
{
    "token": "<token>",
    "SOI": "<name>"
}
```
