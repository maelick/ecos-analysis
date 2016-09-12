import logging
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

gems = pandas.read_csv('data/versions.csv')
sizes = pandas.read_csv('data/sizes.csv')

packages = gems[['package', 'version', 'created_at']]
packages = packages.rename(columns={'created_at': 'time'})
packages['time'] = pandas.to_datetime(packages.time)
packages = packages.merge(sizes, how='outer')
packages.to_csv('data/packages.csv')
