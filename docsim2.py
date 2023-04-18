import re

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
    word_count = {}
    for word in words:
        word_count[word] = word_count.get(word, 0) + 1

    # Calculate the number of times each plavra word appears in the text
    plavra_text_count = {word:word_count.get(word.lower(), 0) for word in plavra}

    # Calculate the cumulative sum for all words in the plavra list
    sum_plavra_text_count = sum(plavra_text_count.values())
    
    # restructure palavra such that each matched word of palavra is filled in palavra its total count in text
    # for example if a palavra word 'melhor' has a plavra_text_count = 12 it means this word appeared 12 in the text
    # so now refill this word 'melhor' 11 times again in the palavra list so that now the plavra list has 12 words of 'melhor'
    # this way we'll calculate the ratio of matched words of text and palavra by dividing the sum of matched words by total
    # words in palavra and multiplying with 100
    
    # for each word in text
    for word in plavra_text_count:
        # if that had a match in palavra
        if plavra_text_count[word] > 0:
            # add that word in the palavra one less the number of times it appeared in the text
            plavra.extend([word]*(plavra_text_count[word]-1))
    

    # Calculate the number of words in the list plavra
    plavra_count = len(plavra)
    
    # get the %age of words that matched in palavra and text
    percentage_match = (sum_plavra_text_count/plavra_count)*100

    # Print the values for plavra_count, text_count, plavra_text_count, and sum_plavra_text_count
    #print(f"plavra_count: {plavra_count}, plavra_text_count: {plavra_text_count}, sum_plavra_text_count: {sum_plavra_text_count}, percentage match: {percentage_match}")

    return percentage_match

