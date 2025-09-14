"""
getRanking.py
calculate player rankings based on performance metrics.
"""

import sys
import os
import json
import time
import concurrent.futures


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from myNHLapi.nhlpy import NHLClient
client = NHLClient()

def load_player_list(filename):
    """Load player IDs from a txt file into a list."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_player_boxscore(player_id, game_id):
    boxscore = client.game_center.boxscore(game_id=game_id)
    for team in ['homeTeam', 'awayTeam']:
        for position in ['forwards', 'defense']:
            for player in boxscore['playerByGameStats'][team][position]:
                if str(player['playerId']) == str(player_id):
                    return player

def get_player_gamelog(player_id, season_id, game_type):
    try:
        gamelog = client.stats.player_game_log(player_id, season_id, game_type)
    except Exception as e:
        print(f"Error fetching gamelog for player {player_id}, season {season_id}: {e}")
        return []
    
    def fetch_full_game(game):
        try:
            boxscore = get_player_boxscore(player_id, game['gameId'])
            return {**game, **boxscore}
        except Exception as e:
            print(f"Error fetching boxscore for player {player_id}, game {game.get('gameId')}: {e}")
            return game
        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        output = list(executor.map(fetch_full_game, gamelog))
    return output

def get_player_stats(player_id):

    seasons = ['20222023', '20232024', '20242025']
    output = {}

    try:
        summarys = client.stats.get_player_stats(player_id, start='20222023', end='20242025')
    except Exception as e:
        print(f"Error fetching stats for player {player_id}: {e}")
        summarys = [{},{},{}]

    for season in seasons:
        gamelog = get_player_gamelog(player_id, season_id=season, game_type=2)
        for summary in summarys:
           if summary.get('seasonId') == season:
               output[season] = {
                   "summary": summary,
                   "gamelog": gamelog
               }
    return output


def main():
    player_list = load_player_list("player_list.txt")
    print(f"Loaded {len(player_list)} players.")
    start_time = time.time()
    
    raw_data = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(get_player_stats, player_list))
    raw_data.extend(results)
    end_time = time.time()
    json.dump(raw_data, open("player_data.json", "w"), indent=4)

    print(f"Estimated Run time: {(len(player_list)*(end_time - start_time))/3600:.2f} hours")



if __name__ == "__main__":
    main()

    