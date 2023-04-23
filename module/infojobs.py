"""
https://www.infojobs.com.br/
"""

'''
get location is => https://www.infojobs.com.br/mf-publicarea/api/autocompleteapi/locations?query=Bras%C3%ADlia
response: {"suggestions":[{"data":{"id":"5203868","group":"Cidades","groupType":5,"groupIconHtml":"\r\n\r\n    <span class=\"icon icon-location   icon-size-16\">\r\n        <svg><use xlink:href=\"#location\" /></svg>\r\n    </span>\r\n"},"value":"Brasília - DF"},{"data":{"id":"5206605","group":"Cidades","groupType":5,"groupIconHtml":"\r\n\r\n    <span class=\"icon icon-location   icon-size-16\">\r\n        <svg><use xlink:href=\"#location\" /></svg>\r\n    </span>\r\n"},"value":"Brasília Legal - PA"},{"data":{"id":"5204830","group":"Cidades","groupType":5,"groupIconHtml":"\r\n\r\n    <span class=\"icon icon-location   icon-size-16\">\r\n        <svg><use xlink:href=\"#location\" /></svg>\r\n    </span>\r\n"},"value":"Brasília de Minas - MG"}]}

jobs link => https://www.infojobs.com.br/empregos.aspx?palabra=Jovem+Aprendiz&poblacion=5203868


'''

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

def get_location(city):
    location_url = f'https://www.infojobs.com.br/mf-publicarea/api/autocompleteapi/locations?query={city}'
    res = requests.get(location_url, headers=headers)
    res = res.json()['suggestions']
    location_ids = []
    for data in res:
        location_ids.append(data['data']['id'])
    
    return location_ids

class Infojobs:
    def __init__(self, urls:list, palavras, timeout_event: Event, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.timeout_event = timeout_event
        self.card_num = card_num
        self.cards = []
        self.total_pages = 1
        self.job_keyword = None
        self.page_index = 1
        
    def get_job_cards(self, url):
        if self.timeout_event.is_set():
            return []
            
        print('===========>Getting cards for: ', url)
        res = requests.get(url, headers=headers)
        if res.status_code==200:
            self.job_keyword = url.split('=')[0].split('&')[0]
            time.sleep(.5)
            html = res.content
      
            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")

            if not '?page=' in url:
                total_pages_element = soup.find('div', {'id':"resumeVacancies"})
                if total_pages_element:
                    total_pages_element = total_pages_element.find('div', class_='col-auto caption')
                    if total_pages_element:
                        self.total_pages = int(total_pages_element.get_text().split()[-1])
            else:
                self.total_pages = 1
            
            # Find all the elements with class name 'base-card' which contain each job listing
            cards_list = soup.find('div', {'id':"filterSideBar"})
            # get cards
      
            if cards_list:
                self.cards.extend(cards_list.find_all('div', class_='card'))
            
            if self.total_pages > 1:
                numbered_pages = []
                for i in range(2, self.total_pages):
                    numbered_pages.append(f'https://www.infojobs.com.br/vagas-de-emprego-{self.job_keyword}-em-porto-alegre,-rs.aspx?page={i}')
            
                with ThreadPoolExecutor(max_workers=self.total_pages) as executor:
                    cards = executor.map(self.get_job_cards, numbered_pages)
            
            if len(self.cards)>self.card_num:
                return self.cards[0:self.card_num]
            return self.cards
        
        return self.cards
    
    
    def get_job_info(self, card):
        if self.timeout_event.is_set():
            return {}

        # Get the text content and href attribute of the title link element
        job_title_element = card.find('h2', class_='h3')
        if job_title_element is None:
            print('============== FAILED CARD ================')
            print(card)
            print('============ FAILED CARD END ==============')
            return None
        job_title = job_title_element.get_text(strip=True) if job_title_element else "Not specified"

        day_posted_element = card.find('div', class_='text-medium small')
        day_posted = day_posted_element.get_text(strip=True) if day_posted_element else "Not specified"

        job_url_element = card.find('div', class_='py-16')
        job_url = 'https://www.infojobs.com.br' + job_url_element['data-href'] if job_url_element else "Not specified"

        location_element = card.find('div', class_='small text-medium mr-24')
        location = location_element.get_text(strip=True) if location_element else "Not specified"

        job_desc = self.extractDescription(job_url)

        company_name_element = card.find('a', class_='text-body text-decoration-none')
        company_name = company_name_element.get_text(strip=True) if company_name_element else "Not specified"

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
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                description_page_info = {}
                html = res.content

                # Parse the HTML content using BeautifulSoup library (or any other method)
                soup = BeautifulSoup(html, "html.parser")
    
                # Find the element with class name 'description__text' which contains the job's description
                descriptionDiv = soup.find("div", class_="js_vacancyDataPanels")
      
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
            print('Totla infojobs Cards: ', len([crd for card in cards for crd in card]))
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
        time.sleep(220)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    infojobs = Infojobs(WEBSITE_URL, plavra, timeout_event)
    jobs = infojobs.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
