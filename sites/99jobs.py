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
from ../module.docsim import rate_text, normalize_text
from itertools import repeat
from math import sqrt

from concurrent.futures import ThreadPoolExecutor
import os
import requests
import json
import re
import time
import random
import logging
import unicodedata


class Jobs99:
    def __init__(self, urls:list, palavras):
        self.urls = ulrs
        self.palavras = palavras
        
    def get_cards(self, url):
        res = requests.get(url)
        cards = []
        if res.status_code==200:
            time.sleep(1)
            html = res.content
      
            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")

            # Find all the elements with class name 'base-card' which contain each job listing
            cards_list = soup.find('div', class_="opportunities-list")
      
            # get cards
      
            if cards_ul:
                cards = cards_list.find_all('a', class_='opportunity-card')
        
        return cards
    
    
    def get_job_info(self, card, plavras):
        # Get the text content and href attribute of the title link element
        jobTitle = None
    
        jobURL = card['href']
        try:
            location = card.find('div', class_='opportunity-address').text.strip()
        except:
            location = 'location not given'

        jobDesc = extractDescription(jobURL)
  
        # Get the text content of the company link element
        try:
            companyName = card.find('div', class_='opportunity-company-infos').find("h2").text.strip()
        except:
            companyName = 'Not specified'
    
        jobTitle = jobDesc['job_title']
        # Get the text content of the date span element
        dayPosted = jobDesc['days_ramained']
    
        rating = rate_text(normalize_text(jobDesc['description']), plavras)
        
        job = {
          "jobTitle": jobTitle,
          "companyName": companyName,
          "dayPosted": dayPosted,
           "jobURL": jobURL,
           'rating': rating,
          'location': location,
          'jobDesc': jobDesc['description']
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
  
        description_page_info = {}
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
                descriptionDiv = soup.find("div", class_="opportunities-details")
      
                side_bar = soup.find('div', class_='details')
                # job title
                job_title = side_bar.find('h2').text.strip()
      
                # days
                days = side_bar.find('div', class_='subscription-btn').find('div', class_='.progress').text.strip()
      
                # Call the parseDescription function on this element and get the result dictionary
    
                time.sleep(0.5)
                # Get the text content of the element
                if descriptionDiv is not None:
                    description = descriptionDiv.text.strip()
                else:
                    description = 'no description specified'

                # Add the complete description to result dictionary
                description_page_info['description'] = normalize_text(description)
                description_page_info['job_title'] = normalize_text(description)
                description_page_info['days_ramained'] = normalize_text(description)

        except Exception as e:
            print('Error while getting job description: %s, %s', str(e), url)

        #print('Finished getting job description from %s', url)

        # Return result dictionary 
        return description_page_info
        
    def main():
        
        results = []
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
                if len(card)>0:
                    time.sleep(2)
                    if sqrt(len(card)) >=1:
                    workers = round(sqrt(len(card)))
                else:
                    workers = 1
                
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    job_data = executor.map(self.get_job_info, card, repeat(self.palavras))
      
                results.extend(list(job_data))
    
            total_cards = len(results)
    
        #    for job in job_data_list:
         #     results.append(job)
      
            return [results, total_cards]
  
        except Exception as e:
            print(e)
            return [[], 0]
  

if __name__ == '__main__':
    WEBSITE_URL = 'https://99jobs.com/opportunities/filtered_search?utf8=%E2%9C%93&utm_source=tagportal&utm_medium=busca&utm_campaign=home&utm_id=001&search%5Bterm%5D=Engenharia'
    
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
	
    jobs99 = Jobs99([WEBSITE_URL], plavra)
    jobs = jobs99.main()

    for job in jobs:
        print(job)
   

  
