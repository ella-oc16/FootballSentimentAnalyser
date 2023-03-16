from getpass import getpass
from time import sleep
import pandas as pd
import os

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.by import By

class Scraper:
    def __init__(self):
        self.PATH = "C:/Users/oconn/Downloads/edgedriver_win64/msedgedriver.exe"

    def getTweetData(self, article):
        """
        extract the data from an article on scroll page
        return info in a tuple
        """
        TweetContent = article.find_element(By.XPATH,".//div[@data-testid='tweetText']").text
        # if spam is detected, do not return the tweet
        if self.spamDetector(TweetContent):
            return
        
        Reply = article.find_element(By.XPATH,".//div[@data-testid='reply']").text
        Retweet = article.find_element(By.XPATH,".//div[@data-testid='retweet']").text
        Like = article.find_element(By.XPATH,".//div[@data-testid='like']").text

        try:
            TimeStamp = article.find_element(By.XPATH,".//time").get_attribute('datetime')
        except NoSuchElementException:
            return      # if article has no timestamp (i.e. sponsored content), don't create a tweet

        # make a tuple for tweet
        tweet = (TimeStamp, TweetContent, Reply, Retweet, Like)
        return tweet
    
    def findTweets(self, subject, category):
        """
        open driver and navigate to tweet scroll page and return a list of tuples of the tweet content
        """
        options = EdgeOptions()
        options.use_chromium = True
        driver = Edge(self.PATH, options=options)
        driver.get("https://twitter.com/login")

        sleep(3)
        username = driver.find_element(By.XPATH,"//input[@name='text']")
        username.send_keys('ellaoc16')
        username.send_keys(Keys.RETURN)

        sleep(2)
        password = driver.find_element(By.XPATH, "//input[@name='password']")
        password.send_keys('QY_d7Kkjq')
        password.send_keys(Keys.RETURN)

        sleep(5)
        explore = driver.find_element(By.XPATH, "//a[@data-testid='AppTabBar_Explore_Link']")
        explore.click()

        sleep(5)
        search_box = driver.find_element(By.XPATH,"//input[@data-testid='SearchBox_Search_Input']")
        search_box.send_keys(subject)
        search_box.send_keys(Keys.ENTER)
        sleep(5)

        if category == 'Top':
            pass
        elif category == 'Latest':
            driver.find_element_by_link_text('Latest').click()
        else:
            print('ERROR - Invalid category name')

        Tweets = []
        tweet_ids = set()

        last_scroll_bar_pos = driver.execute_script("return window.pageYOffset;")
        scrolling = True
        
        while scrolling:
            articles = driver.find_elements(By.XPATH,"//article[@data-testid='tweet']")
            print('Scraping..., no. of tweets scraped: ', len(Tweets))
            
            #only check last 15 tweets loaded
            for article in articles[-15:]:
                tweet = self.getTweetData(article)
                if tweet:
                    # create a unique id for each tweet by just squishing all of its content together into a string
                    tweet_id = ''.join(tweet)
                    # check if this id is in already in id set before appending the tweet to our list
                    if tweet_id not in tweet_ids:
                        Tweets.append(tweet)
                        tweet_ids.add(tweet_id)                
            
            scroll_attempt = 0
            while True:
                driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
                sleep(2)
                current_scroll_bar_pos = driver.execute_script("return window.pageYOffset;")
                
                if current_scroll_bar_pos == last_scroll_bar_pos:
                    scroll_attempt += 1
                    if scroll_attempt >= 3:
                        print('Reached bottom of scoll page, stopping scraping')
                        scrolling = False   # breaks out of outer loop
                        break
                    else:
                        sleep(2)    # attempt another scroll
                else:
                    last_scroll_bar_pos = current_scroll_bar_pos
                    break
        
        return Tweets

    def spamDetector(self, tweet_content):
        spam_terms = ['RT', 'stream', 'mobile', 'LIVE', 'Live', 'STREAM', 'HD', 'WATCH', 'watch']
        for term in spam_terms:
            if term in tweet_content:
                #print('spam detected')
                return True
        return False

    def tweetDF(self, list_of_tweets):
        df = pd.DataFrame(list_of_tweets, columns =['TimeStamp', 'TweetContent', 'Replys', 'Retweets', 'Likes'])
        df.index.name = 'Index'
        return df
    
    def openDFExcel(self, df):
        df.to_excel("C:/Users/oconn/OneDrive/Documents/tweets_dataframe.xlsx",index=False)
        os.system('start "excel" "C:/Users/oconn/OneDrive/Documents/tweets_dataframe.xlsx"')

#create a scraper object
scraper = Scraper()

tweets = scraper.findTweets('watch', 'Top')
dataframe = scraper.tweetDF(tweets)
print(dataframe.head())

# Excel dataframe:
#scraper.openDFExcel(dataframe)