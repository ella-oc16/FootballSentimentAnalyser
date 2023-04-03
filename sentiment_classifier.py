from transformers import AutoModelForSequenceClassification
from transformers import TFAutoModelForSequenceClassification
from transformers import AutoTokenizer
from scipy.special import softmax
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import pandas as pd
import os
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, RegexpTokenizer

class SentimentClassifier():
    def __init__(self):
        # pretrained Roberta sentiment model:
        MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"
        # set-up tokenizer and model using model
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL)

        # use VADER model to get sentiment intensity
        self.sia = SentimentIntensityAnalyzer()

        self.pos_words = {}
        self.neg_words = {}

    
    def preprocess(self, text):
        """
        Preprocesses text (username and link placeholders) for Roberta
        """
        new_text = []
        for t in text.split(" "):
            t = '@user' if t.startswith('@') and len(t) > 1 else t
            t = 'http' if t.startswith('http') else t
            new_text.append(t)
        return " ".join(new_text)
    
    
    def extractText(self, text):  
        """
        Removes hyperlinks and hashtags for VADER
        """
        result = re.sub("http\S+", "", text)
        result = re.sub("#\S+", "", result)
        result = re.sub("@\S+", "", result)
        return result


    def getScores(self, text) -> dict:
        """
        Returns a dictionary of sentiment scores from both VADER and Roberta model
        """
        scores_dict = {}
        
        vader_scores = self.sia.polarity_scores(text)
        scores_dict['V Negative'] = vader_scores['neg']
        scores_dict['V Neutral'] = vader_scores['neu']
        scores_dict['V Positive'] = vader_scores['pos']
        
        # find the polarity score for each sentence in passage and then get mean
        averages = []
        sentences = nltk.sent_tokenize(self.extractText(text))
        for sentence in sentences:
            polarity_score = self.sia.polarity_scores(sentence)  
            averages.append(polarity_score["compound"])  
        if len(averages) == 0:
            scores_dict['V Polarity'] = 0
        else:
            mean = sum(averages)/len(averages)
            scores_dict['V Polarity'] = mean
   
        text = self.preprocess(text)
        encoded_input = self.tokenizer(text, return_tensors='pt')
        output = self.model(**encoded_input)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)

        for i in range(len(scores)):
            if i == 0:
                scores_dict['Classification'] = 'Negative'
                max_score = scores[i]
                scores_dict['R Negative'] = scores[i]
            elif i == 1:
                scores_dict['R Neutral'] = scores[i]
                if scores[i] > max_score:
                    scores_dict['Classification'] = 'Neutral'
                    max_score = scores[i]
            else:
                scores_dict['R Positive'] = scores[i]
                if scores[i] > max_score:
                    scores_dict['Classification'] = 'Positive'
                    max_score = scores[i]

        # get adjective frequency for this tweet's text and append to overall adjective frequency dictionaries
        self.frequencyAdjectives(text, scores_dict['Classification'])

        return scores_dict
    

    def scoresDF(self, df):
        """
        Finds the sentiment scores dict for each tweet in the tweets dataframe
        Produces a scores dataframe from scores dicts and merges it with tweet dataframe
        """
        df = df.reset_index().rename(columns={'index': 'Index'})

        results = {}
        for i, row in df.iterrows():
            text = row['TweetContent']
            myid = i
            results[myid] = self.getScores(text)
        
        scores_df = pd.DataFrame(results).T
        scores_df = scores_df.reset_index().rename(columns={'index': 'Index'})
        scores_df = scores_df.merge(df, how='left')
        
        return scores_df
    

    def openDFExcel(self, df, subject):
        """
        Opens a dataframe in excel with the subject of the tweets in filename
        """
        subject = subject.replace(' ', '')
        filename = "C:/Users/oconn/OneDrive/Documents/Twitter-Data/%s_sentiment.xlsx" % subject
        df.to_excel(filename, index=False)
        os.system('start "excel" %s' % filename)

    
    def averageSentiment(self, df) -> dict:
        """
        Returns a dictionary with the average sentiment scores of the entire df
        """
        neg = []
        pos = []
        neu = []
        for i, row in df.iterrows():
            neg.append(row['R Negative'])
            pos.append(row['R Positive'])
            neu.append(row['R Neutral'])
        
        if len(neg) == 0:
            return

        avg_neg = sum(neg)/len(neg)
        avg_pos = sum(pos)/len(pos)
        avg_neu = sum(neu)/len(neu)
        return {'Avg Negative':avg_neg, 'Avg Positive':avg_pos, 'Avg Neutral':avg_neu}
    

    def averagePolarity(self, df):
        """
        Returns the average polarity of an entire df
        """
        tot = []
        for i, row in df.iterrows():
            tot.append(row['V Polarity'])
        if len(tot) == 0:
            return
        return sum(tot)/len(tot)
    
    
    def frequencyAdjectives(self, text, classification) -> None:
        """
        Appends words from an individual tweet to overall dictionary of adjectives and their frequencies
        """
        tokenizer = RegexpTokenizer(r'\w+')
        stop_words = list(stopwords.words('english'))
        word_pit = tokenizer.tokenize(self.extractText(text))

        # assign a tag to each word in word pit (tag 'JJ' means adjective)
        tags = nltk.pos_tag(word_pit)
        #print(tags)

        banned_adjectives = ['http', 'like']

        for word in tags:
            if word[0] in self.pos_words:       # increment frequency count of word
                self.pos_words[word[0]] += 1
                continue
            elif word[0] in self.neg_words:     # increment frequency count of word
                self.neg_words[word[0]] += 1
                continue
            if len(word[0]) < 3:                # word too short, do not add
                continue
            if word[0].lower() in stop_words or word[0].lower() in banned_adjectives:   
                continue
            if word[1] in ['JJ']:
                if classification == 'Positive': 
                    self.pos_words[word[0].lower()] = 1
                elif classification == 'Negative':
                    self.neg_words[word[0].lower()] = 1


"""
SC = SentimentClassifier()

#SC.frequencyAdjectives('Today is a rainy day', 'Positive')



examples = ["What a goal!", 
            "Get In!",
            "Harry Kane is a legend",
            "Rashford's on fire!"]

for example in examples:
    scores = SC.getScores(example)
    print(example)
    print(scores)
    print('\n')

"""

    


