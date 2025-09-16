"""
DataManager.py
Basic template for managing fantasy hockey data.
"""

import sys
import os
import json
import pandas as pd

import Ranker

def load_file(type, season):
	return json.load(f'data/json/{season}_{type}.json')

def output(data):
    return pd.DataFrame(data)

def get_averages(season):
	pass

def get_std(season):
    pass

def get_ratios(season):
	pass

def get_totals(season):
	pass

def get_fullset(season):
	pass

def get_rankings():
	return output(Ranker.get_rankings())

def get_player_data(type):
	pass

def main():
	print("DataManager script started.")
	# TODO: Implement data management logic

if __name__ == "__main__":
	main()
