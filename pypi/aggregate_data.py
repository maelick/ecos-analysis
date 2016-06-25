
"""
This scripts expects a "raw.tar.gz" (see INPUT_FILEPATH) to be available. 
This file must contains all the metadata extracted from PyPi using the 
"get_raw_data.py" scripts.

The file raw.tar.gz available on the repository was created the 24th of June, 
downloading meta-data for 80 939 packages (83 151 packages were listed by PyPi, 
but the data weren't available for 2212 of them).
"""


import os
import json
import tarfile
import pandas


INPUT_FILEPATH = 'data/raw.tar.gz'
OUTPUT_FILEPATH = 'data/packages.csv'

FIELDS = dict(
    info=['name', 'version', 'author', 'home_page', 'licence', 
          'maintainer', 'requires', 'requires_dist'], 
    urls=['size', 'upload_time', 'packagetype', 'downloads']  # urls is a list of dict (in package metadata)
)


def filter_data(data):
    ndata = {}
    
    info = data['info']
    
    try:
        urls = data['urls'][0]
    except IndexError:
        urls = {}
        
    for key in FIELDS['info']:
        ndata['info_{}'.format(key)] = info.get(key, None)
    for key in FIELDS['urls']:
        ndata['urls_{}'.format(key)] = urls.get(key, None)
    return ndata


if __name__ == '__main__':
    tar = tarfile.open(INPUT_FILEPATH, mode='r:gz')

    data = []
    for item in tar.getmembers():
        if item.isfile():
            with tar.extractfile(item) as f:
                binary_data = '\n'.join((x.decode('utf-8') for x in f.readlines()))
                package_data = json.loads(binary_data)
                data.append(filter_data(package_data))

    df = pandas.DataFrame.from_dict(data)
    df.to_csv(OUTPUT_FILEPATH, index=False)

