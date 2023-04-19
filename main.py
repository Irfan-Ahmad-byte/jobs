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
from docsim import rate_text
from itertools import repeat
from math import sqrt

import concurrent.futures
import os
import requests
import json
import re
import time
import random
import logging
import unicodedata


requests.adapters.DEFAULT_RETRIES = 3
headers = {'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'}
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


def normalize_text(text):
    return unicodedata.normalize('NFC', text)
    

def get_job_info(card, plavras):
  """
    Extracts job information from a BeautifulSoup card object and a list of keywords (plavras).
    
    Args:
        card (bs4.element.Tag): A BeautifulSoup object representing a single job card.
        plavras (List[str]): A list of keywords to rate the job.
    
    Returns:
        dict: A dictionary containing job title, company name, day posted, job URL, rating, location, and job description.
  """
  
  # Get the text content and href attribute of the title link element
  jobTitle = card.find("h3", class_="base-search-card__title").text.strip()
  jobURL = card.find("a")['href']
  try:
    location = card.find("span", class_='job-search-card__location').text.strip()
  except:
    location = 'location not given'

  #jobDesc = extractDescription(jobURL)
  
  # Get the text content of the company link element
  try:
    companyName = card.find("h4", class_="base-search-card__subtitle").text.strip()
  except:
    companyName = 'Not specified'

  # Get the text content of the date span element
  try:
    dayPosted = card.find("time").text.strip()
  except:
    dayPosted = False
    
  jobDesc = extractDescription(jobURL)
  rating = rate_job(normalize_text(jobDesc['description']), plavras)
        

      # Create a dictionary with all these information and append it to results list 
  return {
          "jobTitle": jobTitle,
          "companyName": companyName,
          "dayPosted": dayPosted,
           "jobURL": jobURL,
          'location': location,
          'jobDesc': jobDesc['description'],
          'rating': rating
      }
    

def get_job_cards(url):
    """
    Fetches the HTML content from a LinkedIn jobs search URL and returns a list of job cards as BeautifulSoup objects.
    
    Args:
        url (str): A LinkedIn job search URL.
    
    Returns:
        List[bs4.element.Tag]: A list of job cards as BeautifulSoup objects.
    """
    
    logging.info('Getting jobs from %s', url)
    
    res = requests.get(url, headers=headers)
    time.sleep(1)
    html = res.text    

    # Parse the HTML content using BeautifulSoup library (or any other method)
    soup = BeautifulSoup(html, "html.parser")

    # Find all the elements with class name 'base-card' which contain each job listing
    cards_ul = soup.find('ul', class_="jobs-search__results-list")
    
    cards = []
    
    if cards_ul:
        cards = cards_ul.find_all('li')
    else:
        try:
            cards = soup.find_all('li')
        except:
            ...
    
    return cards
    
    
def extractJobs(urls:list, plavras:list):
  """
    Extracts job information from a list of LinkedIn job search URLs and a list of keywords (plavras).
    
    Args:
        urls (List[str]): A list of LinkedIn job search URLs.
        plavras (List[str]): A list of keywords to rate the jobs.
    
    Returns:
        Tuple[List[dict], int]: A tuple containing a list of job dictionaries and the total number of cards.
  """
  
  plavras = normalize_text(' '.join(plavras)).split(' ')

  # Create an empty list to store the results
  results = []

  # Fetch the HTML content from the URL using requests library (or any other method)
  try:
    #with ThreadPoolExecutor(max_workers=10) as executor:
     # cards = executor.map(get_job_cards, urls)
      
    cards = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
      card_futures = [executor.submit(get_job_cards, url) for url in urls]
      for future in concurrent.futures.as_completed(card_futures):
        cards.extend(future.result())
    
    #cards = pool_processor(get_job_cards, urls)
    #cards = [card for sublist in cards for card in sublist]
    
    total_cards = len(cards)
    
    if len(cards) ==0:
      return [results, 0]

    # Loop through each card element and extract the relevant information
    with concurrent.futures.ThreadPoolExecutor(max_workers=sqrt(len(cards))) as executor:
      results = executor.map(get_job_info, cards, repeat(plavras))
        
    #with ThreadPoolExecutor(max_workers=10) as executor:
     # job_data_list = executor.map(get_job_info, cards, repeat(plavras))
    
    #for job in job_data_list:
     # results.append(job)
  
  except Exception as e:
    print(e)

  #logging.info('Finished getting jobs from %s', urls)
  # Return results list 
  return [results, total_cards]
  
  
def extractDescription(url):
  """
    Extracts job description and location from a LinkedIn job posting URL.
    
    Args:
        url (str): A LinkedIn job posting URL.
    
    Returns:
        dict: A dictionary containing the job description and location.
  """
  
  results = {}
  # Create an empty dictionary to store the result

  # Fetch the HTML content from the URL using requests library (or any other method)
  #logging.info('Getting job description from %s', url)
  try:
    time.sleep(random.uniform(1, 6))
    res = requests.get(url, headers=headers, timeout=3)
    html = res.text

    # Parse the HTML content using BeautifulSoup library (or any other method)
    soup = BeautifulSoup(html, "html.parser")
    
    # Find the element with class name 'description__text' which contains the job's description
    descriptionDiv = soup.find("div", class_="show-more-less-html__markup")
      
    # Call the parseDescription function on this element and get the result dictionary
    
    time.sleep(0.5)
    # Get the text content of the element
    if descriptionDiv is not None:
      description = descriptionDiv.text.strip()
    else:
      description = 'no description specified'
    

    # Add the complete description to result dictionary 
    results['description'] = normalize_text(description)

  except Exception as e:
    print('Error while getting job description: %s, %s', str(e), url)

  #print('Finished getting job description from %s', url)

  # Return result dictionary 
  return results

   
def rate_job(job_description, plavras=False):
    """
    Rates a job based on its description and a list of keywords (plavras).
    
    Args:
        job_description (str): The job description as a string.
        plavras (List[str], optional): A list of keywords to rate the job. Defaults to False.
    
    Returns:
        float: The rating score, rounded to 2 decimal places.
    """
    
    #print('Now rating jobs:/*/*/*/*/')
    rating = 0

    # Check if there are any plavras for the user
    if not plavras:
        return rating
        
    rating = rate_text(plavras, job_description)

    return round(rating, 4)


   
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
      TPeriod = ""
      
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
    
#  user = search_customer(id) # using woocommerce

  location = location.replace(" ", "%20").replace(",", "%2C")

  urls = []
  
  for url in titles:
    keywords = url.replace(" ", "%20").replace(",", "%2C")
    urls.append(f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}{time_period}&position=1&pageNum=0")

  print('REQUESTED URIs: ', urls)
  return JSONResponse(content=extractJobs(urls, plavra))


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

    ress = extractJobs(['https://www.linkedin.com/jobs/search?keywords=Engenharia%20Ambiental&location=Brazil&f_TPR=r86400&position=1&pageNum=0',
    'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=software-engineer&start=225&location=Brazil'], plavra)
    
    elapsed_time = time.time() - start_time
    
    for res in ress[0]:
      print(res['rating'])
    print(f"Time taken to extract job description: {elapsed_time:.2f} seconds")
  except Exception as e:
    logging.error('Error while running the application: %s', str(e))
  
