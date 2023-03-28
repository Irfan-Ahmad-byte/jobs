from sklearn.feature_extraction.text import TfidfVectorizer

def rate_text(plavra, text):
	# Create a TF-idf vectorizer object
	vectorizer = TfidfVectorizer()
	
	# Fit and transform the list of words and phrases and the description string into TF-idf matrices
	X = vectorizer.fit_transform(plavra + [text])
	
	# Get the feature names (words or phrases) from the vectorizer
	features = vectorizer.get_feature_names_out()
	
	# Get the TF-idf matrix for the description string (the last row of X)
	desc_tfidf = X[-1]
	
	# Initialize a variable to store the rating score
	rating = 0
	
	# Loop over the list of words and phrases
	for i, word in enumerate(plavra):
  		# Get the TF-idf score for the word or phrase in the description string
  		score = desc_tfidf[0, i]
  		# Add the score to the rating
  		rating += score

	# Print the rating score
	print(rating)
	
	return rating
