# Import FastAPI and requests libraries
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from typing import Optional


class JobsParams(BaseModel):
    keywords: str
    location: Optional[str] = 'Brazil'
    time_period: Optional[str] = None


import requests
import time
import json
import re


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

def extractJobs(url):

  print('Getting jobs')

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

    # Loop through each card element and extract the relevant information
    for card in cards:
    
      # Get the text content and href attribute of the title link element
      jobTitle = card.find("h3", class_="base-search-card__title").text.strip()
      jobURL = card.find("a", class_="base-card__full-link").get("href")
      jobLoc = LOCATION
      jobDesc = extractDescription(jobURL)
      
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
        'jobDesc': jobDesc
      })
      

  except Exception as error:
    print(error)

  # Return results list 
  return results
  
def extractDescription(url):

  # Create an empty dictionary to store the result
  result = {}

  # Fetch the HTML content from the URL using requests library (or any other method)
  print('getting descr:  ', url)
  try:
    res = requests.get(url)
    html = res.text
    print('descr =*=*=*=*=*=*=>:  ', html)

    # Parse the HTML content using BeautifulSoup library (or any other method)
    soup = BeautifulSoup(html, "html.parser")

    # Find the element with class name 'description__text' which contains the job's description
    descriptionDiv = soup.find("div", class_="description__text")
    
    locationDiv = soup.find("h4", class_="top-card-layout__second-subline")
    if locationDiv is not None:
      location = locationDiv.find("span", class_="topcard__flavor").text.strip()
      result["location"] = location
      
    # Call the parseDescription function on this element and get the result dictionary 
    result.update(parseDescription(descriptionDiv))

  except Exception as error:
    print(error)

  # Return result dictionary 
  return result



def parseDescription(element):

  # Create an empty dictionary to store the result
  result = {}

  # Get the text content of the element
  description = re.sub('\\\n', '', element.text.strip())

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
  return json.dumps(result) 
   
   

# Define a GET endpoint that takes a query parameter 'url' and returns the result of extractJobs function
@app.get("/jobs")
def get_jobs(params: JobsParams):
  
  keywords = params.keywords.replace(" ", "%20")
  keywords = params.keywords.replace(",", "%2C")
  
  location = params.location.replace(" ", "%20")
  location = params.location.replace(",", "%2C")
  
  time_period = params.time_period if params.time_period else None

  url = f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}{'&'time_period if time_period else ''}"

  print('REQUESTED URI: ', url)
  return JSONResponse(content=extractJobs(url))


# Define a GET endpoint that takes a query parameter 'url' and returns the result of extractJobs function
@app.get("/description")
def get_jobs(request: Request):
  return JSONResponse(content=extractDescription(request.query_params.get('url', None)))
  
  
if __name__ == "__main__":
  ress = extractJobs('https://www.linkedin.com/jobs/search?keywords=Engenharia%20Ambiental&location=Brazil&f_TPR=r86400')
  
  print(json.dumps(ress))
  
  
