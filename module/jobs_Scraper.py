from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from typing import List

class JobScraper(ABC):
    def __init__(self, urls: List[str], keywords: List[str]):
        self.urls = urls
        self.keywords = keywords

    def fetch_job_cards(self, url: str):
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            html = response.content
            soup = BeautifulSoup(html, "html.parser")
            return self.parse_job_cards(soup)
        return []

    @abstractmethod
    def parse_job_cards(self, soup: BeautifulSoup) -> List:
        pass

    @abstractmethod
    def parse_job_info(self, card) -> dict:
        pass
        
    @abstractmethod
    def parse_job_description(self, card) -> dict:
        pass

    def scrape_jobs(self):
        results = []
        for url in self.urls:
            cards = self.fetch_job_cards(url)
            for card in cards:
                job_info = self.parse_job_info(card)
                results.append(job_info)
        return results



