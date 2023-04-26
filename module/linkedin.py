

from bs4 import BeautifulSoup
from typing import Optional, List, Union

from woocommerce import API
from module.docsim import rate_text, normalize_text
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


requests.adapters.DEFAULT_RETRIES = 3
headers = {'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'}

class LinkedIn:
    def __init__(self, urls:list, palavras, timeout_event: Event, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.timeout_event = timeout_event
        self.card_num = card_num
        
    def get_job_cards(self, url):
        """
        Fetches the HTML content from a LinkedIn jobs search URL and returns a list of job cards as BeautifulSoup objects.
        
        Args:
            url (str): A LinkedIn job search URL.
        
        Returns:
            List[bs4.element.Tag]: A list of job cards as BeautifulSoup objects.
        """
        
        if self.timeout_event.is_set():
            return []
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
                    
            if len(cards)>self.card_num:
                return cards[0:self.card_num]
                
        return cards
        
    
    def get_job_info(self, card):
        """
          Extracts job information from a BeautifulSoup card object and a list of keywords (plavras).
          
          Args:
              card (bs4.element.Tag): A BeautifulSoup object representing a single job card.
              plavras (List[str]): A list of keywords to rate the job.
          
          Returns:
              dict: A dictionary containing job title, company name, day posted, job URL, rating, location, and job description.
        """
        
        if self.timeout_event.is_set():
            return {}

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
          
        if jobDesc:
            try:
                rating = rate_text(normalize_text(jobDesc), self.palavras)
            except:
                rating = '---'
              
            job = {
                "jobTitle": jobTitle,
                "companyName": companyName,
                "dayPosted": dayPosted,
                "jobURL": jobURL,
                'rating': rating,
                'location': location
                }
            
            print('JOB: ', job)
            # Create a dictionary with all these information and append it to results list 
            return job


    def extractDescription(self, url):
        """
          Extracts job description and location from a LinkedIn job posting URL.
          
          Args:
              url (str): A LinkedIn job posting URL.
          
          Returns:
              dict: A dictionary containing the job description and location.
        """
        if self.timeout_event.is_set():
            return None
        
        description = None
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
              description = normalize_text(descriptionDiv.text.strip())
            else:
              description = None

        except Exception as e:
          print('Error while getting job description: %s, %s', str(e), url)

        #print('Finished getting job description from %s', url)

        # Return result dictionary 
        return description
        
    def main(self):
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.get_job_cards, self.urls)

            cards = list(cards)

            if len(cards) ==0:
                return [[], 0]

            # Loop through each card element and extract the relevant information
            #results = [get_job_info(card, plavras) for card in cards]
            results = []
            
            job_data_list = []

            for card in cards:
                if self.timeout_event.is_set():
                    break
                if len(card)>0:
                    time.sleep(2)
                    root = sqrt(len(card))
                    if root >=1:
                        if root > 10:
                            workers = round(sqrt(len(card)))
                        else:
                            workers = len(card)
                    else:
                        workers = 1
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        job_data = executor.map(self.get_job_info, card)

                    job_data_list.extend(list(job_data))

            results = [jb for jb in job_data_list if jb]
              
            total_cards = len(results)
              
          #    for job in job_data_list:
          #     results.append(job)
                
            return [results, total_cards]
        
        except Exception as e:
            print(e)
            return [[], 0]
  

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

    timeout_event = Event()
    # Start the timeout thread before calling the extractJobs function
    def stop_extraction():
        time.sleep(90)
        timeout_event.set()
        
    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    linked = LinkedIn(url_list, plavra, timeout_event)
    jobs = linked.main()

    elapsed_time = time.time() - start_time

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))

    
    
    for res in jobs[0]:
      print(res['rating'])
      
    print(f"Time taken to extract job description: {elapsed_time:.2f} seconds")
  except Exception as e:
    logging.error('Error while running the application: %s', str(e))
	   

  
