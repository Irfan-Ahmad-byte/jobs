# Import FastAPI and requests libraries
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from typing import Optional
from woocommerce import API
from docsim import rate_text
import os
import requests
import json
import re

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

class JobsParams(BaseModel):
    id: int
    time_period: Optional[str] = False

'''
wcapi = API(
    url="https://your_website_url",  # Replace with your website URL
    consumer_key=os.environ['WOO_CONSUMER_KEY'],  # Replace with your consumer key
    consumer_secret=os.environ['WOO_CONSUMER_SECRET'],  # Replace with your consumer secret
    version="wc/v3"
)
'''

class CustomerSearch(BaseModel):
    username: str
    id: int

origins = [
    "http://localhost:8080",
    "https://irfan-ahmad.com"
]

#from new_sendemail import send_email

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



url1 = 'https://www.linkedin.com/jobs/search?keywords=vue-developer'

url2 = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=software-engineer&start=225'

# A function that takes a URL for LinkedIn jobs search and returns a list of dictionaries containing job title, company name, day posted and URL of the job

LOCATION = 'Brazil'

def extractJobs(url, plavras):

  logging.info('Getting jobs from %s', url)

  # Create an empty list to store the results
  results = []

  # Fetch the HTML content from the URL using requests library (or any other method)
  try:
    res = requests.get(url)
    html = res.text

    # Parse the HTML content using BeautifulSoup library (or any other method)
    soup = BeautifulSoup(html, "html.parser")

    # Find all the elements with class name 'base-card' which contain each job listing
    cards = soup.find_all("div", class_="base-card")
    
    print('Cards: =========', len(cards))
    
    tries = 1
    
    if len(cards) > 0:

      # Loop through each card element and extract the relevant information
      for card in cards:
      
        # Get the text content and href attribute of the title link element
        jobTitle = card.find("h3", class_="base-search-card__title").text.strip()
        jobURL = card.find("a", class_="base-card__full-link").get("href")
        jobDesc = extractDescription(jobURL)
        rating = rate_job(jobDesc['description'], plavras)
        
        print(jobTitle, ' ', jobURL, ' ', )
  
        # Get the text content of the company link element
        try:
          companyName = card.find("h4", class_="base-search-card__subtitle").text.strip()
        except:
          companyName = False
  
        # Get the text content of the date span element
        try:
          dayPosted = card.find("time", class_="job-search-card__listdate").text.strip()
        except:
          dayPosted = False
          
  
        # Create a dictionary with all these information and append it to results list 
        results.append({
          "jobTitle": jobTitle,
          "companyName": companyName,
          "dayPosted": dayPosted,
           "jobURL": jobURL,
          'location': jobDesc['location'],
          'jobDesc': jobDesc['description'],
          'rating': rating,
          'keywords': jobDesc['keywords']
        })
      
        
  
  except Exception as e:
    logging.error('Error while getting jobs: %s', str(e))

  logging.info('Finished getting jobs from %s', url)
  # Return results list 
  return results
  
def extractDescription(url):

  # Create an empty dictionary to store the result
  result = {}

  # Fetch the HTML content from the URL using requests library (or any other method)
  logging.info('Getting job description from %s', url)
  try:
    res = requests.get(url)
    html = res.text

    # Parse the HTML content using BeautifulSoup library (or any other method)
    soup = BeautifulSoup(html, "html.parser")

    # Find the element with class name 'description__text' which contains the job's description
    descriptionDiv = soup.find("div", class_="description__text")
    
    locationDiv = soup.find("h4", class_="top-card-layout__second-subline")
    if locationDiv is not None:
      location = locationDiv.find("span", class_="topcard__flavor").text.strip()
      result["location"] = location
    else:
      result["location"] = None
      
    # Call the parseDescription function on this element and get the result dictionary
    
    result.update(parseDescription(descriptionDiv))

  except Exception as e:
    logging.error('Error while getting job description: %s', str(e))

  logging.info('Finished getting job description from %s', url)

  # Return result dictionary 
  return result



def parseDescription(element):

  # Create an empty dictionary to store the result
  result = {}

  # Get the text content of the element
  description = re.sub('\\\n', '', element.text.strip())
  print('descr =*=*=*=*=*=*=>:  ')

  # Add the complete description to result dictionary 
  result["description"] = description

  # Find all the strong elements which contain the headings of each section
  headings = element.find_all("strong")

  # Loop through each heading element and extract the relevant information
  for heading in headings:
    # Get the text content of the heading element
    key = heading.text.strip()

    # Get the next sibling element which contains the content of each section
    content = heading.next_sibling

    # Get the text content or inner HTML of the content element depending on its tag name
    value = ""
    if content.name:
      if content.name == "p":
        value = content.text.strip()
      elif content.name == "ul":
        value = content.decode_contents().strip()

    # Add each section as a key-value pair to result dictionary 
    result[key] = value

  # Find all the li elements which contain each keyword
  items = element.find_all("li")

  # Create an empty list to store keywords
  keywords = []

  # Loop through each item element and extract the relevant information
  for item in items:
    # Get the text content of the item element
    keyword = item.text.strip()

    # Append it to keywords list 
    keywords.append(keyword)
    
  # Add keywords to result dictionary 
  result["keywords"] = keywords;

  # Return result dictionary as a JSON string 
  return result
   
   
def rate_job(job_description, plavras=False):
    
    print('Now rating jobs:/*/*/*/*/')
    rating = 0

    # Check if there are any plavras for the user
    if not plavras:
        return rating
        
    rating = rate_text(plavras, job_description)

    return round(rating, 2)


   
#@app.post("/search_customer/")
def search_customer(id):
    customer_id = id

    # Fetch the customer data from the WooCommerce API
    customer = wcapi.get(f"customers/{customer_id}").json()

    # Check if the customer data is valid
    if "code" in customer:
        return {"error": "Customer not found"}

    # Extract metadata
    meta_data = customer.get('meta_data', {})

    job_title = 'Engenharia Ambiental'
    location = 'Brazil'
    plavras = []

    for meta in meta_data:
        if meta['key'] == 'jobTitle':
            job_title = meta['value']
        elif meta['key'] == 'plavras':
            plavras = meta['value']
        elif meta['key'] == 'location':
            location = meta['value']

    return {
        "id": customer_id,
	"jobTitle": job_title,
	"plavras": plavras,
	'location': location,
	}
    

# Define a GET endpoint that takes a query parameter 'url' and returns the result of extractJobs function
@app.get("/jobs")
def get_jobs():
  
#  id = params.id
#  user = search_customer(id)

#  keywords = user['jobTitle'].replace(" ", "%20")
#  keywords = user['jobTitle'].replace(",", "%2C")
  keywords = 'Engenharia%20Ambiental'
#  location = user['location'].replace(" ", "%20")
#  location = user['location'].replace(",", "%2C")
  location = 'Brazil'
#  time_period = '&'+params.time_period if params.time_period else ''
  time_period = '&f_TPR=r86400'
  
#  plavra = user['plavras']
  plavra = [
  	'manter registros',
	'projeto',
	'arquivos',
	'arquivos de programas',
	'computador',
	'registrar dados',
	'avaliar',
	'anomalias',
	'revisar documentos',
	'garantir',
	'compartilhamento de tempo',
	'levantar',
	'rapidez',
	'espanhol'
	]

  url = f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}{time_period}"

  print('REQUESTED URI: ', url)
  return JSONResponse(content=extractJobs(url, plavra))


# Define a GET endpoint that takes a query parameter 'url' and returns the result of extractJobs function
@app.get("/description")
def get_jobs(request: Request):
  return JSONResponse(content=extractDescription(request.query_params.get('url', None)))
  
  
if __name__ == "__main__":
  plavra = [
  	'manter registros',
	'projeto',
	'arquivos',
	'arquivos de programas',
	'computador',
	'registrar dados',
	'avaliar',
	'anomalias',
	'revisar documentos',
	'garantir',
	'compartilhamento de tempo',
	'levantar',
	'rapidez',
	'espanhol'
	]
  try:
    ress = extractJobs('https://www.linkedin.com/jobs/search?keywords=Engenharia%20Ambiental&location=Brazil&f_TPR=r86400', plavra)

    logging.info('Results: %s', ress)
  except Exception as e:
    logging.error('Error while running the application: %s', str(e))

  logging.info('Finished running the application')
  
