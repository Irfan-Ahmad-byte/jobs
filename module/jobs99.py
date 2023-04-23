"""
https://99jobs.com/

"""

'''
URL = 'https://99jobs.com/opportunities/filtered_search?utf8=%E2%9C%93&utm_source=tagportal&utm_medium=busca&utm_campaign=home&utm_id=001&search%5Bterm%5D=Engenharia+Ambiental&search%5Bstate%5D=2&search%5Bcity%5D%5B%5D=Acrel%C3%A2ndia
'
'''
'''
cards_element = 'a, .opportunity-card>div, .opportunity-card-content'
location = cards_element > 'div, .opportunity-address'
company = cards_element > 'div, .opportunity-card-footer>div, .opportunity-company-infos>h2 '
rating = rate_text(description, palavra)
jobtitle = 'div, .details>h2' OR 'div, #sidebar>h2'
description_url = 'a, .opportunity-card[href]'

palavra = palavras_list
description = 'div .opportunity-company-infos> div list[.row]'.text
days = 'div, .details>div, .subscription-btn>div, .progress' OR 'div, #sidebar>div, .subscription-btn>div, .progress'
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

class Jobs99:
    def __init__(self, urls:list, palavras, timeout_event: Event, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.timeout_event = timeout_event
        self.card_num = card_num
        
        self.total_jobs = 0
        self.total_pages = 1
        
        self.page_index = 1
        
        self.cards = []
        
    def get_job_cards(self, url):
        if self.timeout_event.is_set():
            return []
            
        print('===========>Getting cards for: ', url)
        res = requests.get(url, timeout=3)
        if res.status_code==200:
            time.sleep(.5)
            html = res.content
      
            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")
            
            if not '?page=' in url:
                total_jobs_element = soup.find('span', {'id'="text-total-opportunities"})
                if total_jobs_element:
                    self.total_jobs = total_jobs_element.text.strip()
            else:
                self.total_pages = 1
                
            self.total_pages = self.total_jobs / 20
            
            # Find all the elements with class name 'base-card' which contain each job listing
            cards_list = soup.find('div', class_="opportunities-list")
            # get cards
            if cards_list:
                self.cards = cards_list.find_all('a', class_='opportunity-card')
            
            if self.total_pages> 1:
                numbered_pages = []
                for i in range(2, self.total_pages):
                    numbered_pages.append(f'https://99jobs.com/opportunities/filtered_search/search_opportunities?page={i}&search%5Bterm%5D={url.split("=")[-1]}&')
                    
                with ThreadPoolExecutor(max_workers=self.total_pages) as executor:
                    cards = executor.map(self.get_job_cards, numbered_pages)

                
            if len(cards)>self.card_num:
                return self.cards[0:self.card_num]
        
        return self.cards
    
    
    def get_job_info(self, card):
        if self.timeout_event.is_set():
            return {}
        # Get the text content and href attribute of the title link element
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
  
        # Get the text content of the company link element
        try:
            companyName = card.find('div', class_='opportunity-company-infos').find("h2").text.strip()
        except:
            companyName = 'Not specified'
        
        if jobDesc is not None:
            jobTitle = jobDesc['job_title']
            # Get the text content of the date span element
            dayPosted = jobDesc['days_ramained']
    
            rating = rate_text(normalize_text(jobDesc['description']), self.palavras)
        
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
                description_page_info = {}
                html = res.content

                # Parse the HTML content using BeautifulSoup library (or any other method)
                soup = BeautifulSoup(html, "html.parser")
    
                # Find the element with class name 'description__text' which contains the job's description
                descriptionDiv = soup.find("div", class_="opportunities-details")
      
                side_bar = soup.find('div', class_='details')
                # job title
                job_title = side_bar.find('h2').text.strip()
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
                    description = 'no description specified'

                # Add the complete description to result dictionary
                description_page_info['description'] = normalize_text(description)
                description_page_info['job_title'] = normalize_text(job_title)
                description_page_info['days_ramained'] = days
                
                return description_page_info

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
            print('Totla 99jobs Cards: ', len([crd for card in cards for crd in card]))
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
    WEBSITE_URL = 'https://99jobs.com/opportunities/filtered_search?utf8=%E2%9C%93&utm_source=tagportal&utm_medium=busca&utm_campaign=home&utm_id=001&search%5Bterm%5D=software%20engineer&search%5Bstate%5D=8&search%5Bcity%5D%5B%5D=Bras%C3%ADlia'
    
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
        time.sleep(3)
        timeout_event.set()

    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    jobs99 = Jobs99([WEBSITE_URL], plavra, timeout_event)
    jobs = jobs99.main()

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
