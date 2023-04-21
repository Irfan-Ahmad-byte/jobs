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

from jobs_Scraper import JobScraper

from concurrent.futures import ThreadPoolExecutor
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

class Jobs99Scraper(JobScraper):
    def parse_job_cards(self, soup: BeautifulSoup) -> List:
        print('===========>Getting cards for: ', url)
        res = requests.get(url, timeout=3)
        cards = []
        if res.status_code==200:
            time.sleep(.5)
            html = res.content
      
            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")

            # Find all the elements with class name 'base-card' which contain each job listing
            cards_list = soup.find('div', class_="opportunities-list")
      
            # get cards
      
            if cards_list:
                cards = cards_list.find_all('a', class_='opportunity-card')
        
        return cards
        
    def parse_job_info(self, card) -> dict:
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
    
            rating = rate_text(normalize_text(jobDesc['description']), self.keywords)
        
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
            
    def parse_job_description(self, card) -> dict:
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
            
            
    def main(self) -> List[dict]:
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards = executor.map(self.get_job_cards, self.urls)

            cards = list(cards)
            print('//////////////////////')
            print('Total 99jobs Cards:', len(*cards))
            print('//////////////////////')

            if len(cards) == 0:
                return []

            results = []

            for card_list in cards:
                if len(card_list) > 0:
                    root = sqrt(len(card_list))
                    workers = round(root) if root >= 1 and root > 10 else len(card_list)

                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        job_data = executor.map(self.parse_job_info, card_list)

                    results.extend(list(job_data))

            return results

        except Exception as e:
            print(e)
            return []

  

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

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))
   

  
