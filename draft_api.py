# this script will call Riot API to build a database for all champions picked in a certain rank of ranked games
import requests
import pandas as pd
import time
import threading

# dictionary of all champions
champs_list = requests.get('http://ddragon.leagueoflegends.com/cdn/10.18.1/data/en_US/champion.json')
champs_list = champs_list.json()
champs_list = champs_list.get('data')
champ_dict = {}
for i in champs_list:
    champ_data = champs_list.get(i)
    champ_name = champ_data.get('name')
    champ_number = champ_data.get('key')
    champ_dict[champ_number] = champ_name

# counter variables
# api for throttle
api_count = {'NA': 3, 'EU': 3, 'KR': 3}
# count for dict building
count = {'NA': 0, "EU": 0, 'KR': 0}
# champ name count
champ_name_count = {'NA': 0, 'EU': 0, 'KR': 0}

# start of the function for individual region calls
def api_calls(region):
    print("{} region is running at time: ".format(region) + str(int(time.time())) + " seconds.")
    
    # setting up overarching data and regions
    regions = {'NA': 'https://na1.api.riotgames.com', 'EU': 'https://euw1.api.riotgames.com', 'KR': 'https://kr.api.riotgames.com'}
    server = regions.get(region)
    api_key = 'RGAPI-e01ff298-6fa3-43bb-914c-b0e3a0a6daf5'
    api_key = 'api_key=' + api_key

    # setting up the larger database for all matches
    all_matches = {}

    # ensuring no duplicate matches
    match_dups = {}

    # getting all the challenger names, expand it to run it on four main servers at same time
    by_queue = '/lol/league/v4/challengerleagues/by-queue/'
    queue_type = 'RANKED_SOLO_5x5'
    url = server + by_queue + queue_type
    challenger_data = requests.get(url, params=api_key)
    time.sleep(1.21)
    if challenger_data.status_code == 200:
        pass
    else:
        print(challenger_data)
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
        try:
            name, throw = user
            player_url = '/lol/summoner/v4/summoners/by-name/'
            player_name = name
            player_request = server + player_url + player_name
            player_response = requests.get(player_request, params=api_key)
            time.sleep(1.21)
            if player_response.status_code == 200:
                pass
            else:
                print(player_response)
            player_dict = player_response.json()
            player_id = player_dict.get('accountId')

            # getting previous match history from player id
            player_history_url = '/lol/match/v4/matchlists/by-account/'
            player_history_request = server + player_history_url + player_id
            player_history_response = requests.get(player_history_request, params=api_key)
            time.sleep(1.21)
            if player_history_response.status_code == 200:
                pass
            else:
                print(player_history_response)
            player_game_history_raw = player_history_response.json()
            player_game_history = player_game_history_raw.get('matches')
            player_game_history_df = pd.DataFrame.from_dict(player_game_history)
            player_game_history_ids = player_game_history_df['gameId']

            # getting match data, parallelized with pandas apply function
            matches_url = '/lol/match/v4/matches/'
            def match_data(row):
                try:
                    raw_match_id = row
                    match_id = str(raw_match_id)
                    if match_id not in match_dups:
                        api_count[region] = api_count.get(region) + 1
                        match_dups[match_id] = 0
                        matches_request = server + matches_url + match_id
                        matches_response = requests.get(matches_request, params=api_key)
                        time.sleep(1.21)
                        if matches_response.status_code == 200:
                            pass
                        else:
                            print(matches_response)
                        matches_dict = matches_response.json()
                        match_queue_id = matches_dict.get('queueId')
                        match_patch = matches_dict.get('gameVersion')
                        if match_queue_id == 420 and '10.18' in match_patch:
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
                                all_matches[count.get(region)] = two_teams_dict.get(i)
                                count[region] = count.get(region) + 1
                    print('{} riot requests to {} server'.format(api_count.get(region), region))
                except:
                    print('{} riot requests to {} server'.format(api_count.get(region), region))
            player_game_history_ids.apply(match_data)
        except:
            print('{} riot requests to {} server'.format(api_count.get(region), region))
    challenger_user.apply(getting_matches, axis=1)

    # bringing the all_matches dictionary to a dataframe, also in the order of roles, excludes the data that do not have clean top, jng, mid, bot, bot
    roles_to_col = {'win': 0, 'TOP': 1, 'JUNGLE': 2, 'MIDDLE': 3, 'BOTTOM': 4, 'NONE': 5}
    number_matches = pd.DataFrame({'count': range(0, max(all_matches)+1, 1)})
    number_matches = number_matches['count']
    def format_dict(row):
        i = row
        dups = 6
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
            if order not in match_order_dict:
                match_order_dict[order] = champ
        for k in range(0, 11):
            try:
                if match_order_dict.get(k) >= 0:
                    new_match_order.append(match_order_dict.get(k))
            except:
                pass
        try:
            all_matches[i] = new_match_order
        except:
            pass
    try:    
        number_matches.apply(format_dict)
    except:
        pass
    all_matches = pd.DataFrame.from_dict(all_matches, orient='index', columns=['norm', 'result', 'top', 'jng', 'mid', 'bot1', 'bot2'])
    all_matches = all_matches.loc[all_matches['norm'] == 0]
    drop = all_matches.pop('norm')
    print('here is the raw data from {}'.format(region))
    print(all_matches)
    all_matches.to_excel('Challenger Patch 10.18 ' + region + '.xlsx')

    # to make it readable and pretty
    data_champ_names = {}
    def insert_champ_name(row):
        result, top, jng, mid, bot1, bot2 = row
        top = champ_dict.get(str(top))
        jng = champ_dict.get(str(jng))
        mid = champ_dict.get(str(mid))
        bot1 = champ_dict.get(str(bot1))
        bot2 = champ_dict.get(str(bot2))
        data_champ_names[champ_name_count.get(region)] = [result, top, jng, mid, bot1, bot2]
        champ_name_count[region] = champ_name_count.get(region) + 1
    all_matches.apply(insert_champ_name, axis=1)
    champ_df = pd.DataFrame.from_dict(data_champ_names, orient='index', columns=['result', 'top', 'jng', 'mid', 'bot1', 'bot2'])
    print('here is the clean data from {}'.format(region))
    print(champ_df)
    champ_df.to_excel('Challenger Patch 10.18 ' + region + ' Champion Names.xlsx')

# initiating multiple region calls with threading
threading.Thread(target=api_calls, args=('NA',)).start()
threading.Thread(target=api_calls, args=('KR',)).start()
threading.Thread(target=api_calls, args=('EU',)).start()