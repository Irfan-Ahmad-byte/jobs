'''
not implemented yet
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
from requests_html import HTMLSession
import json
import re
import time
import random
import logging
import unicodedata


headers = {'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'}

class Indeed:
    def __init__(self, urls:list, palavras, timeout_event: Event, card_num=10):
        self.urls = urls
        self.palavras = palavras
        self.timeout_event = timeout_event
        self.card_num = card_num
        
    def get_job_cards(self, url):
        """
        Fetches the HTML content from a LinkedIn jobs search URL and returns a list of job cards as BeautifulSoup objects.
        
        Args:
            url (str): A LinkedIn job search URL.
        
        Returns:
            List[bs4.element.Tag]: A list of job cards as BeautifulSoup objects.
        """
        
        if self.timeout_event.is_set():
            return []
        print('===========>Getting cards for: ', url)
        
        time.sleep(random.uniform(1,5))
        session = HTMLSession()
        res = session.get(url)
        cards = []
        if res.status_code==200:
            time.sleep(1)
            html = res.html    

            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")

            # Find all the elements with class name 'base-card' which contain each job listing
            cards_ul = soup.find('ul', class_="jobsearch-ResultsList")
        
        
            if cards_ul:
                cards = cards_ul.find_all('li')
            else:
                try:
                    cards = soup.find_all('li')
                except:
                    ...
            return cards
        else:
            print('status returned: ', res.status_code)
                
        return cards
        
    
    def get_job_info(self, card):
        """
          Extracts job information from a BeautifulSoup card object and a list of keywords (plavras).
          
          Args:
              card (bs4.element.Tag): A BeautifulSoup object representing a single job card.
              plavras (List[str]): A list of keywords to rate the job.
          
          Returns:
              dict: A dictionary containing job title, company name, day posted, job URL, rating, location, and job description.
        """
        
        if self.timeout_event.is_set():
            return {}

        # Get the text content and href attribute of the title link element
        jobTitle_element = card.find("h2", class_="jobTitle")
        
        if not jobTitle:
            return
        else:
            jobTitle = jobTitle_element.text.strip()
            
        data_jk = jobTitle_element.find("a")['data-jk']
        data_tk = jobTitle_element.find("a")['data-mobtk']
        jobURL = f'https://br.indeed.com/viewjob?jk={data_jk}&tk={data_tk}&from=serp&vjs=3'
        try:
            location = card.find("div", class_='companyLocation').text.strip()
        except:
            location = 'location not given'

        jobDesc = self.extractDescription(jobURL)
        
        # Get the text content of the company link element
        try:
            companyName = card.find("span", class_='companyName').text.strip()
        except:
            companyName = 'Not specified'

        # Get the text content of the date span element
        try:
            dayPosted_element = card.find("span", class_='date')
            extract_element = dayPosted_element.find("span", class_='visually-hidden')
            if extract_element:
                extract_element.extract()
            
            dayPosted = dayPosted_element.text.strip()
        except:
            dayPosted = False
          
        if jobDesc:
            rating = rate_text(normalize_text(jobDesc), self.palavras)
              
            job = {
                "jobTitle": jobTitle,
                "companyName": companyName,
                "dayPosted": dayPosted,
                "jobURL": jobURL,
                'rating': rating,
                'location': location
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
        if self.timeout_event.is_set():
            return None
        
        description = None
        # Create an empty dictionary to store the result

        # Fetch the HTML content from the URL using requests library (or any other method)
        #logging.info('Getting job description from %s', url)
        try:
          time.sleep(random.uniform(1,3))
          session = HTMLSession()
          res = session.get(url)
          if res.status_code == 200:
            html = res.content

            # Parse the HTML content using BeautifulSoup library (or any other method)
            soup = BeautifulSoup(html, "html.parser")
          
            # Find the element with class name 'description__text' which contains the job's description
            descriptionDiv = soup.find("div", class_="jobDescriptionText")
            
            # Call the parseDescription function on this element and get the result dictionary
          
            time.sleep(0.5)
            # Get the text content of the element
            if descriptionDiv is not None:
              description = normalize_text(descriptionDiv.text.strip())
            else:
              description = None

        except Exception as e:
          print('Error while getting job description: %s, %s', str(e), url)

        #print('Finished getting job description from %s', url)

        # Return result dictionary 
        return description
        
    def main(self):
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                cards_list = executor.map(self.get_job_cards, self.urls)
                
            cards = [crd for card in cards_list for crd in card]
          
            if len(cards) ==0:
                return [[], 0]

            if len(cards)>self.card_num:
                return cards[0:self.card_num]

            # Loop through each card element and extract the relevant information
            #results = [get_job_info(card, plavras) for card in cards]
            results = []
            
            jobs_data_list = []
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                job_data = executor.map(self.get_job_info, cards)
                
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
  try:
    start_time = time.time()
    url_list = [
        'https://uk.indeed.com/jobs?q=software+engineer&l=Rio+Branco%2C+AC&vjk=8a2f88b3be1d9e78',
        'https://uk.indeed.com/jobs?q=software+engineer&l=&vjk=82eca8fdfb93d010'
    ]

    timeout_event = Event()
    # Start the timeout thread before calling the extractJobs function
    def stop_extraction():
        time.sleep(90)
        timeout_event.set()
        
    extraction_thread = Thread(target=stop_extraction)
    extraction_thread.start()
    
    indeed = Indeed(url_list, plavra, timeout_event)
    jobs = indeed.main()

    elapsed_time = time.time() - start_time

    print('=+=+=+=+=+=+=+=+==+=+=+=++==+==++=+==+=+=+=+=+=+=+=+=+=+==+=+=+')
    print(json.dumps(jobs, indent=2))

    
    
    for res in jobs[0]:
      print(res['rating'])
      
    print(f"Time taken to extract job description: {elapsed_time:.2f} seconds")
  except Exception as e:
    logging.error('Error while running the application: %s', str(e))
	   

  
