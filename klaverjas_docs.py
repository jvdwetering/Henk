import gspread
from oauth2client.service_account import ServiceAccountCredentials
 
 
# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

key = "1gHqbbzo6vWcjjmXaWVPMXPpM6g_ORTm8dvE9iNP2iq0"
# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open_by_key(key).sheet1
 
# Extract and print all of the values
#list_of_hashes = sheet.get_all_records()
#print(list_of_hashes)


import pickle
from managedata import ManageData

KLAVERJASSEN = 100
KLAVERJASSEN_DISPATCH = 101
KLAVERJASSEN_CHALLENGE = 102

m = ManageData()
class Bot():
    pass

b = Bot()
b.dataManager = m

games = []
for d in m.games.find(game_type=KLAVERJASSEN):
    g = pickle.loads(d['game_data'])
    g.bot = b
    if not hasattr(g,"seed"): continue
    if len(g.real_players) != 1: continue
    if g.is_active == True: continue
    games.append(g)

rows = []
matches = {}
scores = {}
players = {}
for g in games:
    row = []
    n = g.real_players[0].name
    pid = g.real_players[0].user_id
    row.append(n)
    row.append(pid)
    row.append(g.points1)
    row.append(g.points2)
    row.append(g.pointsglory1)
    row.append(g.pointsglory2)
    if g.points1 <= g.points2: row.append("nat")
    else: row.append("")
    if g.points1 == 0 or g.points2 == 0: row.append("pit")
    else: row.append("")
    row.append(g.seed)
    rows.append(row)
    if g.seed in matches: matches[g.seed].append(pid)
    else: matches[g.seed] = [pid]
    if not pid in players: players[pid] = n
    scores[(g.seed,pid)] = g.points1 - g.points2


matchups = {}
for p1 in players:
    for p2 in players:
        if p1>=p2: continue
        matchups[(p1,p2)] = [0,0,0]

for seed,contestants in matches.items():
    for p1,p2 in matchups:
        if p1 in contestants and p2 in contestants:
            if scores[(seed,p1)] > scores[(seed,p2)]:
                matchups[(p1,p2)][0] += 1
            elif scores[(seed,p1)] < scores[(seed,p2)]:
                matchups[(p1,p2)][1] += 1
            else:
                matchups[(p1,p2)][2] += 1

for (p1, p2),(w,l,d) in matchups.items():
    print("{}|{}: {!s}|{!s}|{!s}".format(players[p1],players[p2],w,l,d))
