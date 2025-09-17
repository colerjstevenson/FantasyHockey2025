"""
ranker.py
Command line script for ranking hockey players.
"""

import argparse
import json

seasons = ['20222023', '20232024', '20242025']

stats_weights = {
    'points': 0.2,
    'plusMinus': 0.4,
    'shg': 0.4,
    'faceoff': 0.2,
    'blocks': 0.7,
    'hits': 0.8,
    'pim': 0.6,
    'gp': 0.5,
    'fights': 0.8 
}

year_weights = {
    '20222023': 0.3,
    '20232024': 0.6,
    '20242025': 0.8
}

def get_args():
	parser = argparse.ArgumentParser(description="Rank hockey players based on stats.")
	parser.add_argument('--player', type=str, required=False, help='player to look for')
	
	return parser.parse_args()

def load_file(season):
	with open(f'data/json/{season}_full.json', 'r') as f:
		return json.load(f)
	
def load_player_list(filename):
    """Load player IDs from a txt file into a list."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def get_ratings(): 
    players = []
    stats = {}
    player_list = load_player_list('player_list.txt')

    for season in seasons:
        season_data = load_file(season)
        stats[season] = season_data

    for player_id in player_list:
        player = get_rating(player_id)
        players.append(player)
        
    return players

def get_rating(player_id):
    rating = 0
    for season in seasons:
        season_rating = 0
        if player_id not in stats[season]:
            continue
    
        season_rating += (stats[season][player_id]['points_ratio'] * stats_weights['points'])
        season_rating += (stats[season][player_id]['plusMinus_ratio'] * stats_weights['plusMinus'])
        season_rating += (stats[season][player_id]['shg_ratio'] * stats_weights['shg'])
        season_rating += (stats[season][player_id]['faceoff_ratio'] * stats_weights['faceoff'])
        season_rating += (stats[season][player_id]['blocks_ratio'] * stats_weights['blocks'])
        season_rating += (stats[season][player_id]['hits_ratio'] * stats_weights['hits'])
        season_rating += (stats[season][player_id]['pim_ratio'] * stats_weights['pim'])
        season_rating += (stats[season][player_id]['fights_ratio'] * stats_weights['fights'])
        season_rating += ((stats[season][player_id]['gp'] / 82) * stats_weights['gp'])
        rating += (season_rating * year_weights[season])

    player = {
            'playerId': player_id,
            'rating': rating
    }
     

def display_rankings(ratings, top_n=100):
    extra_data = load_file('20242025')

    sorted_players = sorted(ratings, key=lambda x: x['rating'], reverse=True)
    print(f"Top {top_n} Players:")
    for rank, player in enumerate(sorted_players[:top_n], start=1):
        player_name = extra_data.get(player['playerId'], {}).get('skaterFullName', 'Unknown')
        print(f"{rank:>3}. ID: {player['playerId']}, Name: {player_name}, Score: {player['rating']:.4f}")

def display_player(search_player, ratings):
    player_data = load_file('20242025')
    average_score = sum([i['rating'] for i in ratings]) / len(ratings) if ratings else 0

    for player in ratings:
        id = str(player['playerId'])
        if id not in player_data:
            continue

        if search_player.lower() in player_data[id]['skaterFullName'].lower():
            print(f"Player ID: {id}, Name: {player_data[id]['skaterFullName']}, Score: {player['rating']:.4f}, Above Average: {player['rating']-average_score:.2f}")
            return
def main():
    args = get_args()
    ratings = get_ratings()

    if args.player:
        display_player(args.player, ratings)
    else:
        display_rankings(ratings)
      



if __name__ == "__main__":
	main()
