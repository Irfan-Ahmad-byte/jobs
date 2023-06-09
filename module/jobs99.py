"""
A module to scrape job listings from 99jobs.com and extract relevant job information.

This module provides the Jobs99 class to scrape job listings from 99jobs.com,
extract job information from the job cards, and rate the job descriptions based on provided keywords.

Attributes:
    requests.adapters.DEFAULT_RETRIES (int): Default number of retries for requests.
    headers (dict): Default headers for requests.

Classes:
    Jobs99: A class that scrapes job listings from 99jobs.com.

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

class Jobs99:
    """
    A class that scrapes job listings from 99jobs.com.
    
    Attributes:
        urls (list): List of URLs to scrape job listings from.
        palavras (list): List of keywords for rating the job description.
        timeout_event (Event): An event to stop the extraction process after a specified time.
        time_period (int): The time in seconds after which the extraction process will be stopped.
        card_num (int): Maximum number of job cards to be scraped.
        
    Methods:
        get_job_cards(url: str) -> List[bs4.element.Tag]:
            Scrapes the job cards from the given URL.
            
        get_job_info(card: bs4.element.Tag) -> dict:
            Extracts job information from a given job card.
            
        extractDescription(url: str) -> Optional[dict]:
            Extracts job description and location from a given job URL.
            
        main() -> List[Union[List[dict], int]]:
            Scrapes job listings from the provided URLs and returns the extracted job information.
    """
    
    def __init__(self, urls:list, palavras, timeout_event: Event, time_period, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.time_period = time_period
        self.timeout_event = timeout_event
        self.card_num = card_num
        
        self.total_jobs = 0
        self.total_pages = 1
        
        self.page_index = 1
        
        self.cards = []
        
    def get_job_cards(self, url):
        """
        Scrapes the job cards from the given URL.
        
        Args:
            url (str): The URL to scrape job listings from.
            
        Returns:
            list: A list of BeautifulSoup Tag objects representing the job cards.
        """
        
        if self.timeout_event.is_set():
            return self.cards
            
        print('===========>Getting cards for: ', url)
        try:
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code==200:
                time.sleep(.5)
                html = res.content
                soup = BeautifulSoup(html, "html.parser")
            
                self.cards.extend(soup.find_all('a', class_='opportunity-card'))
                
                if len(self.cards)>self.card_num:
                    return self.cards[0:self.card_num]
        
            return self.cards
            
        except:
            return self.cards
    
    
    def get_job_info(self, card):
        """
        Extracts job information from a given job card.
        
        Args:
            card (bs4.element.Tag): A BeautifulSoup Tag object representing a job card.
            
        Returns:
            dict: A dictionary containing the extracted job information.
        """
        
        if self.timeout_event.is_set():
            return {}
            
        jobTitle = None
        dayPosted = None
        description = None
        rating = None
    
        jobURL = card['href']
        try:
            location = card.find('div', class_='opportunity-address').text.strip()
        except:
            location = 'location not given'

        jobDesc = self.extractDescription(jobURL)

        try:
            companyName = card.find('div', class_='opportunity-company-infos').find("h2").text.strip()
        except:
            companyName = 'Not specified'
        
        if jobDesc is not None:
            jobTitle = jobDesc['job_title']
            dayPosted = jobDesc['days_ramained']
    
            try:
                rating = rate_text(normalize_text(jobDesc['description']), self.palavras)
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


    def extractDescription(self, url):
        """
        Extracts job description and location from a given job URL.
        
        Args:
            url (str): A job posting URL.
            
        Returns:
            dict: A dictionary containing the job description and location, or None if an error occurs.
        """
        
        if self.timeout_event.is_set():
            return None
        try:
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200:
                description_page_info = {}
                html = res.content

                soup = BeautifulSoup(html, "html.parser")
                descriptionDiv = soup.find("div", class_="opportunities-details")
      
                side_bar = soup.find('div', class_='details')
                # job title
                try:
                    job_title = side_bar.find('h2').text.strip()
                except:
                    job_title = soup.find('h1').text.strip()
                    
                print(url, ': ', job_title)
      
                # days
                days_div = side_bar.find('div', class_='subscription-btn')
                extract_a_tag = days_div.find('a')
                extract_a_tag.extract()
                
                if days_div:
                    days = days_div.text.strip()
                else:
                    days = 'days not given'
      
                # Get the text content of the element
                if descriptionDiv is not None:
                    description = descriptionDiv.text.strip()
                else:
                    return None

                # Add the complete description to result dictionary
                description_page_info['description'] = normalize_text(description)
                description_page_info['job_title'] = normalize_text(job_title)
                description_page_info['days_ramained'] = days
                
                return description_page_info

        except Exception as e:
            print('Error while getting job description: %s, %s', str(e), url)
            return None
        
    def main(self):
        """
        Scrapes job listings from the provided URLs and returns the extracted job information.
        
        Returns:
            list: A list containing the extracted job information as dictionaries, and the total number of job cards.
        """
        
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.get_job_cards, self.urls)

            cards = list(cards)
            print('//////////////////////')
            print('Totla 99jobs Cards: ', len([crd for card in cards for crd in card]))
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
    WEBSITE_URL = 'https://99jobs.com/opportunities/filtered_search?utf8=%E2%9C%93&utm_source=tagportal&utm_medium=busca&utm_campaign=home&utm_id=001&search%5Bterm%5D=software%20engineer'
    
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
    
    jobs99 = Jobs99([WEBSITE_URL], plavra, timeout_event)
    jobs = jobs99.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
