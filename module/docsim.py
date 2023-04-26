"""
This module provides utility functions for text processing and date manipulation.

The main functions are:
1. normalize_text(text): Normalize a given text using the NFC Unicode normalization form.
2. date_category(date_str): Determine the date category for a given date string in Portuguese format.
3. rate_text(text, plavra): Calculate a rating score for a given text based on the cumulative frequency of words in a list within the text.

Developer: Irfan Ahmad, devirfan.mlka@gmail.com
Project Owner: Monica Piccinini, monicapiccinini12@gmail.com
"""


import re
import unicodedata
from datetime import datetime, timedelta, date
from dateutil import parser


def normalize_text(text):
    """
    Normalize the input text using the NFC Unicode normalization form.
    
    Parameters:
    text (str): The input text to be normalized.
    
    Returns:
    str: The normalized text.
    """
    return unicodedata.normalize('NFC', text)

def date_category(date_str: str) -> str:
    """
    Determine the date category for a given date string.
    
    The input date string should contain a date in Portuguese format.
    The date category is determined based on the difference between the current date and the input date.
    
    Parameters:
    date_str (str): The input date string in Portuguese format.
    
    Returns:
    str: The date category as a string representation of seconds ("86400", "604800", "2592000", or "25920000").
    """
    # Dictionary to map Portuguese month abbreviations to month numbers
    pt_month_abbr = {
        'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04',
        'mai': '05', 'jun': '06', 'jul': '07', 'ago': '08',
        'set': '09', 'out': '10', 'nov': '11', 'dez': '12',
        'ontem': (date.today() - timedelta(days=1)).strftime('%d/%m/%y')
    }

    # Replace the Portuguese month abbreviation in the input date string
    for abbr, number in pt_month_abbr.items():
        date_str = date_str.lower().replace(abbr, number)

    # Parse the input date string
    try:
        input_date = parser.parse(date_str, dayfirst=True, yearfirst=False)
    except ValueError:
        return "Invalid date format"

    # Set the date's year to the current year if it's missing
    if input_date.year == 1900:
        input_date = input_date.replace(year=datetime.now().year)

    # Calculate the difference between the current date and the input date
    delta = datetime.now() - input_date

    if delta <= timedelta(hours=24):
        return "86400"
    elif delta <= timedelta(days=7):
        return "604800"
    elif delta <= timedelta(days=30):
        return "2592000"
    else:
        return "25920000"

def rate_text(text, plavra=False):
    """
    Calculate a rating score for a given text based on the cumulative frequency of words in plavra within the text.

    The rating is normalized by dividing it by the product of plavra_count and text_count, and then scaled between 0 and 5.

    Parameters:
    text (str): The input text to be rated.
    plavra (list): A list of words or phrases to rate the input text.

    Returns:
    dict: A dictionary containing various counts and the final rating.
    """
    rating = 0

    # Check if there are any plavras for the user
    if not plavra:
        return rating
    
    plavra = normalize_text(' '.join(plavra)).split(' ')

    # Convert the text to lowercase
    text = normalize_text(text.lower())

    # Tokenize the text by splitting it into words using regex
    words = re.findall(r'\b\w+\b', text)
    
        # Count the occurrences of words in the text
    word_count = {}
    for word in words:
        word_count[word] = word_count.get(word, 0) + 1

    # Calculate the number of times each plavra word appears in the text
    plavra_text_count = [word_count.get(normalize_text(word.lower()), 0) for word in plavra]

    # Calculate the cumulative sum for all words in the plavra list
    sum_plavra_text_count = sum(plavra_text_count)

    # Calculate the number of words in the list plavra
    plavra_count = len(plavra)

    # Calculate the number of words in the text
    text_count = len(words)

    # Normalize the rating by dividing it by the product of plavra_count and text_count
    normalized_rating = sum_plavra_text_count / (plavra_count * text_count) if plavra_count * text_count != 0 else 0

    # Scale the rating to be between 0 and 5
    scaled_rating = round(normalized_rating * 1000, 4)

    # Return the values for plavra_count, text_count, plavra_text_count, and sum_plavra_text_count
    return {'plavra_count': plavra_count, 'text_count': text_count, 'plavra_text_count': plavra_text_count, 'sum_plavra_text_count': sum_plavra_text_count, 'rating': scaled_rating}


