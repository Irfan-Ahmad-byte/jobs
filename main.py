"""
This API module is designed to fetch, process, and rate job postings from LinkedIn. It uses FastAPI to provide an endpoint for getting jobs with specific titles, keywords, and location parameters. The API also utilizes the `rate_text` function from the `docsim.py` module to rate job postings based on the relevance of their descriptions to the provided keywords.

Developer: Irfan Ahmad (devirfan.mlka@gmail.com / https://irfan-ahmad.com)
Project Owner: Monica Piccinini (monicapiccinini12@gmail.com)

The module contains the following functions:
    - get_job_info: Extracts relevant information from a job card.
    - get_job_cards: Fetches job cards from a LinkedIn URL.
    - extractJobs: Fetches job listings from LinkedIn based on the provided URLs and keywords.
    - extractDescription: Extracts job description and location from a LinkedIn job posting URL.
    - rate_job: Rates a job based on its description and a list of keywords (plavras).
    - search_customer: Searches for a customer by ID and returns relevant customer information.
    - create_time_param: Converts a time period string into a LinkedIn time parameter.

The module also defines the following FastAPI endpoints:
    - /jobs: Accepts a POST request with job titles, keywords, time period, and location, and returns the relevant job listings.
    - /description: Accepts a GET request with a job posting URL as a query parameter, and returns the job description and location.
"""



# Import FastAPI and requests libraries
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from bs4 import BeautifulSoup
from typing import Optional, List, Union

from woocommerce import API

from module.docsim import rate_text, normalize_text

from module.jobs99 import Jobs99
from module.linkedin import LinkedIn

from itertools import repeat
from math import sqrt

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread

import os
import requests
import json
import re
import time
import random
import logging
import unicodedata
import urllib
import random


# Set up logging
logging.basicConfig(level=logging.INFO)

class JobsParams(BaseModel):
    titles: List[str]
    plavra: Union[List[str], bool]
    time_period: str
    location: str

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
    '*'
]

#from new_sendemail import send_email

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Content-Type"],
)



url1 = 'https://www.linkedin.com/jobs/search?keywords=vue-developer'

url2 = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=software-engineer&start=225'

# A function that takes a URL for LinkedIn jobs search and returns a list of dictionaries containing job title, company name, day posted and URL of the job

LOCATION = 'Brazil'


def execute_constructor(constructor):
    jobs = constructor.main()
    return jobs


def extractJobs(urls:list, plavras:list, timeout_event: Event):
  """
    Extracts job information from a list of LinkedIn job search URLs and a list of keywords (plavras).
    
    Args:
        urls (List[str]): A list of LinkedIn job search URLs.
        plavras (List[str]): A list of keywords to rate the jobs.
    
    Returns:
        Tuple[List[dict], int]: A tuple containing a list of job dictionaries and the total number of cards.
  """
  # separate job URLS
  sites = {}
  sites['99jobs'] = []
  sites['linkedin'] = []
  
  for url in urls:
    if '99jobs' in url:
      sites['99jobs'].append(url)
    elif 'linkedin' in url:
      sites['linkedin'].append(url)
      
  jobs = []
  
  constructors = []
  
  for key, value in sites.items():
    if key == '99jobs':
      constructors.append(Jobs99(value, plavras, timeout_event))
    elif key == 'linkedin':
      constructors.append(LinkedIn(value, plavras, timeout_event))
      
  totla_jobs = 0
  job_data_list = []
  with ThreadPoolExecutor(max_workers=10) as executor:
    job_data = executor.map(execute_constructor, constructors)
    
    job_data_list= list(job_data)
    
  for jb in job_data_list:
    totla_jobs+= jb[1]
    jobs.extend(jb[0])
    
  random.shuffle(jobs)
  return [jobs, totla_jobs]
  
   
#@app.post("/search_customer/")
def search_customer(id):
    """
    Searches for a customer by ID and returns relevant customer information.
    
    Args:
        id (int): The customer ID.
    
    Returns:
        dict: A dictionary containing the customer's ID, job title, keywords (plavras), and location.
    """
    
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
    
def create_time_param(time):
  """
    Converts a time period string into a LinkedIn time parameter.
    
    Args:
        time (str): A string representing a time period (e.g., "past 24 hours", "past week", "past month", or "any time").
    
    Returns:
        str: A LinkedIn time parameter string.
  """
  
  if time == "past 24 hours":
    TPeriod = "&f_TPR=r86400"
  
  elif time == "past week":
    TPeriod = "&f_TPR=r604800";
  
  elif time== "past month":
    TPeriod = "&f_TPR=r2592000";
  
  elif time == "any time":
      TPeriod = None
      
  return TPeriod


# Define a GET endpoint that takes a query parameter 'url' and returns the result of extractJobs function
@app.post("/jobs")
def get_jobs(user_params: JobsParams):
    """
    FastAPI endpoint that accepts a JobsParams object containing user search parameters.
    Returns the result of the extractJobs function as a JSON response.
    
    Args:
        user_params (JobsParams): A Pydantic model containing user search parameters.
    
    Returns:
        fastapi.responses.JSONResponse: A JSON response containing a list of job dictionaries and the total number of cards.
    """

    titles = user_params.titles
    plavra = user_params.plavra
    time_period = user_params.time_period
    location = user_params.location

    time_period = create_time_param(time_period)

    # Split location into city, state, and country
    location_parts = location.split(', ')
    city = state = None
    country = location_parts[-1]
    if len(location_parts) >= 2:
        state = location_parts[-2]
    if len(location_parts) >= 3:
        city = location_parts[-3]

    location = location.replace(" ", "%20").replace(",", "%2C")

    urls = []

    for title in titles:
        keywords = urllib.parse.quote(title)
        keywords_99jobs = urllib.parse.quote(title)

        # LinkedIn URL
        linkedin_link = f'https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}'
        if time_period:
            linkedin_link += time_period
        linkedin_link += '&position=1&pageNum=0'
        urls.append(linkedin_link)

        # 99jobs URL
        _99jobs_link = f'https://99jobs.com/opportunities/filtered_search?utf8=%E2%9C%93&utm_source=tagportal&utm_medium=busca&utm_campaign=home&utm_id=001&search%5Bterm%5D={keywords_99jobs}'
        if state:
            state_99jobs = urllib.parse.quote(state)
            _99jobs_link += f'&search%5Bstate%5D={state_99jobs}'
        if city:
            city_99jobs = urllib.parse.quote(city)
            _99jobs_link += f'&search%5Bcity%5D%5B%5D={city_99jobs}'
        urls.append(_99jobs_link)
        
    timeout_event = Event()

    # Start the timeout thread before calling the extractJobs function
    def stop_extraction():
        time.sleep(90)
        timeout_event.set()

    extraction_thread = threading.Thread(target=stop_extraction)
    extraction_thread.start()

    result = extractJobs(urls, plavra, timeout_event)

    print('REQUESTED URIs: ', urls)
    return JSONResponse(content=result)


# Define a GET endpoint that takes a query parameter 'url' and returns the result of extractJobs function
@app.get("/")
def display_jobs():
  
  ress = {
      'Hello World': 'Hello World, welcome to Jobs API.'
  }

  return JSONResponse(content=ress)
  
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
    start_time = time.time()
    url_list = [
        'https://99jobs.com/opportunities/filtered_search?utf8=%E2%9C%93&utm_source=tagportal&utm_medium=busca&utm_campaign=home&utm_id=001&search%5Bterm%5D=Engenharia',
        'https://www.linkedin.com/jobs/search?keywords=Engenharia%20Ambiental&location=Brazil&f_TPR=r86400&position=1&pageNum=0',
        'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=software-engineer&start=225&location=Brazil',
        
    ]

    timeout_event = Event()
    # Start the timeout thread before calling the extractJobs function
    def stop_extraction():
        time.sleep(90)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    ress = extractJobs(url_list, plavra, timeout_event)
    
    elapsed_time = time.time() - start_time
    
    print(json.dumps(ress, indent=2))
    print(f"Time taken to extract job description: {elapsed_time:.2f} seconds")
  except Exception as e:
    logging.error('Error while running the application: %s', str(e))
  
