"""
This module is designed to scrape job postings from the InfoJobs website (https://www.infojobs.com.br/) and analyze their descriptions
based on the given keywords. It then assigns a rating to each job posting based on how well the description matches the specified keywords.

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

class Infojobs:
    """
    A class that represents the InfoJobs scraper, designed to scrape job postings and analyze their descriptions based on given keywords.
    """
    
    def __init__(self, urls:list, palavras, timeout_event: Event, time_period=None, card_num=10):
        """
        Initializes the Infojobs object with the specified parameters.

        Args:
            urls (list): A list of URLs to scrape job postings from.
            palavras (list): A list of keywords to analyze job descriptions.
            timeout_event (Event): A threading Event object used to stop the scraper after a specified period of time.
            time_period (Optional[str]): A time period filter for scraping job postings (default is None).
            card_num (int): The maximum number of job cards to scrape (default is 10).
        """
        
        self.urls = urls
        self.palavras = palavras
        self.time_period = time_period
        if time_period:
            self.time_period = time_period.split('=r')[-1]
        self.timeout_event = timeout_event
        self.card_num = card_num
        self.cards = []
        self.total_pages = 1
        self.page_index = 1
        self.job_keyword = None
        
    def parse_cards_url(self, url):
        """
        Parses the specified URL to obtain a list of job cards.

        Args:
            url (str): The URL to parse.

        Returns:
            list: A list of job cards obtained from the specified URL.
        """
        
        cards = []
        cards = self.get_job_cards(cards, url)
        if len(cards)>self.card_num:
            return cards[0:self.card_num]
        return cards
        
    def get_job_cards(self, cards:list, url):
        """
        Retrieves job cards from the specified URL and appends them to the cards list.

        Args:
            cards (list): The list of job cards to append new job cards to.
            url (str): The URL to retrieve job cards from.

        Returns:
            list: The updated list of job cards.
        """
        
        if self.timeout_event.is_set():
            return cards
            
        print('===========>Getting cards for: ', url)
        try:
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200:
                print('success status: ', res.status_code)
                self.job_keyword = url.split('=')[1].split('&')[0]
                time.sleep(.5)
                html = res.content
                
                soup = BeautifulSoup(html, "html.parser")

                if not '?page=' in url:
                    total_pages_element = soup.find('div', {'id':"resumeVacancies"})
                    if total_pages_element:
                        total_pages_element = total_pages_element.find('div', class_='col-auto caption')
                        if total_pages_element:
                            self.total_pages = int(total_pages_element.get_text().split()[-1])
            
                cards_list = soup.find('div', {'id':"filterSideBar"})
                # get cards
      
                if cards_list:
                    cards.extend(cards_list.find_all('div', class_='card'))
                
                if len(cards) >= self.card_num:
                    return cards
                                    
                if self.total_pages > self.page_index:
                    self.page_index += 1
                    self.get_job_cards(cards, f'https://www.infojobs.com.br/vagas-de-emprego-{self.job_keyword}-em-porto-alegre,-rs.aspx?page={self.page_index}')
                else:
                    return cards
            else:
                print(res.status_code)
                return cards
        except Exception as e:
            print('Error while getting job cards: ', e)
            return cards
    
    
    def get_job_info(self, card):
        """
        Extracts job information from a job card and returns it as a dictionary.

        Args:
            card (BeautifulSoup object): A BeautifulSoup object representing a job card.

        Returns:
            dict: A dictionary containing the extracted job information.
        """
        
        if self.timeout_event.is_set():
            return {}

        day_posted_element = card.find('div', class_='text-medium small')
        day_posted = day_posted_element.text.strip()
        if self.time_period:
            time_period = int(date_category(day_posted))
            if time_period > int(self.time_period):
                return

        job_title_element = card.find('h2', class_='h3')
        if job_title_element is None:
            print('============== FAILED CARD ================')
            print(card)
            print('============ FAILED CARD END ==============')
            return None
        job_title = job_title_element.get_text(strip=True) if job_title_element else "Not specified"


        job_url_element = card.find('div', class_='py-16')
        job_url = 'https://www.infojobs.com.br' + job_url_element['data-href'] if job_url_element else "Not specified"

        location_element = card.find('div', class_='small text-medium mr-24')
        location = location_element.get_text(strip=True) if location_element else "Not specified"

        job_desc = self.extractDescription(job_url)

        company_name_element = card.find('a', class_='text-body text-decoration-none')
        company_name = company_name_element.get_text(strip=True) if company_name_element else "Not specified"

        rating = 0
        if job_desc is not None:
            try:
                rating = rate_text(normalize_text(job_desc), self.palavras)
            except:
                rating = '---'

            job = {
        "jobTitle": normalize_text(job_title),
        "companyName": normalize_text(company_name),
        "dayPosted": day_posted,
        "jobURL": job_url,
        'rating': rating,
        'location': normalize_text(location)
            }

            print('JOB: ', json.dumps(job, indent=2))
            return job


    def extractDescription(self, url):
        """
        Extracts the job description from a job posting URL.

        Args:
            url (str): The job posting URL.

        Returns:
            str: The extracted job description.
        """
        
        if self.timeout_event.is_set():
            return None
        try:
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200:
                description_page_info = {}
                html = res.content

                soup = BeautifulSoup(html, "html.parser")
                descriptionDiv = soup.find("div", class_="js_vacancyDataPanels")
      
                # Get the text content of the element
                if descriptionDiv is not None:
                    description = descriptionDiv.text.strip()
                else:
                    description = None
                
                return description

        except Exception as e:
            print('Error while getting job description: %s, %s', str(e), url)
            return None
            
        
    def main(self):
        """
        Main function that coordinates the scraping and processing of job postings from the InfoJobs website.

        Returns:
            tuple: A tuple containing a list of job postings and the total number of job postings.
        """
        
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.parse_cards_url, self.urls)

            cards = list(cards)
            print('Infojobs Cards: ', cards)
            print('//////////////////////')
            print('Total infojobs Cards: ', len([crd for card in cards for crd in card]))
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
    WEBSITE_URL =[ 'https://www.infojobs.com.br/empregos.aspx?palabra=Auxiliar+de+produ%C3%A7%C3%A3o&poblacion=5209591',
    
    'https://www.infojobs.com.br/vagas-de-emprego-auxiliar+de+produ%C3%A7%C3%A3o-em-porto-alegre,-rs.aspx?page=2']
    
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
        time.sleep(300)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    infojobs = Infojobs(WEBSITE_URL, plavra, timeout_event)
    jobs = infojobs.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
