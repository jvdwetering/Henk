import time

import dataset

from managedata import ManageData

m = ManageData()

gamedb = dataset.connect('sqlite:///gamedata.db?check_same_thread=False')

g = gamedb['Games']

for d in m.games.all():
    delta = (time.time()-d['date'])/(3600*24)
    if delta > 12: # older than a week
        ident = d['id']
        del d['id']
        g.insert(d)
        m.games.delete(id=ident)
        
