import re
import unicodedata


def normalize_text(text):
    return unicodedata.normalize('NFC', text)
    

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
    scaled_rating = normalized_rating * 5

    # Print the values for plavra_count, text_count, plavra_text_count, and sum_plavra_text_count
    print(f"plavra_count: {plavra_count}, text_count: {text_count}, plavra_text_count: {plavra_text_count}, sum_plavra_text_count: {sum_plavra_text_count}")

    return {'plavra_count': plavra_count, 'text_count': text_count, 'plavra_text_count': plavra_text_count, 'sum_plavra_text_count': sum_plavra_text_count, 'rating': scaled_rating}

