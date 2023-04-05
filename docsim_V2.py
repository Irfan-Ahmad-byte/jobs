"""
This module provides a function to calculate a rating score for a given text based on the occurrence of words or phrases
in a list using Term Frequency (TF). The rating is normalized by dividing it by the maximum possible term frequency for
the words in the list within the text and then scaled between 0 and 5.

Developer: Irfan Ahmad (devirfan.mlka@gmail.com / https://irfan-ahmad.com)
Project Owner: Monica Piccinini (monicapiccinini12@gmail.com)
"""



from collections import Counter
import re

def rate_text(plavra, text):
    """
    Calculate a rating score for a given text based on the occurrence of words or phrases in plavra using cumulative frequency.

    The rating is normalized by dividing it by the total frequency of words in the text, and then scaled between 0 and 5.

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

    # Calculate the total frequency of words in the text
    total_frequency = sum(word_count.values())

    # Initialize a variable to store the rating score
    rating = 0

    # Loop over the list of words and phrases
    for word in plavra:
        # Convert the word to lowercase
        word = word.lower()

        # Get the frequency for the word in the description string
        score = word_count[word]

        # Add the score to the rating
        rating += score

    # Normalize the rating by dividing it by the total frequency of words in the text
    normalized_rating = rating / total_frequency if total_frequency != 0 else 0

    # Scale the rating to be between 0 and 5
    scaled_rating = normalized_rating * 5

    # Print the scaled rating score
    print(scaled_rating)

    return scaled_rating


