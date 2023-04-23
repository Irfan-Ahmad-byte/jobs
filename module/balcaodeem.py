"""
https://www.balcaodeempregos.com.br/
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

class Balca:
    def __init__(self, urls:list, palavras, timeout_event: Event, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.timeout_event = timeout_event
        self.card_num = card_num
        
    def get_job_cards(self, url):
        if self.timeout_event.is_set():
            return []
            
        print('===========>Getting cards for: ', url)
        res = requests.get(url, headers=headers)
        cards = []
        if res.status_code==200:
            time.sleep(.5)
            html = res.content
      
            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all the elements with class name 'base-card' which contain each job listing
            cards_list = soup.find('fieldset')
            # get cards
      
            if cards_list:
                cards.extend(cards_list.find_all('div', class_='panel-vaga link-draw-vaga'))
                    
            if len(cards)>self.card_num:
                return cards[0:self.card_num]
            return cards
        
        return cards
    
    
    def get_job_info(self, card):
        if self.timeout_event.is_set():
            return {}

        # Get the text content and href attribute of the title link element
        job_title_element = card.find('div', class_='col-xs-12 col-sm-8 col-lg-9 bold font-16 text-dark-gray no-padding-left no-padding-right').get_text().strip()
        if job_title_element is None:
            print('============== FAILED CARD ================')
            print(card)
            print('============ FAILED CARD END ==============')
            return None
        job_title = job_title_element.get_text(strip=True) if job_title_element else "Not specified"

        day_posted = '---'

        location = card.find('div', class_='col-xs-12 no-padding-left italic text-gray with-small-padding-bottom').get_text().strip()
        company_name = card.find('strong', string='Empresa: ').find_next_sibling('span').get_text().strip()
        
        job_id = card['id-vaga']

        job_url = f"https://www.balcaodeempregos.com.br/Vaga/GetVagaById"

        job_desc = self.extractDescription(job_url, job_id=job_id)


        rating = 0
        if job_desc is not None:
            rating = rate_text(normalize_text(job_desc), self.palavras)

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


    def extractDescription(self, url, job_id):
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
            data = {
                "id": job_id
            }
            res = requests.post(url, headers=headers, data=data)
            if res.status_code == 200:
                description_page_info = {}
                html = res.json()
    
                # Find the element with class name 'description__text' which contains the job's description
                description = html['vaga']['Descricao']
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
            print('Totla Balcaodeem Cards: ', len([crd for card in cards for crd in card]))
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
        time.sleep(20)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    balca = Balca(WEBSITE_URL, plavra, timeout_event)
    jobs = balca.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
