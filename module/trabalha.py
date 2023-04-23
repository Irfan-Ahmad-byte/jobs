"""
https://www.trabalhabrasil.com.br/
"""


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

class Trabalha:
    def __init__(self, urls:list, palavras, timeout_event: Event):
        self.urls = urls
        self.palavras = palavras
        self.timeout_event = timeout_event
        
    def get_job_cards(self, url):
        if self.timeout_event.is_set():
            return []
            
        print('===========>Getting cards for: ', url)
        res = requests.get(url, timeout=3)
        cards = []
        if res.status_code==200:
            time.sleep(.5)
            html = res.content
      
            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")

            # Find all the elements with class name 'base-card' which contain each job listing
            cards_list = soup.find('div', {"id":"jobs-wrapper"})
      
            # get cards
      
            if cards_list:
                cards = cards_list.find_all('a', class_='job__vacancy')
        
        return cards
    
    
    def get_job_info(self, card):
        if self.timeout_event.is_set():
            return {}
        # Get the text content and href attribute of the title link element
        jobTitle = card.find('h2', class_='job__name').text.strip()
        
        dayPosted = '---'
    
        jobURL = 'https://www.trabalhabrasil.com.br'+card['href']
        try:
            location = card.find_all('h3', class_='job__detail')[-1].text.strip()
        except:
            location = 'location not given'

        jobDesc = self.extractDescription(jobURL)
  
        # Get the text content of the company link element
        try:
            companyName = card.find('h3', class_='job__company').text.strip()
        except:
            companyName = 'Not specified'
        
        rating = 0
        
        if jobDesc is not None:
            rating = rate_text(normalize_text(jobDesc), self.palavras)
        
        job = {
          "jobTitle": jobTitle,
          "companyName": companyName,
          "dayPosted": dayPosted,
           "jobURL": jobURL,
           'rating': rating,
          'location': normalize_text(location)
            }
      
        print('JOB: ', json.dumps(job, indent=2))
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
        # Fetch the HTML content from the URL using requests library (or any other method)
        #logging.info('Getting job description from %s', url)
        try:
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200:
                html = res.content

                # Parse the HTML content using BeautifulSoup library (or any other method)
                soup = BeautifulSoup(html, "html.parser")
    
                # Find the element with class name 'description__text' which contains the job's description
                descriptionDiv = soup.find("div", class_="jobview__info")
      
                # Get the text content of the element
                if descriptionDiv is not None:
                    description = descriptionDiv.text.strip()
                else:
                    description = 'no description specified'
                
                return description

        except Exception as e:
            print('Error while getting job description: %s, %s', str(e), url)

            #print('Finished getting job description from %s', url)

            # Return result dictionary 
            return None
        
    def main(self):
        
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.get_job_cards, self.urls)
                
            cards = list(cards)
            print('//////////////////////')
            print('Totla trabalha Cards: ', len([crd for card in cards for crd in card]))
            print('//////////////////////')
    
            if len(cards) ==0:
                return [[], 0]

            # Loop through each card element and extract the relevant information
            #results = [get_job_info(card, plavras) for card in cards]
            results = []
            
            jobs_data_list = []
            for card in cards:
                if self.timeout_event.is_set():
                    break
                if len(card)>0:
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
      
                    jobs_data_list.extend(list(job_data))
                    
            results = [jb for jb in jobs_data_list if jb]
    
            total_cards = len(results)
    
        #    for job in job_data_list:
         #     results.append(job)
      
            return [results, total_cards]
  
        except Exception as e:
            print(e)
            return [[], 0]
  

if __name__ == '__main__':
    WEBSITE_URL = 'https://www.trabalhabrasil.com.br/vagas-empregos-em-sao-paulo-sp/software%20engineer'
    
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
	
    timeout_event = Event()
    # Start the timeout thread before calling the extractJobs function
    def stop_extraction():
        time.sleep(60)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    trabalha = Trabalha([WEBSITE_URL], plavra, timeout_event)
    jobs = trabalha.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
