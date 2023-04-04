from sklearn.feature_extraction.text import CountVectorizer

def rate_text(plavra, text):
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

    # Calculate the maximum possible term frequency for the words in plavra within the text
    max_term_frequency = sum(desc_tf[0, i] for i in range(len(features)))

    # Normalize the rating by dividing it by the maximum term frequency
    normalized_rating = rating / max_term_frequency if max_term_frequency != 0 else 0

    # Scale the rating to be between 0 and 5
    scaled_rating = normalized_rating * 5

    # Print the scaled rating score
    print(scaled_rating)

    return scaled_rating

