"""
stragglers.py
used for getting last pieces of data through play by play that can't be 
obtained through the other endpoints, specifically faceoff wins and fights
"""


import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from myNHLapi.nhlpy import NHLClient
client = NHLClient()

total ={}
sums = {}

def main():
	get_games()


def get_games():
    for season in ['20222023','20232024', '20242025']:
        games = get_games_season(season=season)

        with open(f"gameIds/{season}.txt", "w") as f:
            for id in games:
                f.write(str(id) + "\n")


def get_teams():
    client = NHLClient()
    teams = client.teams.teams()
    team_ids = [team['abbr'] for team in teams]

    return team_ids

def get_games_season(season="20242025"):
     teams = get_teams()
     games = []

     for team in teams:
        team_games = client.schedule.team_season_schedule(team_abbr=team, season=season)
        games += [game['id'] for game in team_games['games']]

     return list(set(games))

def parse_game_events( game_id):
    play_by_play_data = client.game_center.play_by_play(game_id)
    faceoff_wins = 0
    fights = 0

    
        

    print(f"Total Faceoff Wins: {faceoff_wins}")
    print(f"Total Fights: {fights}")

if __name__ == "__main__":
	main()
'''
.
'''



