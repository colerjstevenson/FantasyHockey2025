"""
DataManager.py
Basic template for managing fantasy hockey data.
"""

import sys
import os
import json
import pandas as pd

import Ranker

class DataManager:
    def __init__(self):
        self.data = {}
        json_dir = os.path.join('data', 'json')
        for filename in os.listdir(json_dir):
            if filename.endswith('.json'):
                type = filename.replace('.json', '').split('_')[-1]
                season = filename.split('_')[0]
                if type in self.data.keys():
                     self[type][season] = self.load_file(type, season)
                
                    
    def load_file(self, type, season):
        return json.load(open(f'data/json/{season}_{type}.json'))

    def output(self, data):
        return pd.DataFrame(data)

    def get_averages(self, season):
        pass

    def get_std(self, season):
        pass

    def get_ratios(self, season):
        pass

    def get_totals(self, season):
        pass

    def get_fullset(self, season):
        pass

    def get_rankings(self):
        return self.output(Ranker.get_rankings())

    def get_player(self, player_id):
        pass

    def get_player_data(self, type):
        pass

def main():
	dm = DataManager()
    
     

if __name__ == "__main__":
	main()
