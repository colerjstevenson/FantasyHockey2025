# get list of all players who played at least 30 games in one of the last 3 seasons
from nhlpy import NHLClient

def main():
    seasons= ['20242025', '20232024']
    player_list = []
    for season in seasons:
        player_ids = get_roster_player_ids(season)
        print(len(player_ids), "players found in " + season)
        player_list.extend(player_ids)
    player_list = list(set(player_list))
    # Save player list to txt file
    with open("player_list.txt", "w") as f:
        for player_id in player_list:
            f.write(str(player_id) + "\n")
    

def get_roster_player_ids(season):
    """
    Returns a dict mapping playerId -> playerName for all players rostered
    in those seasons across all teams.
    """
    client = NHLClient()
    teams = client.teams.teams()
    team_ids = [team['franchise_id'] for team in teams]
    players = []
    for id in team_ids:
        skater_stats = client.stats.skater_stats_summary(
                            start_season=season, 
                            end_season=season,
                            franchise_id=id,
                            limit=1000,
                            fact_cayenne_exp="gamesPlayed>=30"
                        )
        players += skater_stats

    return list(set([p['playerId'] for p in players]))


if __name__ == "__main__":
    main()

