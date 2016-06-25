import requests
import json
import xmlrpc.client as xmlrpclib
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


INDEX_URL = 'https://pypi.python.org/pypi'
PACKAGE_URL = 'http://pypi.python.org/pypi/{package}/json'
VERSION_URL = 'http://pypi.python.org/pypi/{package}/{version}/json'

OUTPUT_PATH = os.path.join(os.path.curdir, 'raw')

WORKERS = 8  # Mainly IO bound!


def list_packages():
    """
    Return a list of all available package from PyPi
    """
    client = xmlrpclib.ServerProxy(INDEX_URL)
    return client.list_packages()


def get_package(package):
    """
    Return a list of all available releases for given package name
    """
    req = requests.get(PACKAGE_URL.format(package=package))
    res = json.loads(req.content.decode('utf-8'))
    return res


def get_release(package, version):
    """
    Return all available information about given version for given package
    """
    req = requests.get(VERSION_URL.format(package=package, version=version))
    res = json.loads(req.content.decode('utf-8'))
    return res


def get_package_releases(package):
    logger = logging.getLogger(__name__)
    
    try:
        versions = get_package(package)['releases'].keys()
    except Exception as e: 
        logger.exception('Error while getting package data for {}'.format(package))
        return
    
    logger.info('{}: {} version(s) found'.format(package, len(versions)))
        
    # Create directory if it does not exist
    directory = os.path.join(OUTPUT_PATH, package)
    if not os.path.exists(directory):
        logger.debug('Making directory for {}'.format(package))
        os.mkdir(directory)
    
    for version in versions:     
        filepath = os.path.join(directory, version)
        if not os.path.exists(filepath):
            try:
                release = get_release(package, version)
                # Drop other releases
                release.pop('releases')
            except Exception as e:
                logger.exception('Error while getting release data for version {} of {}'.format(version, package))
                continue
                
            logger.debug('Storing version {} for {}'.format(version, package))
            with open(filepath, 'w') as f: 
                json.dump(release, f)
        else:
            logger.debug('Skipping version {} for {}'.format(version, package))


if __name__ == '__main__':
    # Create directory if it does not exist
    if not os.path.exists(OUTPUT_PATH):
        logging.getLogger(__name__).debug('Creating {} directory'.format(OUTPUT_PATH))
        os.mkdir(OUTPUT_PATH)

    packages = list_packages()

    # Create a pool of (lazy) tasks
    pool = Pool(WORKERS)
    it = pool.imap_unordered(get_package_releases, packages, chunksize=1)

    for _ in tqdm.tqdm(it, desc='Packages', total=len(packages)):
        pass

