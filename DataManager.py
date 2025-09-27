"""
DataManager.py
Basic template for managing fantasy hockey data.
"""

import sys
import os
import re
import json
import pandas as pd
import numpy as np




class DataManager:
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
			'points': 0.1,
			'plusMinus': 0.2,
			'shg': 0.2,
			'faceoff': 0.4,
			'blocks': 0.6,
			'hits': 0.9,
			'pim': 0.6,
			'gp': 0.5,
			'fights': 0.8,
			'age': 0.4
		}

		self.year_weights = {
			'20222023': 0.3,
			'20232024': 0.6,
			'20242025': 0.8
		}



		self.data = {}
		self.bios = json.load(open('data/json/player_bios.json'))
		self.players = self.load_player_list()
		self.seasons = ['20222023', '20232024', '20242025']
		self.meta = self.load_meta()
		self.base = {}

		#load bulk of data
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

		#add fights and faceoffs to ratios
		for player in self.players:
			for season in self.seasons:
				if player in self.data['full'][season]:
					self.data['ratios'][season][player]['faceoff_ratio'] = self.data['full'][season][player]['faceoff_ratio']
					self.data['ratios'][season][player]['fights_ratio'] = self.data['full'][season][player]['fights_ratio']
					self.data['ratios'][season][player]['age_ratio'] = self.get_age_ratio(player)

		#store normalized versions of ratios
		self.data['norms'] = {}
		for season in self.seasons:
			self.data['norms'][season] = self.normalize_ratios(season)



		# store player data
		for player in self.players:
			self.base[player] = {
				'Team': self.bios[player]['team'],
				'ID': player,
				'Name': self.bios[player]['name'],
				'Pos': self.bios[player]['position'],
				'Age': self.bios[player]['age']
			}


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

		fp = 0
		for v in values.keys():
			fp += self.data['full'][season][player][v] * values[v]
		
		return fp / self.data['full'][season][player]['gp']


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
			season_rating += ((self.data['full'][season][player_id]['gp'] / 82) * self.stats_weights['gp'])
			rating += (season_rating * self.year_weights[season])

		return rating * self.get_age_ratio(player_id)

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
