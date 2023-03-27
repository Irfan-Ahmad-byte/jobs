from sklearn.feature_extraction.text import TfidfVectorizer

def rate_test(plavra, text):
	# Create a TF-idf vectorizer object
	vectorizer = TfidfVectorizer()
	
	# Fit and transform the list of words and phrases and the description string into TF-idf matrices
	X = vectorizer.fit_transform(plavra + [description])
	
	# Get the feature names (words or phrases) from the vectorizer
	features = vectorizer.get_feature_names()
	
	# Get the TF-idf matrix for the description string (the last row of X)
	desc_tfidf = X[-1]
	
	# Initialize a variable to store the rating score
	rating = 0
	
	# Loop over the list of words and phrases
	for word in plavra:
  		# Get the index of the word or phrase in the feature names
  		index = features.index(word)
  		# Get the TF-idf score for the word or phrase in the description string
  		score = desc_tfidf[0, index]
  		# Add the score to the rating
  		rating += score

	# Print the rating score
	print(rating)
	
	return rating
