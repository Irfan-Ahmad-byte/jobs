"""
This module provides a function to calculate a rating score for a given text based on the occurrence of words or phrases
in a list using Term Frequency (TF). The rating is normalized by dividing it by the maximum possible term frequency for
the words in the list within the text and then scaled between 0 and 5.

Developer: Irfan Ahmad (devirfan.mlka@gmail.com / https://irfan-ahmad.com)
Project Owner: Monica Piccinini (monicapiccinini12@gmail.com)
"""



from sklearn.feature_extraction.text import CountVectorizer

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
    
    # Create a CountVectorizer object
    vectorizer = CountVectorizer()

    # Fit and transform the list of words and phrases and the description string into term frequency matrices
    X = vectorizer.fit_transform(plavra + [text])

    # Get the feature names (words or phrases) from the vectorizer
    features = vectorizer.get_feature_names_out()

    # Get the term frequency matrix for the description string (the last row of X)
    desc_tf = X[-1]

    # Initialize a variable to store the rating score
    rating = 0

    # Loop over the list of words and phrases
    for i, word in enumerate(plavra):
        # Get the term frequency for the word or phrase in the description string
        score = desc_tf[0, i]
        # Add the score to the rating
        rating += score

    # Calculate the total frequency of words in the text
    total_frequency = sum(desc_tf[0, i] for i in range(len(features)))

    # Normalize the rating by dividing it by the total frequency of words in the text
    normalized_rating = rating / total_frequency if total_frequency != 0 else 0

    # Scale the rating to be between 0 and 5
    scaled_rating = normalized_rating * 5

    # Print the scaled rating score
    print(scaled_rating)

    return scaled_rating


