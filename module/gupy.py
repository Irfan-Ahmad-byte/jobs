"""
This module provides a Gupy class to scrape and process job listings from 'https://portal.gupy.io/en'.
It extracts job information such as the job title, company name, location, posted date, and job URL.
Additionally, it rates the job listing based on the provided keywords.

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

def get_location(city):
    location_url = f'https://www.infojobs.com.br/mf-publicarea/api/autocompleteapi/locations?query={city}'
    res = requests.get(location_url, headers=headers)
    res = res.json()['suggestions']
    location_ids = []
    for data in res:
        location_ids.append(data['data']['id'])
    
    return location_ids

class Gupy:
    """
    A class to scrape and process job listings from 'https://portal.gupy.io/en'.

    Attributes:
        urls (list): A list of URLs to scrape job listings from.
        palavras (list): A list of keywords to rate the job listings.
        timeout_event (Event): A threading.Event to signal when the scraping should be stopped.
        time_period (Optional[str]): Time period filter for the job listings.
        card_num (int): The maximum number of job cards to retrieve.

    Methods:
        get_job_cards(url: str) -> List[Dict[str, str]]:
            Fetches job cards from the provided URL and returns a list of job card elements.

        get_job_info(card: Dict[str, str]) -> Optional[Dict[str, Union[str, int]]]:
            Extracts job information from a job card element and returns a dictionary with the relevant data.

        main() -> Tuple[List[Dict[str, Union[str, int]]], int]:
            The main function that orchestrates the scraping and processing of job listings.
    """
    
    def __init__(self, urls:list, palavras, timeout_event: Event, time_period=None, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.time_period = time_period
        if time_period:
            self.time_period = time_period.split('=r')[-1]
        self.timeout_event = timeout_event
        self.card_num=card_num
        
    def get_job_cards(self, url):
        """
        Fetches job cards from the provided URL and returns a list of job card elements.

        Args:
            url (str): The URL to scrape job cards from.

        Returns:
            list: A list of job card elements.
        """
        
        if self.timeout_event.is_set():
            return []
            
        print('===========>Getting cards for: ', url)
        res = requests.get(url, headers=headers, timeout=3)
        
        cards = []
        
        if res.status_code==200:
            time.sleep(.5)
            cards = res.json()["data"]
            print(f'Total jobs for {url}: ', len(cards))
            if len(cards)>self.card_num:
                return cards[0:self.card_num]
            return cards
        return cards
    
    
    def get_job_info(self, card):
        """
        Extracts job information from a job card element and returns a dictionary with the relevant data.

        Args:
            card (Dict[str, str]): A job card element.

        Returns:
            Optional[dict]: A dictionary with job information, or None if the time_period condition is not met.
        """
        
        if self.timeout_event.is_set():
            return {}

        posted_date = card["publishedDate"].split('T')[0]
        if self.time_period:
            time_period = int(date_category(posted_date))
            if time_period > int(self.time_period):
                return
        
        company_name = card["careerPageName"]
        location = f"{card['city']}, {card['state']}, {card['country']}"
        job_name = card["name"]
        description = card["description"]
        job_url = card["jobUrl"]

        rating = 0
        if description:
            try:
                rating = rate_text(normalize_text(description), self.palavras)
            except:
                rating = '---'

            job = {
        "jobTitle": normalize_text(job_name),
        "companyName": normalize_text(company_name),
        "dayPosted": posted_date,
        "jobURL": job_url,
        'rating': rating,
        'location': normalize_text(location)
            }

            print('JOB: ', json.dumps(job, indent=2))
            return job
        
    def main(self):
        """
        The main function that orchestrates the scraping and processing of job listings.

        Returns:
            Tuple[list, int]: A tuple with a list of job dictionaries and the total number of job cards.
        """
        
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.get_job_cards, self.urls)

            cards = list(cards)
            print('//////////////////////')
            print('Totla Gupy job Cards: ', len([crd for card in cards for crd in card]))
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
    WEBSITE_URL =[ 'https://portal.api.gupy.io/api/v1/jobs?jobName=python%20developer&limit=50&offset=1',
    'https://portal.api.gupy.io/api/v1/jobs?jobName=software%20engineer&limit=50&offset=1',
    'https://portal.api.gupy.io/api/v1/jobs?jobName=data%20entery%20operator&limit=50&offset=1',
    'https://portal.api.gupy.io/api/v1/jobs?jobName=data%20scientist&limit=50&offset=1']
    
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
        time.sleep(20)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    gupy = Gupy(WEBSITE_URL, plavra, timeout_event)
    jobs = gupy.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
