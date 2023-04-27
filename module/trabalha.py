"""
This module is used for scraping job listings from Trabalha Brasil (https://www.trabalhabrasil.com.br/) based on the provided search URLs and a list of keywords.
The script utilizes the BeautifulSoup library in Python to parse the HTML content and extract the relevant job information.

Developer: Irfan Ahmad, devirfan.mlka@gmail.com
Project Owner: Monica Piccinini, monicapiccinini12@gmail.com
"""


from bs4 import BeautifulSoup
from typing import Optional, List, Union

from woocommerce import API
from module.docsim import rate_text, normalize_text, date_category
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
    """
    A class used to represent a Trabalha Brasil job scraper.

    Attributes:
    -----------
    urls : list
        A list of Trabalha Brasil job search URLs.
    palavras : list
        A list of keywords to rate the jobs.
    timeout_event : Event
        A threading Event object to control the timeout functionality.
    card_num : int, optional
        The maximum number of job cards to be returned, defaults to 10.

    Methods:
    --------
    get_job_cards(self, url)
        Fetches the HTML content from a Trabalha Brasil jobs search URL and returns a list of job cards as BeautifulSoup objects.
    get_job_info(self, card)
        Extracts job information from a BeautifulSoup card object and a list of keywords.
    extractDescription(self, url)
        Extracts job description from a Trabalha Brasil job posting URL.
    main(self)
        Controls the flow of the script, fetching job cards, extracting information, and returning the result.
    """
    
    def __init__(self, urls:list, palavras, timeout_event: Event, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.timeout_event = timeout_event
        self.card_num = card_num
        
    def get_job_cards(self, url):
        """
        Fetches the HTML content from a Trabalha Brasil jobs search URL and returns a list of job cards as BeautifulSoup objects.
        
        Args:
            url (str): A Trabalha Brasil job search URL.
        
        Returns:
            List[bs4.element.Tag]: A list of job cards as BeautifulSoup objects.
        """
        
        if self.timeout_event.is_set():
            return []
            
        print('===========>Getting cards for: ', url)
        res = requests.get(url, timeout=3)
        cards = []
        if res.status_code==200:
            time.sleep(.5)
            html = res.content
      
            soup = BeautifulSoup(html, "html.parser")

            cards_list = soup.find('div', {"id":"jobs-wrapper"})
      
            # get cards
      
            if cards_list:
                cards = cards_list.find_all('a', class_='job__vacancy')
                
            if len(cards)>self.card_num:
                return cards[0:self.card_num]
        
        return cards
    
    
    def get_job_info(self, card):
        """
        Extracts job information from a BeautifulSoup card object and a list of keywords (palavras).
          
        Args:
            card (bs4.element.Tag): A BeautifulSoup object representing a single job card.
            palavras (List[str]): A list of keywords to rate the job.
          
        Returns:
            dict: A dictionary containing job title, company name, day posted, job URL, rating, and location.
        """
        
        if self.timeout_event.is_set():
            return {}
        jobTitle = card.find('h2', class_='job__name').text.strip()
        
        dayPosted = '---'
    
        jobURL = 'https://www.trabalhabrasil.com.br'+card['href']
        try:
            location = card.find_all('h3', class_='job__detail')[-1].text.strip()
        except:
            location = 'location not given'

        jobDesc = self.extractDescription(jobURL)
  
        try:
            companyName = card.find('h3', class_='job__company').text.strip()
        except:
            companyName = 'Not specified'
        
        rating = 0
        
        if jobDesc is not None:
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
          'location': normalize_text(location)
                }
      
            print('JOB: ', json.dumps(job, indent=2))
            return job


    def """
        Extracts job description from a Trabalha Brasil job posting URL.
          
        Args:
            url (str): A Trabalha Brasil job posting URL.
          
        Returns:
            str: The job description as a string, or None if not found.
        """
        
        if self.timeout_event.is_set():
            return None
        try:
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200:
                html = res.content

                soup = BeautifulSoup(html, "html.parser")
                descriptionDiv = soup.find("div", class_="jobview__info")
      
                # Get the text content of the element
                if descriptionDiv is not None:
                    description = descriptionDiv.text.strip()
                else:
                    description = 'no description specified'
                
                return description

        except Exception as e:
            print('Error while getting job description: %s, %s', str(e), url)
            return None
        
    def main(self):
        """
        Controls the flow of the script, fetching job cards, extracting information, and returning the result.

        Returns:
            tuple: A tuple containing a list of dictionaries with the job details and the total number of job cards.
        """
        
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.get_job_cards, self.urls)

            cards = list(cards)
            print('//////////////////////')
            print('Totla trabalha Cards: ', len([crd for card in cards for crd in card]))
            print('//////////////////////')

            if len(cards) ==0:
                return [[], 0]

            results = []
            
            jobs_data_list = []
            
            for card in cards:
                if self.timeout_event.is_set():
                    break
                if len(card)>0:
                    with ThreadPoolExecutor(max_workers=len(card)) as executor:
                        job_data = executor.map(self.get_job_info, card)

                    jobs_data_list.extend(list(job_data))

            results = [jb for jb in jobs_data_list if jb]
    
            total_cards = len(results)
      
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
   

  
