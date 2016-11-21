#!/usr/bin/env python3

import pandas as pd
import requests
# from functools import lru_cache
from IPython.display import HTML, display

host = 'http://bigg.ucsd.edu/api/v2/'

# @lru_cache(maxsize=200)
def get_metabolite(bigg_id):
    req = requests.get(host + 'universal/metabolites/' + bigg_id)
    try:
        req.raise_for_status()
    except Exception as e:
        print(bigg_id)
        raise e
    return req.json()

not_dups = ['MNXM12007', 'MNXM12009', 'MNXM12012', 'MNXM12014', 'MNXM12016',
            'MNXM12019', 'MNXM12021', 'MNXM12023', 'MNXM12025', 'MNXM2',
            'MNXM2379', 'MNXM41358', 'MNXM9451', 'MNXM643', 'MNXM8637',
            'MNXM6536', 'MNXM491', 'MNXM626', 'MNXM685', 'MNXM710', 'MNXM9139',
            'MNXM920', 'MNXM41', 'MNXM147330', 'MNXM147331', 'MNXM147332',
            'MNXM3903', 'MNXM4851', 'MNXM75042', 'MNXM147493', 'MNXM1623',
            'MNXM1206', 'MNXM3863', 'MNXM7865']
prefer = ['cmpacna', '2ameph', 'guln__L', 'cysi__L', 'forcoa', '3ohodcoa',
          'urcan', 'tag__D', '4izp', '5g2oxpt', 'ckdo', 'kdolipid5', 'fdxr_42',
          'fdxo_42', 'frmd', 'phllqne', '5cmhm', '4h2opntn', 'udcpo4', '2ohed',
          '5cmhmsa', '4cml', 'fdxrd', 'applp', 'scys__L', 'gtocophe', 'copre4',
          'hpglu', 'mhpglu', 'coucoa', 'codhpre6', 'avite1', 'op4en', 'cph4',
          'hemeA', 'bvite', 'salcn6p', 'quin', 'copre2', 'dptne', 'colipa',
          'focytc', 'caro', 'dscl', 'hphhlipa']
additional = [
    ['glc__bD', 'glc_bD', 'glc_B'],
    ['glc__aD', 'Glc_aD', 'glc_A'],
]

# load dups tables
df = pd.read_table('dups.txt', sep='\t', names=['mnx', 'bigg_id', 'tag', 'name'])
df.bigg_id = df.bigg_id.str.replace('bigg:', '')
df = df.drop('tag', axis='columns')
df = df[~df.mnx.isin(not_dups)]

# apply preferences
prefs = []; missing = []; new_not_dups = []
for mnx, group in df.groupby('mnx'):
    mets = []
    found_pref = False
    for ind, row in group.iterrows():
        bigg_id = row.bigg_id
        d = get_metabolite(bigg_id)
        models = set(x['model_bigg_id'] for x in d['compartments_in_models'])
        # check list of preferred BiGG IDs
        if bigg_id in prefer:
            found_pref = bigg_id
        # lowest preference for STM_v1_0 and iRC1080
        elif models in [set(['STM_v1_0']), set(['iRC1080'])] and len(group) == 2:
            found_pref = group[group.bigg_id != bigg_id].iloc[0].bigg_id
        mets.append([bigg_id, models])
    if all(models == mets[0][1] for _, models in mets):
        new_not_dups.append(mnx)
    elif not found_pref:
        print(mnx)
        missing.append(mnx)
        for bigg_id, models in mets:
            display(HTML("<a href='http://bigg.ucsd.edu/universal/metabolites/%s' target='none'>%s</a>" % (bigg_id, bigg_id)))
            print(models)
        print('\n--\n')
    else:
        prefs.append([found_pref] + [met for met, _ in mets if met != found_pref])

# add additional rows
prefs += additional

# save
pd.DataFrame(prefs).to_csv('metabolite-duplicates.txt', sep='\t', index=False, header=None)

print('done')
