from scraper import *
from sentiment_classifier import *

scraper = Scraper()

subject = input("SUBJECT:\n>>> ")

category = input("Top / Latest:\n>>> ")
if category == 'Latest':
    time_gap = int(input("How recent? (mins):\n>>> "))
    tweets = scraper.findTweets(subject, category, time_gap, maxTweets=50)
else:
    tweets = scraper.findTweets(subject, category, maxTweets=50)


tweet_dataframe_and_subject = scraper.tweetDF(tweets)
dataframe = tweet_dataframe_and_subject[0]
subject = tweet_dataframe_and_subject[1]

print('Subject: ', subject)
print('Dataframe: \n', dataframe)

tweet_file = "C:/Users/oconn/OneDrive/Documents/Twitter-Data/%s_tweets.xlsx" % subject.replace(' ', '')
dataframe.to_excel(tweet_file, index=False)
os.system('start "excel" %s' % tweet_file)

# ------------------

SC = SentimentClassifier()
sentiment_dataframe = SC.scoresDF(dataframe)

SC.openDFExcel(sentiment_dataframe, subject)
