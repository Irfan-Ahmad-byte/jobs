# Import FastAPI and requests libraries
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from woocommerce import API
from docsim import rate_text
from itertools import repeat
import os
import requests
import json
import re
import time
import random

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

class JobsParams(BaseModel):
    page: int

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
    "https://irfan-ahmad.com",
    'http://comomaquinasaprendem.xyz'
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


def get_job_info(card, plavras):

  # Get the text content and href attribute of the title link element
  jobTitle = card.find("h3", class_="base-search-card__title").text.strip()
  jobURL = card.find("a")['href']
  
  with open('urls.txt', 'a') as fl:
    fl.write('\n'+jobURL)
  jobDesc = extractDescription(jobURL)
      
  print(jobTitle, ' ', jobURL, ' ', )
  
  # Get the text content of the company link element
  try:
    companyName = card.find("h4", class_="base-search-card__subtitle").text.strip()
  except:
    companyName = False

  # Get the text content of the date span element
  try:
    dayPosted = card.find("time").text.strip()
  except:
    dayPosted = False
    
  rating = rate_job(jobDesc['description'], plavras)
        

      # Create a dictionary with all these information and append it to results list 
  return {
          "jobTitle": jobTitle,
          "companyName": companyName,
          "dayPosted": dayPosted,
           "jobURL": jobURL,
           'rating': rating,
          'location': jobDesc['location'],
          'jobDesc': jobDesc['description']
      }
    
    
def extractJobs(url, plavras, page=1):

  logging.info('Getting jobs from %s', url)

  # Create an empty list to store the results
  results = []

  # Fetch the HTML content from the URL using requests library (or any other method)
  try:
    res = requests.get(url)
    time.sleep(1)
    html = res.text    

    # Parse the HTML content using BeautifulSoup library (or any other method)
    soup = BeautifulSoup(html, "html.parser")

    # Find all the elements with class name 'base-card' which contain each job listing
    cards = soup.find('ul', class_="jobs-search__results-list").find_all('li')
    total_cards = len(cards)
    
    #  select cards to display on the selected page
    start_index = (page*13)-13	# starting index of cards for current page
    
    cards = cards[start_index:page*13]
    
    print('Cards: =========', len(cards))
    

    # Loop through each card element and extract the relevant information
    #results = [get_job_info(card, plavras) for card in cards]
    with ThreadPoolExecutor(max_workers=5) as executor:
      job_data = executor.map(get_job_info, cards, repeat(plavras))
      
    job_data_list = list(job_data)
    
    for job in job_data_list:
      results.append(job)
        
  
  except Exception as e:
    logging.error('Error while getting jobs: %s', str(e))

  logging.info('Finished getting jobs from %s', url)
  # Return results list 
  return [results, total_cards]
  
def extractDescription(url):

  # Create an empty dictionary to store the result
  result = {}

  # Fetch the HTML content from the URL using requests library (or any other method)
  logging.info('Getting job description from %s', url)
  try:
    time.sleep(random.uniform(0.5, 3))
    res = requests.get(url)
    time.sleep(random.uniform(0.5, 3))
    html = res.text

    # Parse the HTML content using BeautifulSoup library (or any other method)
    soup = BeautifulSoup(html, "html.parser")
    
    # Find the element with class name 'description__text' which contains the job's description
    descriptionDiv = soup.find("div", class_="show-more-less-html__markup")
    
    locationDiv = soup.find("h4", class_="top-card-layout__second-subline")
    if locationDiv is not None:
      try:
        location = locationDiv.find_all("span", class_="topcard__flavor")[1].text.strip()
        result["location"] = location
      except:
        result["location"] = None
    else:
      result["location"] = None
      
    # Call the parseDescription function on this element and get the result dictionary
    
    time.sleep(0.5)
    # Get the text content of the element
    if descriptionDiv is not None:
      description = descriptionDiv.text.strip()
    else:
      description = 'no description specified'
      
    print('descr =*=*=*=*=*=*=>:  ')

    # Add the complete description to result dictionary 
    result["description"] = description

  except Exception as e:
    print('Error while getting job description: %s, %s', str(e), url)

  print('Finished getting job description from %s', url)

  # Return result dictionary 
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
def get_jobs(request: Request):
  
#  id = params.id
#  user = search_customer(id)
  page = request.get('page')

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

  url = f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}{time_period}&position=1&pageNum=0"

  print('REQUESTED URI: ', url)
  return JSONResponse(content=extractJobs(url, plavra, 1))


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
    ress = extractJobs('https://www.linkedin.com/jobs/search?keywords=Engenharia%20Ambiental&location=Brazil&f_TPR=r86400&position=1&pageNum=0', plavra)

    logging.info('Results: %s', len(ress[0]))
  except Exception as e:
    logging.error('Error while running the application: %s', str(e))

  logging.info('Finished running the application')
  
