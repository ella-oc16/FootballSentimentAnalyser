from match_analyser import *
import datetime

def run():
    print('\n')

    # initiate betfair API depending on which competition you want results for
    competition = input("Premier League 'P' or EURO Qualifiers 'E'?\n>>> ")
    if competition == 'P':
        API = betfairAPI('Premier League')
    elif competition == 'E':
        API = betfairAPI('EURO Qualifiers')
    
    # make a list of the fixtures for the next week and print them
    print('\n')
    fixtures = API.upcomingFixtures(168)
    print('\n')

    fixtures.append({'index':16, 'kickOffTime':datetime.datetime.now() + datetime.timedelta(minutes=1),
                     'homeTeam':'Man City', 'awayTeam':'Liverpool'})

    fixture_num = int(input("Fixture Number:\n>>> "))
    fixture = fixtures[fixture_num]
    print(fixture)

    # create an analyse match object with this fixture as the input
    match = AnalyseMatch(fixture, API=API)
    
    # wait for kickoff before beginning analysis of tweets
    waiting_for_kickoff = True
    kickoff_time_string = datetime.datetime.strftime(match.kickoff_time, "%H:%M")
    print('Waiting for Kick-Off at', kickoff_time_string)

    while waiting_for_kickoff:
        now = datetime.datetime.now().strftime("%H:%M")
        if now == kickoff_time_string:
            waiting_for_kickoff = False
            print('KICKOFF!!!')

    # analyse data for both teams
    match.analyse()


if __name__ == "__main__":
   run()



