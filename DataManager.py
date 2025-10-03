
"""
DataManager.py
Fantasy Hockey Data Management Module
"""


import sys
import os
import re
import json
import pandas as pd
import numpy as np

# --- Utility Functions ---
def is_season_type(filename):
	pattern = r'^\d{8}_[a-zA-Z0-9]+'
	return re.match(pattern, filename) is not None

# --- DataManager Class ---
class DataManager:
		
	# --- Initialization & Loading ---
	def __init__(self):
		self.stats = [
			'points',
			'plusMinus',
			'shg',
			'faceoff',
			'blocks',
			'hits',
			'pim',
			'fights',
			'age'
		]
		self.stats_weights = {
			'points':    0.10,
			'plusMinus': 0.25,
			'shg':       0.20,
			'faceoff':   0.45,
			'blocks':    0.65,
			'hits':      0.90,
			'pim':       0.65,
			'gp':        0.50,
			'fights':    0.80,
			'age':       0.50,
			'fr':        1.00,
			'team':      0.20
		}
		self.year_weights = {
			'20222023': 0.3,
			'20232024': 0.5,
			'20242025': 0.9
		}

		self.team_weights = {
			"ARI": 0.99,
			"ANA": 1.01,
			"BOS": 1.09,
			"BUF": 1.02,
			"CGY": 1.05,
			"CAR": 0.99,
			"CBJ": 1.06,
			"CHI": 0.94,
			"COL": 0.93,
			"DAL": 0.91,
			"DET": 1.01,
			"EDM": 0.90,
			"FLA": 1.10,
			"LAK": 0.98,
			"MIN": 0.92,
			"MTL": 1.07,
			"NSH": 1.03,
			"NJD": 1.04,
			"NYI": 1.01,
			"NYR": 1.06,
			"OTT": 1.07,
			"PHI": 1.02,
			"PIT": 0.99,
			"SJS": 0.95,
			"SEA": 0.98,
			"STL": 1.02,
			"TBL": 0.94,
			"TOR": 1.06,
			"VAN": 1.09,
			"VGK": 0.98,
			"WPG": 1.04
		}
  
		self.data = {}
		self.bios = json.load(open('data/json/player_bios.json'))
		self.players = self.load_player_list()
		self.seasons = ['20222023', '20232024', '20242025']
		self.meta = self.load_meta()
		self.base = {}
		self._load_bulk_data()
		self._add_ratios_to_data()
		self._store_normalized_ratios()
		self._store_player_data()
		self._store_team_fantasy_scores()
		self._store_fantasy_norms()

	def _load_bulk_data(self):
		json_dir = os.path.join('data', 'json')
		for filename in os.listdir(json_dir):
			if filename.endswith('.json') and is_season_type(filename):
				type = filename.replace('.json', '').split('_')[-1]
				season = filename.split('_')[0]
				if type in self.data.keys():
					self.data[type][season] = self.load_file(type, season)
				else:
					self.data[type] = {}
					self.data[type][season] = self.load_file(type,season)

	def _add_ratios_to_data(self):
		for player in self.players:
			for season in self.seasons:
				if player in self.data['full'][season]:
					self.data['ratios'][season][player]['faceoff_ratio'] = self.data['full'][season][player]['faceoff_ratio']
					self.data['ratios'][season][player]['fights_ratio'] = self.data['full'][season][player]['fights_ratio']
					self.data['ratios'][season][player]['age_ratio'] = self.get_age_ratio(player)

	def _store_normalized_ratios(self):
		self.data['norms'] = {}
		for season in self.seasons:
			self.data['norms'][season] = self.normalize_ratios(season)

	def _store_player_data(self):
		for player in self.players:
			self.base[player] = {
				'Team': self.bios[player]['team'],
				'ID': player,
				'Name': self.bios[player]['name'],
				'Pos': self.bios[player]['position'],
				'Age': self.bios[player]['age']
			}

	def _store_team_fantasy_scores(self):
		self.team_fantasy_scores = {}
		for season in self.seasons:
			self.team_fantasy_scores[season] = self.get_team_fantasy_scores(season)

	def _store_fantasy_norms(self):
		self.fantasy_norms = {}
		for season in self.seasons:
			self.fantasy_norms[season] = self.get_normalized_fantasy_points(season)

	# --- Data Transformation & Normalization ---


	def normalize_ratios(self, season):
		out = {}
		for stat in self.stats:
			values = [self.data['ratios'][season][pid][stat+'_ratio'] for pid in self.players if pid in self.data['ratios'][season]]
			min_val, max_val = min(values), max(values)

			for player in self.players:
				if player not in self.data['ratios'][season]:
					continue

				if player not in out:
					out[player] = {}

				out[player][stat+'_norm'] = (self.data['ratios'][season][player][stat+'_ratio'] - min_val) / (max_val - min_val) if max_val > min_val else 0
		
		return out


	def get_normalized_fantasy_points(self, season):
		out = {}
		values = [self.get_fantasy_points(pid, season) for pid in self.players if pid in self.data['full'][season]]
		min_val, max_val = min(values), max(values)

		for player in self.players:
			if player not in self.data['full'][season]:
				continue

			out[player] = (self.get_fantasy_points(player, season) - min_val) / (max_val - min_val) if max_val > min_val else 0
		
		return out

	def get_fantasy_ratio(self, player, season):
		values = {
			'points': 0.5,
			'plusMinus': 2,
			'faceoff': 1,
			'shg': 2,
			'blocks': 3,
			'pim': 5,
			'hits': 7
		}

		if player not in self.data['full'][season]:
			return 0

		fp = 0.0
		for v in values.keys():
			fp += self.data['full'][season][player][v+'_ratio'] * values[v]

		return fp / float(self.data['full'][season][player]['gp'])


	def get_team_fantasy_scores(self, season):
		teams = {}
		games_played = {}
		for player in self.players:
			if player not in self.data['full'][season]:
				continue

			team = self.bios[player]['team']
			if team not in teams:
				teams[team] = 0
				games_played[team] = 0

			games_played[team] += self.data['full'][season][player]['gp']
			teams[team] += self.get_fantasy_ratio(player, season)

		for team in teams:
			if team in games_played and games_played[team] > 0:
				teams[team] /= games_played[team]

		normalized_teams = {}
		min_val = min(teams.values())
		max_val = max(teams.values())
		for team in teams:
			normalized_teams[team] = (teams[team] - min_val) / (max_val - min_val) if max_val > min_val else 0
		return normalized_teams


	def get_fantasy_points(self, player, season):
		values = {
			'points': 0.5,
			'plusMinus': 2,
			'faceoff': 1,
			'shg': 2,
			'blocks': 3,
			'pim': 5,
			'hits': 7
		}

		fp = 0.0
		for v in values.keys():
			fp += self.data['full'][season][player][v] * values[v]
		
		return fp / float(self.data['full'][season][player]['gp'])


	def get_age_ratio(self, player, peak=30, alpha=0.0025, minf=0.8, maxf=1.2):
		age = self.bios[player]['age']
		f = 1.0 - alpha * (age - peak)**2
		return float(np.clip(f, minf, maxf))


	def load_file(self, type, season):
		name = f'data/json/{season}_{type}.json'
		try:
			return json.load(open(name))
		except:
			print(f"{name} not found")
			return {}
			

	def toCVS(self, data):
		if 'Rating' in data[0]:
			sorted_data = sorted(data, key=lambda x: x['Rating'], reverse=True)
			return pd.DataFrame(sorted_data)
		
		return pd.DataFrame(data)
	

	def get_player_data(self, player):
		out = []
		for season in self.seasons:
			if player in self.data['full'][season].keys():
				tot = self.stage_data(player, season, no_rank=True)
				avg = self.stage_data(player, season, dataset='avg', no_rank=True)
				sd = self.stage_data(player, season, dataset='sd', no_rank=True)
				rat = self.stage_data(player, season, dataset='ratio', no_rank=True)
				out.append({**{'season': season}, **tot, **rat, **avg, **sd})
			else:
				print(f'{player} not found in {season}')
		return out
	
	def get_player_bio(self, player):
		return self.bios[player]

	def stage_data(self, player, season, dataset=None, no_rank=False):
		stats = ['hits', 'blocks', 'pim', 'faceoff', 'shg', 'plusMinus', 'points', 'fights']
		if dataset:
			tag = '_' + dataset
		else:
			tag = ''

		out = {}

		out['GP'] = self.data['full'][season][player].get('gp', 0)

		if not no_rank:
			out['Rating'] = self.get_rating(player)

		out['FP/GP'] = self.get_fantasy_points(player, season)

		for stat in stats:
			out[stat+tag] = self.data['full'][season][player].get(stat+tag, 0)

		return out


	def get_averages(self, season):
		output = []
		for player in self.players:
			if player in self.data['full'][season].keys():
				stats = self.stage_data(player, season, 'avg')
				output.append({**{'Picked' : self.meta[player]['picked']}, **self.base[player] , **stats})

		return output

	def get_std(self, season):
		output = []
		for player in self.players:
			if player in self.data['full'][season].keys():
				stats = self.stage_data(player, season, 'sd')
				output.append({**{'Picked' : self.meta[player]['picked']}, **self.base[player] , **stats})

		return output

	def get_ratios(self, season):
		output = []
		for player in self.players:
			if player in self.data['full'][season].keys():
				stats = self.stage_data(player, season, 'ratio')
				output.append({**{'Picked' : self.meta[player]['picked']}, **self.base[player] , **stats})

		return output

	def get_totals(self, season):
		output = []
		for player in self.players:
			if player in self.data['full'][season].keys():
				stats = self.stage_data(player, season)
				output.append({**{'Picked' : self.meta[player]['picked']}, **self.base[player] , **stats})

		return output

	def get_fullset(self, season):
		output = []

		for player in self.players:
			if player in self.data['full'][season].keys():
				tot = self.stage_data(player, season, no_rank=True)
				avg = self.stage_data(player, season, dataset='avg', no_rank=True)
				sd = self.stage_data(player, season, dataset='sd', no_rank=True)
				rat = self.stage_data(player, season, dataset='ratio')

				output.append({**{'Picked' : self.meta[player]['picked']}, **self.base[player] , **rat, **tot, **avg, **sd})
		
		return output


	def get_ratings(self): 
		players = []

		for player_id in self.players:
			player = self.get_rating(player_id)
			players.append(player)
			
		return players

	def get_rating(self, player_id):
		rating = 0
		for season in self.seasons:
			season_rating = 0
			if player_id not in self.data['ratios'][season]:
				continue
		
			season_rating += (self.data['ratios'][season][player_id]['points_ratio'] * self.stats_weights['points'])
			season_rating += (self.data['ratios'][season][player_id]['plusMinus_ratio'] * self.stats_weights['plusMinus'])
			season_rating += (self.data['ratios'][season][player_id]['shg_ratio'] * self.stats_weights['shg'])
			season_rating += (self.data['ratios'][season][player_id]['faceoff_ratio'] * self.stats_weights['faceoff'])
			season_rating += (self.data['ratios'][season][player_id]['blocks_ratio'] * self.stats_weights['blocks'])
			season_rating += (self.data['ratios'][season][player_id]['hits_ratio'] * self.stats_weights['hits'])
			season_rating += (self.data['ratios'][season][player_id]['pim_ratio'] * self.stats_weights['pim'])
			season_rating += (self.data['ratios'][season][player_id]['fights_ratio'] * self.stats_weights['fights'])
			season_rating += (self.fantasy_norms[season][player_id] * self.stats_weights['fr'])
			# season_rating += (self.team_fantasy_scores[season].get(self.bios[player_id]['team'], 0) * self.stats_weights['team'])
			season_rating += ((self.data['full'][season][player_id]['gp'] / 82) * self.stats_weights['gp'])
			rating += (season_rating * self.year_weights[season])

		return rating * self.get_age_ratio(player_id) * self.team_weights.get(self.bios[player_id]['team'], 1.0)

	def set_pick(self, player, pick):
		self.meta[player]['picked'] = pick

	def set_note(self, player, note):
		self.meta[player]['note'] = note

	def save_meta(self):
		filename = 'data/json/player_meta.json'
		with open(filename, 'w') as f:
			json.dump(self.meta, f)
	
	def load_meta(self):
		filename = 'data/json/player_meta.json'
		if os.path.exists(filename):
			with open(filename, 'r') as f:
				meta = json.load(f)
		else:
			meta = {}
			for player in self.players:
				meta[player] = {
					'picked': False,
					'note': ''
				}

		return meta

	def load_player_list(self):
		filename = 'player_list.txt'
		with open(filename, 'r') as f:
			return [line.strip() for line in f if line.strip() and self.bios[line.strip()]['active']]


def is_season_type(filename):
	pattern = r'^\d{8}_[a-zA-Z0-9]+'
	return re.match(pattern, filename) is not None





def main():
	dm = DataManager()



if __name__ == "__main__":
	main()
