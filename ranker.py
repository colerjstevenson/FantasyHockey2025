"""
ranker.py
Command line script for ranking hockey players.
"""

import argparse
import json

stats_weights = {
    'points': 0.2,
    'plusMinus': 0.4,
    'shg': 0.4,
    'faceoffPctg': 0.4,
    'blocks': 0.7,
    'hits': 0.8,
    'pim': 0.8,
    'gp': 0.5
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
	with open(f'data/json/{season}_ratios.json', 'r') as f:
		return json.load(f)
	
def load_player_list(filename):
    """Load player IDs from a txt file into a list."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def get_ratings():
    seasons = ['20222023', '20232024', '20242025']
    
    players = []
    ratios = {}
    player_list = load_player_list('player_list.txt')

    for season in seasons:
        season_data = load_file(season)
        ratios[season] = season_data

    for player_id in player_list:
        rating = 0
        for season in seasons:
            season_rating = 0
            if player_id not in ratios[season]:
                continue
        
            season_rating += (ratios[season][player_id]['points'] * stats_weights['points'])
            season_rating += (ratios[season][player_id]['plusMinus'] * stats_weights['plusMinus'])
            season_rating += (ratios[season][player_id]['shg'] * stats_weights['shg'])
            season_rating += (ratios[season][player_id]['faceoffPctg'] * stats_weights['faceoffPctg'])
            season_rating += (ratios[season][player_id]['blocks'] * stats_weights['blocks'])
            season_rating += (ratios[season][player_id]['hits'] * stats_weights['hits'])
            season_rating += (ratios[season][player_id]['pim'] * stats_weights['pim'])
            season_rating += ((ratios[season][player_id]['gp'] / 82) * stats_weights['gp'])
            rating += (season_rating * year_weights[season])

        player = {
             'playerId': player_id,
             'rating': rating
        }
        players.append(player)
        
    return players


def display_rankings(ratings, top_n=100):
    extra_data = load_file('20242025')

    sorted_players = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    print(f"Top {top_n} Players:")
    for rank, (player_id, score) in enumerate(sorted_players[:top_n], start=1):
        player_name = extra_data.get(player_id, {}).get('playerName', 'Unknown')
        print(f"{rank:>3}. ID: {player_id}, Name: {player_name}, Score: {score:.4f}")

def display_player(player, ratings):
    player_data = load_file('20242025')
    average_score = sum(ratings.values()) / len(ratings) if ratings else 0

    for player_id, score in ratings.items():
        if player_id in player_data:
            if player.lower() in player_data[player_id]['playerName'].lower():
                print(f"Player ID: {player_id}, Name: {player_data[player_id]['playerName']}, Score: {score:.4f}, Above Average: {score-average_score:.2f}")
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
