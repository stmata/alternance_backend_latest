import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download NLTK resources if not already done
nltk.download('stopwords')
nltk.download('wordnet')


class TextPreprocessor:
    def __init__(self, language='french'):
        """
        Initializes the text preprocessor with specified language.
        
        :param language: The language for stopwords (default 'french').
        """

        self.stop_words = set(stopwords.words(language))
        self.lemmatizer = WordNetLemmatizer()

    def clean_text(self, text):
        """
        Cleans the text by removing stopwords, special characters, and excess whitespace.
        
        :param text: The text to clean.
        :return: The cleaned text.
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove special characters and hashtags
        text = re.sub(r'\@w+|\#', '', text)
        # Remove digits
        text = re.sub(r'\d+', '', text)
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Convert to lowercase
        text = text.lower()
        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove stopwords and lemmatize
        words = text.split()
        cleaned_text = ' '.join([self.lemmatizer.lemmatize(word) for word in words if word not in self.stop_words])
        return cleaned_text
