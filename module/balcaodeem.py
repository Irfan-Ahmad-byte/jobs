"""
This module scrapes job listings from 'https://www.balcaodeempregos.com.br/' and rates them based on the relevance of specified keywords.

The main class in this module is Balca, which provides methods to parse job cards, extract job information, and rate the jobs based on the relevance of specified keywords.

Developer: Irfan Ahmad, devirfan.mlka@gmail.com
Project Owner: Monica Piccinini, monicapiccinini12@gmail.com
"""

from bs4 import BeautifulSoup, element
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

class Balca:
    """
    A class to scrape and process job listings from 'https://www.balcaodeempregos.com.br/'.

    Attributes:
        urls (list): A list of URLs to scrape job listings from.
        palavras (list): A list of keywords to rate the job listings.
        timeout_event (Event): A threading.Event to signal when the scraping should be stopped.
        time_period (Optional[str]): Time period filter for the job listings.
        card_num (int): The maximum number of job cards to retrieve.

    Methods:
        parse_cards_url(url: str) -> List[Dict[str, str]]:
            Parses job cards from the provided URL and returns a list of job card elements.

        get_job_cards(cards: List, url: str) -> List[Dict[str, str]]:
            Recursively fetches job cards and adds them to the cards list.

        get_job_info(card: element.Tag) -> Optional[Dict[str, Union[str, int]]]:
            Extracts job information from a job card element and returns a dictionary with the relevant data.

        extractDescription(url: str, job_id: str) -> Optional[str]:
            Extracts job description from the provided job posting URL.

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
        self.card_num = card_num
        
        self.total_pages = 1
        self.page_index = 1
        
    def parse_cards_url(self, url):
        """
        Parses job cards from the provided URL and returns a list of job card elements.

        Args:
            url (str): The URL to scrape job cards from.

        Returns:
            list: A list of job card elements.
        """
        
        cards = []
        cards = self.get_job_cards(cards, url)
        if len(cards)>self.card_num:
            return cards[0:self.card_num]
        return cards
    
    
    def get_job_cards(self, cards:list, url):
        """
        Recursively fetches job cards and adds them to the cards list.

        Args:
            cards (list): The list of job cards to append to.
            url (str): The URL to scrape job cards from.

        Returns:
            list: The list of job cards.
        """
        
        if self.timeout_event.is_set():
            return cards
            
        print('===========>Getting cards for: ', url)
        try:
            res = requests.get(url, headers=headers)
            if res.status_code==200:
                time.sleep(.5)
                html = res.content
      
                soup = BeautifulSoup(html, "html.parser")
            
                if '?pagina=' not in url:
                    total_pages_element = soup.find('ul', class_='pagination')
                    if total_pages_element:
                        self.total_pages = len(total_pages_element.find_all('li'))

                cards_list = soup.find('fieldset')
                # get cards
      
                if cards_list:
                    cards.extend(cards_list.find_all('div', class_='panel-body panel-vaga link-draw-vaga'))
                
                if len(cards) >= self.card_num:
                    return cards
                                    
                if self.total_pages > self.page_index:
                    self.page_index += 1
                    self.get_job_cards(cards, url.replace('?', f'?pagina={self.page_index}&'))
                else:
                    return cards
        except:
            return cards
    
    def get_job_info(self, card):
        """
        Extracts job information from a job card element and returns a dictionary with the relevant data.

        Args:
            card (element.Tag): A job card element.

        Returns:
            Optional[dict]: A dictionary with job information, or None if the time_period condition is not met.
        """
        
        if self.timeout_event.is_set():
            return {}
                        
        job_secs = card.find_all('div', recursive=False)
        job_title_section = job_secs[0]
        job_title_element = job_title_section.find_all('div', recursive=False)

        day_posted = job_title_element[1].find('strong').text.strip()
        if self.time_period:
            time_period = int(date_category(day_posted))
            if time_period > int(self.time_period):
                return

        job_id = card['id-vaga']
        
        job_location_section = job_secs[1]
        job_detail_section = job_secs[3]
        
        job_title = job_title_element[0].text.strip()

        location = ' '.join(job_location_section.text.strip().split(' ')[1:])

        company_name = job_detail_section.find('div').find_all('strong', recursive=False)[0].find_next_sibling('span').text.strip()

        base_url = 'https://www.balcaodeempregos.com.br'
        
        comment = job_detail_section.find(string=lambda x: isinstance(x, element.Comment))
        href_match = re.search(r'href="(.+?)"', comment)
        if href_match:
            href = href_match.group(1)
            description_url = base_url+href
        
        job_response_url = f"https://www.balcaodeempregos.com.br/Vaga/GetVagaById"

        job_desc = self.extractDescription(job_response_url, job_id=job_id)


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
        "jobURL": description_url,
        'rating': rating,
        'location': normalize_text(location)
            }

            print('JOB: ', json.dumps(job, indent=2))
            return job


    def extractDescription(self, url, job_id):
        """
        Extracts job description from the provided job posting URL.

        Args:
            url (str): A job posting URL.
            job_id (str): The job ID to fetch the description for.

        Returns:
            Optional[str]: The job description or None if an error occurs.
        """
        
        try:
            data = {
                "id": job_id
            }
            res = requests.post(url, headers=headers, data=data)
            if res.status_code == 200:
                description_page_info = {}
                html = res.json()
                description = html['vaga']['Descricao']
                return description

        except Exception as e:
            print('Error while getting job description: %s, %s', str(e), url)
            return None
            
        
    def main(self):
        """
        The main function that orchestrates the scraping and processing of job listings.

        Returns:
            Tuple[list, int]: A tuple with a list of job dictionaries and the total number of job cards.
        """
        
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.parse_cards_url, self.urls)

            cards = list(cards)
            print('//////////////////////')
            print('Totla Balcaodeem Cards: ', len([crd for card in cards for crd in card]))
            print('//////////////////////')

            if len(cards) ==0:
                return [[], 0]

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
      
            return [results, total_cards]
  
        except Exception as e:
            print(e)
            return [[], 0]
  

if __name__ == '__main__':
    WEBSITE_URL =[ 'https://www.balcaodeempregos.com.br/vagas-por-cargo/recepcionista?criterio=Recepcionista&cidadeEstado=']
    
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
        time.sleep(40)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    balca = Balca(WEBSITE_URL, plavra, timeout_event)
    jobs = balca.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
