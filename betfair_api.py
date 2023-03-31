import pandas as pd
import datetime
import json, urllib, urllib.error, urllib.request, sys, re
import requests

class betfairAPI():
    def __init__(self, competition):
        APP_KEY = 'QYz0oglFZXYpAL7y'
        login_endpoint = 'https://identitysso-cert.betfair.com/api/certlogin'

        payload = 'username=ellaoc16&password=Brainiac007!'
        headers = {'X-Application': APP_KEY, 'Content-Type': 'application/x-www-form-urlencoded'}

        # send a HTTP POST request to login API endpoint, receive a json response giving login details
        login_response = requests.post(url=login_endpoint, data=payload, headers=headers,
                         cert=(r"C:\Users\oconn\OneDrive\Documents\int_name.crt", r"C:\Users\oconn\OneDrive\Documents\client-2002.pem"))
        
        login_resp_json = login_response.json()
        session_status = login_resp_json['loginStatus']
        session_token = login_resp_json['sessionToken']

        if session_status != 'SUCCESS':
            print('ERROR logging into befair API')
        
        # headers for API requests
        self.headers = {'X-Application': APP_KEY, 'X-Authentication': session_token ,'content-type': 'application/json'}
        
        # API endpoint
        self.betting_endpoint = 'https://api.betfair.com/exchange/betting/json-rpc/v1'

        # filters for API requests
        self.marketType = '["MATCH_ODDS"]'
        self.eventTypeID = '["1"]'                  # id for football
        self.priceProjection = '["EX_BEST_OFFERS"]' 

        if competition == 'Premier League':
            self.competitionID = '["10932509"]'   
        elif competition == 'EURO Qualifiers':
            self.competitionID = '["12552926"]'  
            
    
    def getFootballComps(self):
        # set filters on what data we want to receive from API request
        jsonrpc_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCompetitions", "params": {"filter":{ "eventTypeIds": [1] }}, "id": 1}'
        response = requests.post(url=self.betting_endpoint, data=jsonrpc_req, headers=self.headers)
        footballCompetitions = response.json()
        return footballCompetitions
    
    def getMarketCatalogue(self, hours:int) -> list:
        """
        Input parameter 'hours' refers to number of hours into future you want to get market catalogue
        """
        marketStartTime = (datetime.datetime.now() - datetime.timedelta(hours=2))
        marketStartTime = marketStartTime.strftime('%Y-%m-%dT%H:%M:%SZ')
        marketEndTime = (datetime.datetime.now() + datetime.timedelta(hours=hours))
        marketEndTime = marketEndTime.strftime('%Y-%m-%dT%H:%M:%SZ')

        catalogue_req='{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue",\
                    "params": {"filter":{"eventTypeIds":'+self.eventTypeID+',"competitionIds":'+self.competitionID+',"marketTypeCodes":'+self.marketType+',\
                    "marketStartTime":{"from":"'+marketStartTime+'", "to":"'+marketEndTime+'"}},"sort":"FIRST_TO_START",\
                    "maxResults":"1000", "marketProjection":["RUNNER_METADATA", "MARKET_START_TIME"]}, "id": 1}'
    
        req = urllib.request.Request(self.betting_endpoint, data=catalogue_req.encode('utf-8'), headers=self.headers)
        response = urllib.request.urlopen(req)
        jsonResponse = response.read()
        pkg = jsonResponse.decode('utf-8')
        Result = json.loads(pkg) 
        market_catalogue = Result['result']
        return market_catalogue
    
    def marketCatalogue_DF(self, market_catalogue):
        df = pd.DataFrame(market_catalogue)
        return df
    
    def upcomingFixtures(self, hours:int) -> list:
        """
        Prints the upcoming fixtures and their times based on market catalogue inputted
        and returns a list of fixtures (each one is a dictionary)
        """
        fixtures = []
        market_catalogue = self.getMarketCatalogue(hours)
        print('Upcoming Fixtures:')
        count = 0

        for item in market_catalogue:
            fixture = {}
            fixture['index'] = count
            runners = item['runners']

            fixture['homeTeam'] = runners[0]['runnerName']
            fixture['awayTeam'] = runners[1]['runnerName']
            start_time = item['marketStartTime'] 
            start_time = datetime.datetime.strptime(start_time[:19], '%Y-%m-%dT%H:%M:%S')
            fixture['kickOffTime'] = start_time + datetime.timedelta(hours=1)

            fixtures.append(fixture)
            print('%i: %s - %s vs %s' % (fixture['index'], fixture['kickOffTime'],fixture['homeTeam'], fixture['awayTeam']))
            count += 1
        
        return fixtures
            
    def findFixture(self, market_catalogue, inputTeam:str):
        """
        Takes in a team's name as input and returns the market ID and selection ID if involved in a fixture in the 
        market catalogue
        """
        for item in market_catalogue:
            runners_list = item['runners']
            
            for runner in runners_list:
                team_name = runner['runnerName']
                if team_name == inputTeam:
                    return item['marketId'], runner['selectionId']
        
        print('Team not found in market catalogue, check spelling')
        return

    def getRunnerBook(self, marketID, selectionID) -> dict:
        price_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listRunnerBook", "params": {"locale":"en",\
                    "marketId":"'+marketID+'", "selectionId":"'+selectionID+'", '\
                    '"priceProjection":{"priceData":'+self.priceProjection+'},"orderProjection":"ALL"},"id":1}'
        
        req = urllib.request.Request(self.betting_endpoint, data=price_req.encode('utf-8'), headers=self.headers)
        price_response= urllib.request.urlopen(req)
        price_jsonResponse = price_response.read()
        price_pkg = price_jsonResponse.decode('utf-8')
        price_result = json.loads(price_pkg)
        runner_book = price_result['result'][0]
        return runner_book
    
    def odds_of_team_to_win(self, market_catalogue, inputTeam:str):
        fixture = self.findFixture(market_catalogue, inputTeam)
        # NB! make IDs into strings so that zero digits at end aren't lost
        market_id = str(fixture[0])
        selection_id = str(fixture[1])
        
        runnerBook = self.getRunnerBook(market_id, selection_id)
        match_odds = runnerBook['runners'][0]['lastPriceTraded']
        percentage_odds = 100/match_odds
        return percentage_odds



"""
API = betfairAPI('Premier League')
API.upcomingFixtures(120)

marketCatalogue = API.getMarketCatalogue(120)
print(marketCatalogue)

team_name = 'Bournemouth'
fixture = API.findFixture(marketCatalogue, team_name)
print(fixture)

runnerBook = API.getRunnerBook(fixture[0], str(fixture[1]))
print(runnerBook)

odds = API.odds_of_team_to_win(marketCatalogue, 'Bournemouth')
print(odds)
"""











       