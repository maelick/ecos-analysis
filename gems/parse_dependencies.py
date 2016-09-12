import logging
import requests
import tqdm
import pandas
import json
import os.path
from multiprocessing import Pool

WORKERS = 6
URL = 'https://rubygems.org/api/v2/rubygems/{}/versions/{}.json'
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def gem_filename(gem):
    return 'data/dependencies/{}.json'.format(gem)

def get_dependencies(gem, version, deps):
    deps = pandas.DataFrame(deps['runtime'])
    deps['package'] = gem
    deps['version'] = version
    deps = deps.rename(columns={'name': 'dependency',
                                'requirements': 'constraint'})
    return deps.set_index(['package', 'version'])

def read_gem(gem):
    filename = gem_filename(gem)
    try:
        versions = json.load(open(gem_filename(gem)))
    except IOError:
        logger.warning('Can\'t read {}'.format(filename))
    else:
        deps = [get_dependencies(gem, k, v['dependencies'])
                for k, v in versions.items()]
        return pandas.concat(deps)

gems = set(pandas.read_csv('data/versions.csv').package)
gems = [g for g in gems if os.path.exists(gem_filename(g))]
pool = Pool(WORKERS)
it = pool.imap_unordered(read_gem, gems, chunksize=1)

deps = pandas.concat(tqdm.tqdm(it, desc='Dependencies', total=len(gems)))

gems = set(pandas.read_csv('data/versions.csv').package)
deps = deps[[d in gems for d in deps.dependency]]
deps.ix[deps.constraint == ">= 0", 'constraint'] = '*'

deps.to_csv('data/deps.csv')
