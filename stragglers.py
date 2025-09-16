"""
stragglers.py
used for getting last pieces of data through play by play that can't be 
obtained through the other endpoints, specifically faceoff wins and fights
"""


import sys
import os
import json
import csv
import concurrent.futures

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from myNHLapi.nhlpy import NHLClient
client = NHLClient()

FACEOFF = 502
PENALTY = 509

fights = {}

def main():
	parse_all_games()


def get_games():
    for season in ['20222023','20232024', '20242025']:
        games = get_games_season(season=season)

        with open(f"gameIds/{season}.txt", "w") as f:
            for id in games:
                f.write(str(id) + "\n")


def load_player_list():
    """Load player IDs from a txt file into a list."""
    with open('player_list.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

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

def parse_game_events(game_id):
    plays = client.game_center.play_by_play(game_id)['plays']
    faceoff_wins = {}

    boxscore = client.game_center.boxscore(game_id=game_id)
    for team in ['homeTeam', 'awayTeam']:
        for position in ['forwards', 'defense']:
            try:
                for player in boxscore['playerByGameStats'][team][position]:
                    faceoff_wins[player['playerId']] = 0
            except:
                print(boxscore.keys())

    for play in plays:
        if play['typeCode'] == FACEOFF:
            winner = play['details']['winningPlayerId']
            faceoff_wins[winner] += 1

        if play['typeCode'] == PENALTY and play['details']['descKey'] == 'fighting':
            player = play['details']['committedByPlayerId']
            fights[player] = fights.get(player, 0) + 1

    print(f"Processed game {game_id}")

    return faceoff_wins      



def parse_all_games():
    player_list = load_player_list()

    for season in ['20222023','20232024', '20242025']:
        with open(f"gameIds/{season}.txt", "r") as f:
            game_ids = [line.strip() for line in f if line.strip()]
        players = {}
        for player in player_list:
            players[player] = {
                'FO_n': 0,
                'FO_total': 0,
                'FO_delta': 0,
                'FO_mean': 0,
                'FO_M2': 0,
                'fights': 0
            }

        # Use ThreadPoolExecutor to process games concurrently
        print(f"Processing {len(game_ids)} games for season {season}...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(parse_game_events, game_ids))
        
        for wins in results:
            for player_id, win_count in wins.items():
                if str(player_id) in players:
                    players[str(player_id)]['FO_n'] += 1
                    players[str(player_id)]['FO_total'] += win_count
                    delta = win_count - players[str(player_id)]['FO_mean']
                    players[str(player_id)]['FO_mean'] += delta / players[str(player_id)]['FO_n']
                    players[str(player_id)]['FO_M2'] += delta * (win_count - players[str(player_id)]['FO_mean'])

        output = {}
        for player_id in players:
            output[player_id] = {
                'faceoffWins': players[player_id]['FO_total'],
                'faceoff_avg': players[player_id]['FO_mean'],
                'faceoff_sd': (players[player_id]['FO_M2'] / players[player_id]['FO_n'])**0.5 if players[player_id]['FO_n'] > 1 else 0,
                'fights': fights.get(int(player_id), 0)
            }

        with open(f"data/json/{season}_additional.json", "w") as f:
            json.dump(output, f, indent=4)
        
        with open(f'data/csv/{season}_additional.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['playerId', 'faceoffWins', 'faceoff_avg', 'faceoff_sd', 'fights'])
            writer.writeheader()
            for player_id, stats in output.items():
                row = {'playerId': player_id}
                row.update(stats)
                writer.writerow(row)



if __name__ == "__main__":
	main()
'''
.
'''



