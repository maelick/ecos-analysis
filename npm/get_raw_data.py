import requests
import json
import os
import tqdm
import logging
from logging.config import dictConfig
from multiprocessing import Pool

dictConfig(dict(
    version=1,
    formatters={
        'verbose': {'format': '%(asctime)s :: %(levelname)s :: %(message)s'},
    },
    handlers={
        'stream': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'verbose',
        },
        'info_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'filename': 'info.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'filename': 'error.log',
            'formatter': 'verbose',
        },
    },
    loggers={
        __name__: {
            'handlers': ['info_file', 'error_file', ],
            'level': 'DEBUG',
        },
    }
))


REGISTRY_URL = 'https://registry.npmjs.org'

DATA_PATH = os.path.curdir
OUTPUT_PATH = os.path.join(DATA_PATH, 'raw')
PACKAGES_PATH = os.path.join(OUTPUT_PATH, 'packages')

WORKERS = 8  # Mainly IO bound!


def fetch_package_list(dest):
    """
    Fetch npm package list, store the result in dest
    """
    req = requests.get(os.path.join(REGISTRY_URL, '-/all'))
    with open(dest, 'w') as f:
        f.write(req.text.encode('utf-8'))

def get_package(package):
    """
    Return package meta-data
    """
    req = requests.get(os.path.join(REGISTRY_URL, package))
    return req.text

def get_package_metadata(package):
    """
    Fetch package metadata and store the result
    """
    logger = logging.getLogger(__name__)

    logger.info('Fetching metadata for {}'.format(package))

    try:
        metadata = get_package(package)
    except Exception as e:
        logger.exception('Error while getting metadata for {}'.format(package))
        return

    filename = os.path.join('{}/{}.json'.format(PACKAGES_PATH, package))
    with open(filename, 'w') as f:
        f.write(metadata.encode('utf-8'))

if __name__ == '__main__':
    # Create directory if it does not exist
    logger = logging.getLogger(__name__)
    if not os.path.exists(OUTPUT_PATH):
        logger.debug('Creating {} directory'.format(OUTPUT_PATH))
        os.mkdir(OUTPUT_PATH)

    packages_filename = os.path.join(OUTPUT_PATH, 'packages.json')
    fetch_package_list(packages_filename)

    with open(packages_filename) as f:
        packages = json.load(f)

    if not os.path.exists(PACKAGES_PATH):
        logger.debug('Making directory {}'.format(PACKAGES_PATH))
        os.mkdir(PACKAGES_PATH)

    packages = [p.encode('utf-8') for p in packages
                if not os.path.exists('{}/{}.json'.format(PACKAGES_PATH, p))]

    # Create a pool of (lazy) tasks
    pool = Pool(WORKERS)
    it = pool.imap_unordered(get_package_metadata, packages, chunksize=1)

    for _ in tqdm.tqdm(it, desc='Packages', total=len(packages)):
        pass
