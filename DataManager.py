"""
DataManager.py
Basic template for managing fantasy hockey data.
"""

import sys
import os
import re
import json
import pandas as pd




class DataManager:
	def __init__(self):
		self.stats_weights = {
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

		self.year_weights = {
			'20222023': 0.3,
			'20232024': 0.6,
			'20242025': 0.8
		}



		self.data = {}
		self.bios = json.load(open('data/json/player_bios.json'))
		self.players = self.load_player_list()
		self.seasons = ['20222023', '20232024', '20242025']
		self.base = {}

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

		print(self)
		for player in self.players:
			self.base[player] = {
				'Team': self.bios[player]['team'],
				'Name': self.bios[player]['name'],
				'Pos': self.bios[player]['position'],
			}



	def load_file(self, type, season):
		try:
			return json.load(open(f'data/json/{season}_{type}.json'))
		except:
			print("file not found")
			return {}
			

	def toCVS(self, data):
		return pd.DataFrame(data)
	
	def stage_data(self, player, season, dataset=None, no_rank=False):
		stats = ['hits', 'blocks', 'pim', 'faceoff', 'shg', 'plusMinus', 'points', 'fights']
		if dataset:
			tag = '_' + dataset
		else:
			tag = ''

		out = {}

		if not no_rank:
			out['Rating'] = self.get_rating(player)

		for stat in stats:
			out[stat+tag] = self.data['full'][season][player].get(stat+tag, 0)

		return out

	def get_averages(self, season):
		output = []
		for player in self.players:
			stats = self.stage_stats(player, season, 'avg')
			output.append({**self.base[player], **stats})

		return output

	def get_std(self, season):
		output = []
		for player in self.players:
			stats = self.stage_stats(player, season, 'sd')
			output.append({**self.base[player], **stats})

		return output

	def get_ratios(self, season):
		output = []
		for player in self.players:
			stats = self.stage_stats(player, season, 'ratio')
			output.append({**self.base[player], **stats})

		return output

	def get_totals(self, season):
		output = []
		for player in self.players:
			stats = self.stage_stats(player, season)
			output.append({**self.base[player], **stats})

		return output

	def get_fullset(self, season):
		output = []

		for player in self.players:
			if player in self.data['full'][season].keys():
				tot = self.stage_data(player, season, no_rank=True)
				avg = self.stage_data(player, season, dataset='avg', no_rank=True)
				sd = self.stage_data(player, season, dataset='sd', no_rank=True)
				rat = self.stage_data(player, season, dataset='ratio')

				output.append({**self.base[player], **rat, **tot, **avg, **sd})
		
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
			season_rating += (self.data['full'][season][player_id]['faceoff_ratio'] * self.stats_weights['faceoff'])
			season_rating += (self.data['ratios'][season][player_id]['blocks_ratio'] * self.stats_weights['blocks'])
			season_rating += (self.data['ratios'][season][player_id]['hits_ratio'] * self.stats_weights['hits'])
			season_rating += (self.data['ratios'][season][player_id]['pim_ratio'] * self.stats_weights['pim'])
			season_rating += (self.data['full'][season][player_id]['fights_ratio'] * self.stats_weights['fights'])
			season_rating += ((self.data['full'][season][player_id]['gp'] / 82) * self.stats_weights['gp'])
			rating += (season_rating * self.year_weights[season])

		return rating

	def get_player(self, player_id):
		pass

	def get_player_data(self, type):
		pass


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
