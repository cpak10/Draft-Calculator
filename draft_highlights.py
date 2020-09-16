# this code is to parse the solo/duo queue databases from the API to show popular picks and their win rates
import pandas as pd
import requests

# inputs
pos1 = input('First role: ')
pos2 = input('Second role: ')
bar = int(input('Number of times combo played: '))

# setting up the champion id -> champion name dictionary
champs_list = requests.get('http://ddragon.leagueoflegends.com/cdn/10.18.1/data/en_US/champion.json')
champs_list = champs_list.json()
champs_list = champs_list.get('data')
champ_dict = {}
for i in champs_list:
    champ_data = champs_list.get(i)
    champ_name = champ_data.get('name')
    champ_number = champ_data.get('key')
    champ_dict[champ_number] = champ_name

# reading and combining the databases
df = pd.read_excel('Challenger Patch 10.18 NA.xlsx')
df1 = pd.read_excel('Challenger Patch 10.18 EU.xlsx')
df2 = pd.read_excel('Challenger Patch 10.18 KR.xlsx')
df = df.append(df1)
df = df.append(df2)
df = df[df.columns[-6:]]

# setting up the roles parser
top_jng_dict = {}
def highlights(row):
    result, top, jng, mid, bot1, bot2 = row
    entered_values = {'top': top, 'jng': jng, 'mid': mid, 'bot1': bot1, 'bot2': bot2}
    if pos1 == 'bot1' or pos1 == 'bot2':
        if bot1 > bot2:
            top_jng = str(entered_values.get(pos1)) + ';' + str(entered_values.get(pos2))
        if bot2 > bot1:
            top_jng = str(entered_values.get(pos2)) + ';' + str(entered_values.get(pos1))
        if top_jng in top_jng_dict:
            top_jng_list = top_jng_dict.get(top_jng)
            top_jng_list.append(result)
            top_jng_dict[top_jng] = top_jng_list
        else:
            top_jng_dict[top_jng] = [result]
    else:
        top_jng = str(entered_values.get(pos1)) + ';' + str(entered_values.get(pos2))
        if top_jng in top_jng_dict:
            top_jng_list = top_jng_dict.get(top_jng)
            top_jng_list.append(result)
            top_jng_dict[top_jng] = top_jng_list
        else:
            top_jng_dict[top_jng] = [result]
df.apply(highlights, axis=1)

# parsing the data for combos played over x times
for i in list(top_jng_dict):
    if len(top_jng_dict.get(i)) <= bar:
        top_jng_dict.pop(i)

# calculating win rates
for i in top_jng_dict:
    win_rate = round((sum(top_jng_dict.get(i))/len(top_jng_dict.get(i))) * 100, 2)
    top_jng_dict[i] = [i, win_rate]
top_jng_df = pd.DataFrame.from_dict(top_jng_dict, orient='index', columns=['Name', 'win_rate'])
top_jng_df[['top', 'jng']] = top_jng_df.Name.str.split(';', expand=True)
top_jng_df.pop('Name')

# replacing champion ids for names
data_champ_names = {}
def insert_champ_name(row):
    percent, top, jng = row
    top_jng = str(top) + ';' + str(jng)
    top = champ_dict.get(str(top))
    jng = champ_dict.get(str(jng))
    data_champ_names[top_jng] = [percent, top, jng]
top_jng_df.apply(insert_champ_name, axis=1)
champ_df = pd.DataFrame.from_dict(data_champ_names, orient='index', columns=['win_rate', pos1, pos2])
champ_df = champ_df.sort_values(by=['win_rate'], ascending=False)
print(champ_df)
