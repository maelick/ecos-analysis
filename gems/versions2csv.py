import logging
import requests
import tqdm
import pandas
import json
import itertools
from multiprocessing import Pool

WORKERS = 6
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def version(package, version):
    licenses = version['licenses']
    licenses = ';'.join(licenses) if licenses else ''
    return (package, version['number'], version['authors'], version['built_at'],
            version['created_at'], version['downloads_count'], licenses)

gems = json.load(open('data/versions.json'))

versions = [[version(p, v) for v in versions] for p, versions in gems.items()]
versions = pandas.DataFrame(list(itertools.chain.from_iterable(res)),
                            columns=('package', 'version', 'authors',
                                     'built_at', 'created_at', 'downloads',
                                     'licenses'))

versions.to_csv('data/versions.csv', index=False, encoding='utf-8')
