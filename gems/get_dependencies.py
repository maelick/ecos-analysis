import logging
import requests
import tqdm
import pandas
import json
import os.path
from multiprocessing import Pool

WORKERS = 10
URL = 'https://rubygems.org/api/v2/rubygems/{}/versions/{}.json'
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def fetch_dependencies(package, version):
    url = URL.format(package, version)
    logger.debug('Parsing {}'.format(url))
    page = requests.get(url)
    if page.status_code == 200:
        return json.loads(page.text)
    else:
        logger.warning('HTTP {} for {}'.format(page.status_code, url))

def gem_filename(gem):
    return 'data/dependencies/{}.json'.format(gem)

def fetch_gem(gem):
    gem, versions = gem
    filename = gem_filename(gem)
    if not os.path.exists(filename):
        logger.info('Fetch dependencies for {}'.format(gem))
        deps = {v: fetch_dependencies(gem, v) for v in versions.version}
        if all(map(bool, deps.values())):
            with open(filename, 'w') as f:
                json.dump(deps, f)
        else:
            logger.warning('Did not saved deps for {}'.format(gem))

gems = pandas.read_csv('data/versions.csv')
gems = [g for g in gems.groupby('package')
        if not os.path.exists(gem_filename(g[0]))]
pool = Pool(WORKERS)
it = pool.imap_unordered(fetch_gem, gems, chunksize=1)
