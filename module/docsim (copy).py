import re
from collections import Counter

def rate_text(plavra, text):
    """
    Calculate a rating score for a given text based on the cumulative frequency of words in plavra within the text.

    The rating is normalized by dividing it by the product of plavra_count and text_count, and then scaled between 0 and 5.

    Parameters:
    plavra (list): A list of words or phrases to rate the input text.
    text (str): The input text to be rated.

    Returns:
    float: The rating score between 0 and 5, where 0 indicates no relevance and 5 indicates maximum relevance.
    """

    # Convert the text to lowercase
    text = text.lower()

    # Tokenize the text by splitting it into words using regex
    words = re.findall(r'\b\w+\b', text)

    # Count the occurrences of words in the text
    word_count = Counter(words)

    # Calculate the number of words in plavra
    plavra_count = len(plavra)

    # Calculate the number of words in the text
    text_count = len(words)

    # Calculate the number of times each plavra word appears in the text
    plavra_text_count = [word_count[word.lower()] for word in plavra]

    # Calculate the cumulative sum for all words in plavra list
    sum_plavra_text_count = sum(plavra_text_count)

    # Normalize the rating
    normalized_rating = sum_plavra_text_count / (plavra_count * text_count) if plavra_count * text_count != 0 else 0

    # Scale the rating to be between 0 and 5
    scaled_rating = normalized_rating * 5


    return scaled_rating, plavra_count, text_count, plavra_text_count, sum_plavra_text_count





