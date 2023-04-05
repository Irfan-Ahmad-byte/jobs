import re
from collections import Counter

def rate_text(plavra, text):
    """
    Calculate a rating score for a given text based on the cumulative frequency of words in plavra within the text.

    The rating is normalized by dividing it by the sum of cumulative frequencies of words in plavra, and then scaled between 0 and 5.

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

    # Calculate the cumulative frequency of words in plavra within the text
    cumulative_frequency = sum(word_count[word.lower()] for word in plavra)

    # Calculate the sum of cumulative frequencies of words in plavra
    sum_cumulative_frequencies = sum(word_count.values())

    # Normalize the rating by dividing it by the sum of cumulative frequencies of words in plavra
    normalized_rating = cumulative_frequency / sum_cumulative_frequencies if sum_cumulative_frequencies != 0 else 0

    # Scale the rating to be between 0 and 5
    scaled_rating = normalized_rating * 5

    # Print the scaled rating score
    print(scaled_rating)

    return scaled_rating

