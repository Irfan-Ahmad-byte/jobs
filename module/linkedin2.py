

from bs4 import BeautifulSoup
from typing import Optional, List, Union

from woocommerce import API
from module.docsim import rate_text, normalize_text
from itertools import repeat
from math import sqrt

from jobs_Scraper import JobScraper

from concurrent.futures import ThreadPoolExecutor
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

class LinkedInScraper(JobScraper):
    def parse_job_cards(self, soup: BeautifulSoup) -> List:
        """
        Fetches the HTML content from a LinkedIn jobs search URL and returns a list of job cards as BeautifulSoup objects.
        
        Args:
            url (str): A LinkedIn job search URL.
        
        Returns:
            List[bs4.element.Tag]: A list of job cards as BeautifulSoup objects.
        """
        print('===========>Getting cards for: ', url)
        
        res = requests.get(url)
        cards = []
        if res.status_code==200:
            time.sleep(1)
            html = res.content    

            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")

            # Find all the elements with class name 'base-card' which contain each job listing
            cards_ul = soup.find('ul', class_="jobs-search__results-list")
        
        
            if cards_ul:
                cards = cards_ul.find_all('li')
            else:
                try:
                    cards = soup.find_all('li')
                except:
                    ...
        
        return cards

    def parse_job_info(self, card) -> dict:
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
        
        if not jobTitle:
            return
          
        jobURL = card.find("a")['href']
        try:
            location = card.find("span", class_='job-search-card__location').text.strip()
        except:
            location = 'location not given'

        jobDesc = self.extractDescription(jobURL)
        
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
          
        rating = rate_text(normalize_text(jobDesc), plavras)
              
        job = {
                "jobTitle": jobTitle,
                "companyName": companyName,
                "dayPosted": dayPosted,
                "jobURL": jobURL,
                'rating': rating,
                'location': location,
                'jobDesc': jobDesc
            }
            
        print('JOB: ', job)
            # Create a dictionary with all these information and append it to results list 
        return job
        
    def parse_job_description(self, card) -> dict:
        """
          Extracts job description and location from a LinkedIn job posting URL.
          
          Args:
              url (str): A LinkedIn job posting URL.
          
          Returns:
              dict: A dictionary containing the job description and location.
        """
        
        description = ''
        # Create an empty dictionary to store the result

        # Fetch the HTML content from the URL using requests library (or any other method)
        #logging.info('Getting job description from %s', url)
        try:
          time.sleep(3)
          res = requests.get(url, headers=headers, timeout=3)
          if res.status_code == 200:
            html = res.content

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
          description = normalize_text(description)

        except Exception as e:
          print('Error while getting job description: %s, %s', str(e), url)

        #print('Finished getting job description from %s', url)

        # Return result dictionary 
        return description
                
  

if __name__ == '__main__':

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
        'https://www.linkedin.com/jobs/search?keywords=Engenharia%20Ambiental&location=Brazil&f_TPR=r86400&position=1&pageNum=0',
        'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=software-engineer&start=225&location=Brazil',
        
    ]

    linked = LinkedIn(url_list, plavra)
    jobs = linked.main()

    elapsed_time = time.time() - start_time

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))

    
    
    for res in jobs[0]:
      print(res['rating'])
      
    print(f"Time taken to extract job description: {elapsed_time:.2f} seconds")
  except Exception as e:
    logging.error('Error while running the application: %s', str(e))
	   

  
