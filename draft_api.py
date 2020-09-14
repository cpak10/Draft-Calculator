# this script will call Riot API to build a database for all champions picked in a certain rank of ranked games
import requests
import pandas as pd
import time

# setting up overarching data
server = 'https://na1.api.riotgames.com'
api_key = 'api_key=[INSERT API CODE HERE]'

# to keep track of api usage and throttling
api_count = 3

# setting up the larger database for all matches
all_matches = {}
count = 0

# ensuring no duplicate matches
match_dups = {}

# getting all the challenger names
by_queue = '/lol/league/v4/challengerleagues/by-queue/'
queue_type = 'RANKED_SOLO_5x5'
url = server + by_queue + queue_type
challenger_data = requests.get(url, params=api_key)
challenger_data = challenger_data.json()
challenger_data = challenger_data.get('entries')
challenger_names = {}
for i in challenger_data:
    name = i.get('summonerName')
    challenger_names[name] = [str(name), 0]
challenger_user = pd.DataFrame.from_dict(challenger_names, orient='index')

# limiting the runs, remove this when dev api comes through
challenger_user = challenger_user.head(1000)

# getting player data by name
def getting_matches(user):
    name, throw = user
    player_url = '/lol/summoner/v4/summoners/by-name/'
    player_name = name
    player_request = server + player_url + player_name
    player_response = requests.get(player_request, params=api_key)
    player_dict = player_response.json()
    player_id = player_dict.get('accountId')

    # getting previous match history from player id
    player_history_url = '/lol/match/v4/matchlists/by-account/'
    player_history_request = server + player_history_url + player_id
    player_history_response = requests.get(player_history_request, params=api_key)
    player_game_history_raw = player_history_response.json()
    player_game_history = player_game_history_raw.get('matches')
    player_game_history_df = pd.DataFrame.from_dict(player_game_history)
    player_game_history_ids = player_game_history_df['gameId']

    # getting match data, parallelized with pandas apply function
    matches_url = '/lol/match/v4/matches/'
    def match_data(row):
        raw_match_id = row
        match_id = str(raw_match_id)
        if match_id not in match_dups:
            global api_count
            api_count += 1
            match_dups[match_id] = 0
            matches_request = server + matches_url + match_id
            matches_response = requests.get(matches_request, params=api_key)
            matches_dict = matches_response.json()
            match_queue_id = matches_dict.get('queueId')
            match_patch = matches_dict.get('gameVersion')[0:5]
            if match_queue_id == 420 and match_patch == '10.16':
                two_teams_dict = {}
                match_team_data = matches_dict.get('teams')
                for i in match_team_data:
                    team_id = i.get('teamId')/100
                    team_win = i.get('win')
                    if team_win == 'Fail':
                        team_win = 0
                    else:
                        team_win = 1
                    two_teams_dict[team_id] = [('win', team_win)]
                match_participant_data = matches_dict.get('participants')
                for i in match_participant_data:
                    team_id = i.get('teamId')/100
                    champion_id = i.get('championId')
                    player_lane = i.get('timeline').get('lane')
                    two_teams_dict.get(team_id).append((player_lane, champion_id))
                for i in two_teams_dict:
                    global count
                    all_matches[count] = two_teams_dict.get(i)
                    count += 1
        time.sleep(1.5)
        print('{} riot requests'.format(api_count))
    try:
        player_game_history_ids.apply(match_data)
    except:
        pass
try:
    challenger_user.apply(getting_matches, axis=1)
except:
    pass

# bringing the all_matches dictionary to a dataframe, also in the order of roles, excludes the data that do not have clean top, jng, mid, bot, bot
roles_to_col = {'win': 0, 'TOP': 1, 'JUNGLE': 2, 'MIDDLE': 3, 'BOTTOM': 4, 'NONE': 5}
number_matches = pd.DataFrame({'count': range(0, max(all_matches)+1, 1)})
number_matches = number_matches['count']
def format_dict(row):
    i = row
    dups = 10
    match_order_dict = {}
    new_match_order = [0]
    for j in all_matches.get(i):
        role, champ = j
        order = roles_to_col.get(role)
        if order in match_order_dict:
            if order == 4:
                match_order_dict[dups] = champ
                dups += 1
            else:
                new_match_order[0] = 1
                match_order_dict[dups] = champ
                dups += 1
        if order == 5:
            new_match_order[0] = 1
            match_order_dict[order] = champ
        else:
            match_order_dict[order] = champ
    for k in match_order_dict:
        new_match_order.append(match_order_dict.get(k))
    all_matches[i] = new_match_order
number_matches.apply(format_dict)
all_matches = pd.DataFrame.from_dict(all_matches, orient='index', columns=['norm', 'result', 'top', 'jng', 'mid', 'bot1', 'bot2'])
all_matches = all_matches.loc[all_matches['norm'] == 0]
drop = all_matches.pop('norm')
print(all_matches)
all_matches.to_excel('api_test.xlsx')
