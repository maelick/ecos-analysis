import logging
import requests
import tqdm
import pandas
import json
from multiprocessing import Pool

WORKERS = 10
URL = 'https://rubygems.org/api/v1/versions/{}.json'
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def fetch_versions(gem):
    url = URL.format(gem)
    logger.info('Parsing {}'.format(url))
    page = requests.get(url)
    if page.status_code == 200:
        return gem, json.loads(page.content)
    else:
        logger.warning('HTTP {} for {}'.format(page.status_code, url))

gems = pandas.read_csv('data/gems.csv')
pool = Pool(WORKERS)
it = pool.imap_unordered(fetch_versions, gems.package, chunksize=1)
versions = list(tqdm.tqdm(it, desc='Versions', total=len(gems.package)))

with open('data/versions.json', 'w') as f:
    json.dump(dict(versions), f)
