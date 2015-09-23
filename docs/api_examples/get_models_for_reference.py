#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download all the models for a given PMID or doi."""

usage_str = """
Usage:

python get_models_for_reference.py pmid 24277855

or

python get_models_for_reference.py doi "10.1128/ecosalplus.10.2.1"

"""

import requests
from sys import argv, exit
import zipfile
import zlib
import re

def make_url(path, api=False):
    """Make a bigg api request url."""
    if api:
        return 'http://bigg.ucsd.edu/api/v2/%s' % path.lstrip('/')
    else:
        return 'http://bigg.ucsd.edu/%s' % path.lstrip('/')

def escape_for_file(s):
    """Take out invalid characters for a filename."""
    return re.sub('/', '-', s)

def main():
    # check arguments
    if len(argv) != 3:
        print(usage_str)
        exit()
    if argv[1] not in ['pmid', 'doi']:
        print(usage_str)
        exit()

    ref_type, ref = argv[1:3]

    # get the models
    models_r = requests.get(make_url('/models', api=True))
    results = models_r.json()
    models = results['results']
    download_list = []
    for model_summary in models:
        bigg_id = model_summary['bigg_id']
        model_r = requests.get(make_url('/models/%s' % bigg_id, api=True))
        model = model_r.json()
        if model['reference_type'] == ref_type and model['reference_id'] == ref:
            download_list.append(bigg_id)

    print ', '.join(download_list)
    import sys
    sys.exit()

    if len(download_list) == 0:
        print('No matching models were found')
        exit()
    else:
        print('Downloading %d files' % len(download_list))

    # download the models and make a big zip file
    output = escape_for_file('models_%s_%s.zip' % (ref_type, ref))
    zip_file = zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED)
    for bigg_id in download_list:
        print('Downloading %s' % bigg_id)
        sbml_r = requests.get(make_url('/static/dumped_models/%s.xml' % bigg_id))
        sbml_r.encoding = 'utf8'
        sbml = sbml_r.text
        print('Writing %s to zip file' % bigg_id)
        zip_file.writestr('%s.xml' % bigg_id, sbml.encode('utf8'))
    zip_file.close()
    print('Wrote %s' % output)


if __name__ == '__main__':
    main()
