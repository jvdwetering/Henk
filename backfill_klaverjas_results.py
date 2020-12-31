import json
import pickle

from managedata import ManageData

m = ManageData()

for i, d in enumerate(m.games.all()):
  print(i, end="\r")
  if d['game_type'] != 100:
    continue
  g = pickle.loads(d['game_data'])
  if g.is_active:
    continue
  m.add_klaverjas_result(g.seed, g.game_id, json.dumps(g.game_result()))

m.klaverjas_results.create_index(['seed'])
