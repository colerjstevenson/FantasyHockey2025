"""
getRanking.py
calculate player rankings based on performance metrics.
"""

import csv
import math
import sys
import os
import json
import time
import concurrent.futures
from functools import lru_cache
from datetime import datetime


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
    return parse_player_data(output)


def main():
    parse_player_data()



def get_full_data_set(season):
    
    raw = json.load(open(f'data/json/{season}_main_raw.json', 'r'))
    additional = json.load(open(f'data/json/{season}_additional.json', 'r'))
    ratios = json.load(open(f'data/json/{season}_ratios.json', 'r'))

    output = {}
    for player in raw:
        new_dict = {**player, **additional[player['playerId']], **ratios[player['playerId']]}
        new_dict['faceoff_ratio'] = float(additional[player['playerId']]['faceoff_avg']/(additional[player['playerId']]['faceoff_sd']+1))
        new_dict['fights_ratio'] = float(additional[player['playerId']]['fights']/player['gamesPlayed'])
        new_dict['faceoff'] = additional[player['playerId']]['faceoffWins']
        new_dict['shg'] = player['shGoals']
        new_dict['blocks'] = player['blockedShots']
        new_dict['pim'] =  player['penaltyMinutes']
        output[player['playerId']] = new_dict
    
    return output




def parse_player_data(data=None):
    if data is None:
        with open("player_data_full.json", "r") as f:
            raw_data = json.load(f)
    else:
        raw_data = data

    flipped_data = convert_season_data(raw_data)


    for season, data in flipped_data.items():
        with open(f"data/json/{season}_main.json", "w") as f:
            json.dump(data, f, indent=2)

        with open(f'data/csv/{season}_main.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        with open(f"data/json/{season}_ratios.json", "w") as f:
            json.dump(get_ratios(data), f, indent=2)

        with open(f'data/csv/{season}_ratios.csv', 'w', newline='') as f:
            ratios = list(get_ratios(data).values())
            writer = csv.DictWriter(f, fieldnames=ratios[0].keys())
            writer.writeheader()
            writer.writerows(ratios)

        with open(f"data/json/{season}_full.json", "w") as f:
            json.dump(get_full_data_set(season), f, indent=2)

        with open(f'data/csv/{season}_full.csv', 'w', newline='') as f:
            full = get_full_data_set(season)
            writer = csv.DictWriter(f, fieldnames=full['8478402'].keys())
            writer.writeheader()
            writer.writerows(full.values())

    return flipped_data


def get_ratios(data):
    output = {}
    for player in data:
        player_output = {
            'playerId': player['playerId'],
            'playerName': player['skaterFullName'],
            'position':player['position'],
            'team':player['teamAbbrevs'],
            'gp':player['gamesPlayed'],
            'points_ratio':float(player['points_avg'] / (player['points_sd'] + 1)),
            'plusMinus_ratio':float(player['plusMinus_avg'] / (player['plusMinus_sd'] + 1)),
            'shg_ratio':float(player['shg_avg'] / (player['shg_sd'] + 1)),
            'faceoffPctg_ratio':float(player['faceoffPctg_avg'] / (player['faceoffPctg_sd'] + 1)),
            'blocks_ratio':float(player['blocks_avg'] / (player['blocks_sd'] + 1)),
            'hits_ratio':float(player['hits_avg'] / (player['hits_sd'] + 1)),
            'pim_ratio':float(player['pim_avg'] / (player['pim_sd'] + 1))    
        }
        output[player['playerId']] = player_output

    return output


def convert_season_data(data_list):
    result = {}

    for entry in data_list:
        for season_id, value in entry.items():
            result.setdefault(season_id, []).append(value)

    return result   

def request_player_data():
    player_list = load_player_list("player_list.txt")
    print(f"Loaded {len(player_list)} players.")
    
    
    raw_data = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(get_player_stats, player_list))
    raw_data.extend(results)
   
    


def request_player_bios():
    player_list = load_player_list("player_list.txt")
    
    out = {}
    for player in player_list:
        print(player)
        career_stats = client.stats.player_career_stats(player_id=player)
        data = {
            'playerId' : career_stats['playerId'],
            'name': career_stats['firstName']['default'] + ' ' + career_stats['lastName']['default'],
            'team': career_stats.get('currentTeamAbbrev','NaN'),
            'position': career_stats['position'] if career_stats['position'] == 'D' else 'F',
            'active': career_stats['isActive'],
            'image': career_stats['headshot'],
            'height': career_stats['heightInInches'],
            'weight': career_stats['weightInPounds'],
            'age': calculate_age(career_stats['birthDate'])

        }
        out[player] = data
    
    json.dump(out, open("data/json/player_bios.json", "w"), indent=2)

def calculate_age(birthday_str):
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d")
    today = datetime.today()
    age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
    return age

if __name__ == "__main__":
    main()

