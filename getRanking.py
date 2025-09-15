"""
getRanking.py
calculate player rankings based on performance metrics.
"""

import math
import sys
import os
import json
import time
import concurrent.futures
from functools import lru_cache


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from myNHLapi.nhlpy import NHLClient
client = NHLClient()

def load_player_list(filename):
    """Load player IDs from a txt file into a list."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

@lru_cache(maxsize=1024)
def get_player_boxscore(player_id, game_id):
    boxscore = client.game_center.boxscore(game_id=game_id)
    for team in ['homeTeam', 'awayTeam']:
        for position in ['forwards', 'defense']:
            for player in boxscore['playerByGameStats'][team][position]:
                if str(player['playerId']) == str(player_id):
                    return player

def get_player_gamelog(player_id, season_id, game_type, summary):
    try:
        gamelog = client.stats.player_game_log(player_id, season_id, game_type)
    except Exception as e:
        print(f"Error fetching gamelog for player {player_id}, season {season_id}: {e}")
        return []
    
    output = {}
    output['playerId'] = player_id
    output['points_sd'] = 0
    output['plusMinus_sd'] = 0
    output['shg_sd'] = 0
    output['faceoffPctg_sd'] = 0
    output['blocks_sd'] = 0
    output['hits_sd'] = 0
    output['pim_sd'] = 0

    games_played = summary.get('gamesPlayed', 1)
    summary['faceoffWinPct'] = summary.get('faceoffWinPct', 0) or 0
    average = {
        'points_avg': summary.get('points', 0) / games_played,
        'plusMinus_avg': summary.get('plusMinus', 0) / games_played,
        'shg_avg': summary.get('shGoals', 0) / games_played,
        'blocks_avg': summary.get('blockedShots', 0) / games_played,
        'hits_avg': summary.get('hits', 0) / games_played,
        'pim_avg': summary.get('penaltyMinutes', 0) / games_played,
        'faceoffPctg_avg': (summary.get('faceoffWinPct', 0) or 0) / games_played
    }
    
    for game in gamelog:
        try:
            boxscore = get_player_boxscore(player_id, game['gameId'])
            output['position'] = 'F' if boxscore['position'] != 'D' else 'D'
            output['points_sd'] += (game['points'] - average['points_avg'])**2
            output['plusMinus_sd'] += (game['plusMinus'] - average['plusMinus_avg'])**2
            output['shg_sd'] += (game['shorthandedGoals'] - average['shg_avg'])**2
            output['faceoffPctg_sd'] += (boxscore['faceoffWinningPctg'] - average['faceoffPctg_avg'])**2
            output['blocks_sd'] += (boxscore['blockedShots'] - average['blocks_avg'])**2
            output['hits_sd'] += (boxscore['hits'] - average['hits_avg'])**2
            output['pim_sd'] += (game['pim'] - average['pim_avg'])**2
        except Exception as e:
            print(f"Error fetching boxscore for player {player_id}, game {game.get('gameId')}: {e}")

    output['points_sd'] = math.sqrt(output['points_sd']/games_played)
    output['plusMinus_sd'] = math.sqrt(output['plusMinus_sd']/games_played)
    output['shg_sd'] = math.sqrt(output['shg_sd']/games_played)
    output['faceoffPctg_sd'] = math.sqrt(output['faceoffPctg_sd']/games_played)
    output['blocks_sd'] = math.sqrt(output['blocks_sd']/games_played)
    output['hits_sd'] = math.sqrt(output['hits_sd']/games_played)
    output['pim_sd'] = math.sqrt(output['pim_sd']/games_played)

    return {**output, **average}

def get_player_stats(player_id):

    seasons = ['20222023', '20232024', '20242025']
    output = {}

    try:
        summarys = client.stats.get_player_stats(player_id, start='20222023', end='20242025')
    except Exception as e:
        print(f"Error fetching stats for player {player_id}: {e}")
        summarys = [{},{},{}]
    for season in seasons:
        for summary in summarys:
            if str(summary['seasonId']) == str(season):
               gamelog = get_player_gamelog(player_id, season_id=season, game_type=2,summary=summary)
               output[season] = {**summary, **gamelog}

    print(f"Fetched stats for player {summarys[0].get('skaterFullName','Unknown')} ({player_id})")
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
    json.dump(raw_data, open("player_data.json", "w"), indent=2)

    print(f"Estimated Run time: {((end_time - start_time))/3600:.2f} hours")



if __name__ == "__main__":
    main()

