from getpass import getpass
from time import sleep
import pandas as pd
import datetime

import selenium.webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.by import By

class Scraper:
    def __init__(self):
        self.PATH = "C:/Users/oconn/Downloads/edgedriver_win64/msedgedriver.exe"
        self.scraper_subject : str

    def getTweetData(self, article) -> tuple:
        """
        Extracts data from an individual tweet and returns this data in form of tuple
        """
        try:
            TweetContent = article.find_element(By.XPATH,".//div[@data-testid='tweetText']").text
        except StaleElementReferenceException:
            return
        except NoSuchElementException:
            return

        # if spam is detected, do not return the tweet
        if self.spamDetector(TweetContent):
            return
        
        # if not in english, do not return tweet
        try:
            Language = article.find_element(By.XPATH, ".//div[@lang='en']")
        except NoSuchElementException:
            #print('not in english! ---------')
            #print(TweetContent)
            return

        #Reply = article.find_element(By.XPATH,".//div[@data-testid='reply']").text
        Retweet = article.find_element(By.XPATH,".//div[@data-testid='retweet']").text
        Like = article.find_element(By.XPATH,".//div[@data-testid='like']").text

        try:
            TimeStamp = article.find_element(By.XPATH,".//time").get_attribute('datetime')
        except NoSuchElementException:
            return      # if article has no timestamp (i.e. sponsored content), don't create a tweet

        # make a tuple for tweet
        tweet = (TimeStamp, TweetContent, Retweet, Like)
        return tweet
    
    def findTweets(self, subject, category, time_gap=5, maxTweets=300) -> list:
        """
        open driver and navigate to tweet scroll page and return a list of tuples of the tweet content
        """
        self.scraper_subject = subject
        options = EdgeOptions()
        options.headless = True
        options.add_argument('log-level=3')
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
        try:
            explore.click()
        except ElementClickInterceptedException:
            print('ERROR - Pop Up preventing tweet scraping, exiting scraper')
            return

        sleep(3)
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
            print('Scraping...\nNo. of tweets scraped: ', len(Tweets))

            # set upper limit on amount of tweets that can be collected
            if len(Tweets) >= maxTweets:
                scrolling = False
                print('FINISHED SCRAPING - Exceeded Upper Limit on Tweets')
                break
            
            # only check last 15 tweets loaded
            for article in articles[-15:]:
                tweet = self.getTweetData(article)
                if tweet:
                    # if we're looking at lastest tweets, check that tweet is no older than time gap
                    # if it is, stop scrolling
                    datetime_of_tweet = datetime.datetime.strptime(tweet[0][:19], '%Y-%m-%dT%H:%M:%S')
                    if category == 'Latest' and datetime_of_tweet < datetime.datetime.now() - datetime.timedelta(minutes=time_gap):
                        print('FINISHED SCRAPING - Retrieved All Tweets From Last %s Minutes' % time_gap)
                        scrolling = False
                        break

                    # create a unique id for each tweet by squishing all of its content together into a string
                    tweet_id = ''.join(tweet)
                    # check if this id is already in id set before appending the tweet to our list
                    if tweet_id not in tweet_ids:
                        Tweets.append(tweet)
                        tweet_ids.add(tweet_id)                
            
            scroll_attempt = 0
            while True:
                driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
                sleep(2)
                current_scroll_bar_pos = driver.execute_script("return window.pageYOffset;")
                
                # check if the current scroll bar position is same as previous scroll bar position
                if current_scroll_bar_pos == last_scroll_bar_pos:
                    scroll_attempt += 1
                    if scroll_attempt >= 3:
                        print('FINISHED SCRAPING - Bottom of Page Reached')
                        scrolling = False   # breaks out of outer loop
                        break
                    else:
                        sleep(2)    # attempt another scroll
                else:
                    last_scroll_bar_pos = current_scroll_bar_pos
                    break
        
        return Tweets

    def spamDetector(self, tweet_content):
        spam_terms = ['RT', 'stream', 'mobile', 'LIVE', 'Live', 'STREAM', 'HD', 'WATCH', 'watch', 'GIVEAWAY']
        for term in spam_terms:
            if term in tweet_content:
                #print('spam detected')
                return True
        return False

    # Returns a dataframe of the tweets along with the subject of the dataframe
    def tweetDF(self, tweets : list):
        """
        Takes in the list of tweets and returns a dataframe and the subject of the dataframe
        """
        df = pd.DataFrame(tweets, columns =['TimeStamp', 'TweetContent', 'Retweets', 'Likes'])
        df.index.name = 'Index'
        return df, self.scraper_subject
    
