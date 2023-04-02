from scraper import *
from sentiment_classifier import *
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, RegexpTokenizer
from wordcloud import WordCloud
from contextlib import redirect_stdout
from PIL import Image

class teamData():
    def __init__(self, teamName:str, timeGap:int):
        self.team_name = teamName
        self.time_gap = timeGap
    
        self.data = []
        self.pos_words = {}
        self.neg_words = {}
        self.matchOdds = []

        # if team has a hashtag, search up hashtag in scraper rather than team name
        hashtag_dict = {'Man Utd':'#MUFC', 
                        'Leeds': '#LUFC',
                        'Newcastle':'#NUFC'}
        #'Liverpool':'#LFC', 'Man City':'#ManCity',
        if teamName in hashtag_dict:
            self.hashtag = hashtag_dict[teamName]
        else:
            self.hashtag = teamName
     
    def getSentimentDF(self, open=False):
        """
        Scrapes tweets, analyses sentiment and returns full dataframe
        Open: if set to True, will open an excel spreadsheet of dataframe
        """
        scraper = Scraper()
        SC = SentimentClassifier()
        tweets = scraper.findTweets(self.hashtag, 'Latest', self.time_gap, maxTweets=150)

        if not tweets:
            print('No Tweets Collected at this Time Interval')
            return pd.DataFrame()
        
        # make dataframe and label using the search subject
        dataframe, subject = scraper.tweetDF(tweets)[0], scraper.tweetDF(tweets)[1]
        
        # classify all tweets in dataframe by sentiment 
        sentiment_df = SC.scoresDF(dataframe)
        
        if open:
            print('Opening Excel of Sentiment Dataframe')
            SC.openDFExcel(sentiment_df, subject)
        
        # update the dictionaries of pos and neg adjectives
        self.pos_words.update(SC.pos_words)
        self.neg_words.update(SC.neg_words)

        return sentiment_df
    
    def getSentimentAverages(self, df, time) -> tuple:
        """
        Takes the sentiment dataframe and returns the average values of all sentiment columns
        """
        SC = SentimentClassifier()
        # datetime of data collection
        today = datetime.datetime.today()
        timestamp = datetime.datetime.strptime(time, "%H:%M")
        timestamp = timestamp.replace(year=today.year,month=today.month,day=today.day)
        
        # check if any data was collected in time gap 
        if SC.averagePolarity(df):
            print('Analysing Sentiment of Tweets Collected at %s' % timestamp)
            return (timestamp, SC.averagePolarity(df), SC.averageSentiment(df)['Avg Negative'], SC.averageSentiment(df)['Avg Positive'])
        else:
            print('No Tweets Collected in this Time Gap')
            return
    
    def overallSentiments(self) -> tuple:
        """
        Takes list of tuples of sentiment data and returns the overall averages for each sentiment
        """
        if len(self.data) == 0:
            print('No data')
            return
        polarities = []
        negatives = []
        positives = []
        for data_tuple in self.data:
            polarities.append(data_tuple[1])
            negatives.append(data_tuple[2])
            positives.append(data_tuple[3])
        
        overall_avg_polarity = sum(polarities)/len(polarities)
        overall_avg_negativity = sum(negatives)/len(negatives)
        overall_avg_positivity = sum(positives)/len(positives)
        
        # return the average of each list in tuple form
        return (overall_avg_polarity, overall_avg_negativity, overall_avg_positivity)
    
    def sentimentBarGraph(self, sentiment:str):
        style.use('ggplot')
        fig, ax = plt.subplots(figsize=(7.5, 1.75))
        fig.tight_layout(pad=3)

        if sentiment == 'n':
            colour_code = '#FF6961'
            i = 1
            sentiment_str = 'Negativity'
        elif sentiment == 'p':
            colour_code = '#33FFBD'
            i = 2
            sentiment_str = 'Positivity'

        ax.barh('b', self.overallSentiments()[i], align='center', color=colour_code)
        ax.get_yaxis().set_visible(False)
        plt.xlim(0,1)
        ax.set_title('Overall %s = %f' % (sentiment_str, np.round(self.overallSentiments()[i], decimals=3)))

    def polarityGraph(self):
        """
        Takes the tuple of data and returns polarity graph
        """
        if len(self.data) == 0:
            print('No Polarity Data')
            return
        
        x = []
        y = []
        for tuple in self.data:
            x.append(tuple[0])
            y.append(tuple[1])
        
        style.use('ggplot')
        plt.plot(x, y, "b-")
        plt.title('Polarity of Tweets - %s' % self.team_name)
        plt.xlabel('Time')
        plt.ylabel('Average Polarity')

    def negativeGraph(self):
        """
        Takes the tuple of data and returns polarity graph
        """
        if len(self.data) == 0:
            print('No Negativity Data')
            return
        
        x = []
        y = []
        for tuple in self.data:
            x.append(tuple[0])
            y.append(tuple[2])
        
        style.use('ggplot')
        plt.plot(x, y, color='r')
        plt.title('Negativity of Tweets - %s' % self.team_name)
        plt.xlabel('Time')
        plt.ylabel('Negative Sentiment')
    
    def positiveGraph(self):
        """
        Takes the tuple of data and returns polarity graph
        """
        if len(self.data) == 0:
            print('No Positivity Data')
            return
        
        x = []
        y = []
        for tuple in self.data:
            x.append(tuple[0])
            y.append(tuple[3])
        
        style.use('ggplot')
        plt.plot(x, y, color='g')
        plt.title('Positivity of Tweets - %s' % self.team_name)
        plt.xlabel('Time')
        plt.ylabel('Positive Sentiment')
    
    def makeWordCloud(self, word_dict:dict, sentiment:str):
        # set colour scheme
        if sentiment == 'p':
            cmap = 'Greens'
        elif sentiment == 'n':
            cmap = 'Reds'

        speech_bubble_mask = np.array(Image.open(r"C:\Users\oconn\OneDrive\Documents\bubble.png"))
        circle_mask = np.array(Image.open(r"C:\Users\oconn\OneDrive\Documents\circle.png"))
        
        # set parameters of word cloud
        wordcloud = WordCloud(width = 800, height = 800, mask=speech_bubble_mask, 
                    background_color ='white', relative_scaling=0.5, colormap=cmap)
        
        try:
            wordcloud.generate_from_frequencies(frequencies=word_dict)
        except ValueError:
            print('No words to make a word cloud')
            return


        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.tight_layout(pad=0)

    def saveData(self):
        """
        Writes data attributes of team to output file
        """
        output_file = "Output_Data_of_%s.txt" % self.team_name
        with open(output_file, mode='w', encoding="utf-8") as f:
            with redirect_stdout(f):
                print('---', self.team_name, '---')
                print('Data: ', self.data)
                print('Overall Sentiments: ', self.overallSentiments())
                print('Positive Words: ', self.pos_words)
                print('Negative Words: ', self.neg_words)
                print('Match Odds: ', self.matchOdds)

    def matchOddsGraph(self):
        """
        Takes the list of match odds data and returns a graph
        """
        x = []
        y = []
        for matchOdd in self.matchOdds:
            x.append(matchOdd[0])
            y.append(matchOdd[1])
        
        style.use('ggplot')
        plt.plot(x, y, color='m')
        plt.title('Match Odds of %s' % self.team_name)
        plt.ylim(0,100)
        plt.xlabel('Time')
        plt.ylabel('Odds')





        


        
