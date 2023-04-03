from team_data import *
from betfair_api import *
from matplotlib.backends.backend_pdf import PdfPages

class AnalyseMatch():
    def __init__(self, fixture, API:betfairAPI):
        self.API = API
        self.kickoff_time = fixture['kickOffTime']
        self.time_gap = int(input("Take data every ___ minutes\n>>> "))

        # create two team data objects
        self.TEAMS = [teamData(fixture['homeTeam'], self.time_gap), teamData(fixture['awayTeam'], self.time_gap)]

    
    def analyse(self):
        time_gap_counter = 0

        # football match length: 90 mins + 15 mins (halftime) + 10 mins (additional time/stoppages) = 115 mins
        total_no_of_gaps = 115 / self.time_gap

        while True:
            if time_gap_counter == total_no_of_gaps:
                break

            now = datetime.datetime.now().strftime("%H:%M")
            desired_time_datetime = self.kickoff_time + (time_gap_counter*datetime.timedelta(minutes=self.time_gap))
            desired_time = datetime.datetime.strftime(desired_time_datetime, "%H:%M")

            if now == desired_time:
                print('--------------------------------')
                print('Time Gap No. %d / %d' % (time_gap_counter, total_no_of_gaps))

                for TEAM in self.TEAMS:
                    # get current odds of team to win
                    market_catalogue = self.API.getMarketCatalogue(168)
                    odds = self.API.odds_of_team_to_win(market_catalogue, TEAM.team_name)
                    TEAM.matchOdds.append((desired_time_datetime, odds))
                    print('Odds of %s to win: %f' % (TEAM.team_name, odds))
                    
                    # scrape recent tweets and make a df with their corresponding sentiment scores
                    print('Currently getting tweets for %s at %s' % (TEAM.team_name, now))
                    sentiment_dataframe = TEAM.getSentimentDF()
                    if not sentiment_dataframe.empty:
                        sentiment_data = TEAM.getSentimentAverages(sentiment_dataframe, desired_time)
                        TEAM.data.append(sentiment_data)
                        print(TEAM.data)
        
                time_gap_counter += 1
        
        # when have collected all data and exited loop:
        # save data to output file and make pdf of graphs
        for TEAM in self.TEAMS:
            TEAM.saveData()
            self.makeGraphPDF(TEAM=TEAM)
   

    def makeGraphPDF(self, TEAM:teamData):
        print('Saving graphs of %s to a PDF file...' % TEAM.team_name)
        # set PDF parameters 
        plt.rcParams["figure.autolayout"] = True

        # check if data was collected before trying to make graphs
        # by checking if first tuple in data list is empty
        if len(TEAM.data) == 0:
            print('No Data Collected for %s' % TEAM.team_name)
        else: 
            fig1 = plt.figure(figsize=(7.50, 3.50))
            TEAM.polarityGraph()
            fig2 = plt.figure(figsize=(7.50, 3.50))
            TEAM.negativeGraph()
            fig3 = plt.figure(figsize=(7.50, 3.50))
            TEAM.positiveGraph()
            fig4 = plt.figure(figsize=(7.50, 3.50))
            TEAM.matchOddsGraph()
            TEAM.sentimentBarGraph('n')
            TEAM.sentimentBarGraph('p')
            fig5 = plt.figure()
            TEAM.makeWordCloud(TEAM.pos_words, 'p')
            fig6 = plt.figure()
            TEAM.makeWordCloud(TEAM.neg_words, 'n')
            
            filename = "Graphs_of_%s.pdf" % TEAM.team_name
            self.save_multi_image(filename)
            plt.close('all')

        print('Saved!')
            
            
    def save_multi_image(self, filename):
        pp = PdfPages(filename)
        fig_nums = plt.get_fignums()
        figs = [plt.figure(n) for n in fig_nums]
        for fig in figs:
            fig.savefig(pp, format='pdf')
        pp.close()




        


        
