import json
import os
import tqdm
import logging
import gzip
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


DATA_PATH = '/data/npm'
# DATA_PATH = os.path.curdir
OUTPUT_PATH = os.path.join(DATA_PATH, 'raw')
PACKAGES_PATH = os.path.join(OUTPUT_PATH, 'packages')

WORKERS = 8  # Mainly IO bound!


def read_metadata(filename):
    """
    Read JSON filename.
    """
    with open(filename) as f:
        return json.load(f)

def package_filename(package):
    """
    Return package raw metadata filename.
    """
    return os.path.join('{}/{}.json'.format(PACKAGES_PATH, package))

def metadata_exists(package):
    """
    Return True if the package has metadata on disk.
    """
    return os.path.exists(package_filename(package))

def packages_with_metadata(packages):
    """
    Return the list of packages for which there are metadata on disk.
    """
    return filter(metadata_exists, packages)

def check_metadata(packages):
    """
    Check whether package metadata can be parsed as JSON.
    If not, it removes the metadata file.
    """
    logger = logging.getLogger(__name__)
    for p in packages:
        filename = package_filename(p)
        try:
            with open(filename) as f:
                json.load(f)
                logger.info('parsed metadata for {} successfully'.format(p))
        except ValueError as e:
            os.remove(filename)
            logger.error('failed to parsed metadata for {}:\n{}'.format(p, e))

def get_fields(packages):
    """
    Return the number of packages using each package-level and
    version-level fields.
    """
    keys = {}
    keys2 = {}
    logger = logging.getLogger(__name__)
    for p in packages:
        filename = package_filename(p)
        logger.info('gettings fields of {}'.format(p))
        with open(filename) as f:
            md = json.load(f)
        for k in md.keys():
            keys[k] = keys.get(k, 0) + 1
        if 'versions' in md:
            for v in md['versions'].values():
                if type(v) is dict:
                    for k in v.keys():
                        keys2[k] = keys2.get(k, 0) + 1
    return (keys, keys2)


package_fields = ('_id', '_rev', 'name', 'description', 'dist-tags',
                  'keywords', 'versions', 'author', 'contributors',
                  'maintainers', 'users', 'time', 'readmeFilename',
                  'readme', 'homepage', 'repository', 'bugs', 'license')

version_fields = ('name', 'version', 'main', 'scripts', 'keywords', 'author',
                  'license', 'repository', 'bugs', 'homepage', 'dependencies',
                  'devDependencies', 'dist', 'directories', '_npmUser',
                  '_nodeVersion', '_shasum', 'description', 'scripts', 'gitHead',
                  'engines', 'bin', 'contributors', 'licenses', 'files',
                  'peerDependencies', 'readme', 'readmeFilename',
                  'optionalDependencies', 'private', 'config', 'deprecated',
                  'authors', 'tags', 'url', 'title', 'os', 'style')

def get_field_types(packages):
    """
    Return the types of each package-level and version-level fields and the
    number of packages using each of them.
    """
    keys = {k: {} for k in package_fields}
    keys2 = {k: {} for k in version_fields}
    logger = logging.getLogger(__name__)
    for p in packages:
        logger.info('gettings field types of {}'.format(p))
        with open(package_filename(p)) as f:
            md = json.load(f)
        for k in md.keys():
            if k in keys:
                t = type(md[k])
                keys[k][t] = keys[k].get(t, 0) + 1
        if 'versions' in md:
            for v in md['versions'].values():
                if type(v) is dict:
                    for k in v.keys():
                        if k in keys2:
                            t = type(v[k])
                            keys2[k][t] = keys2[k].get(t, 0) + 1
    return (keys, keys2)

def versions(p):
    """
    """
    logger = logging.getLogger(__name__)
    logger.info('gettings versions of {}'.format(p))
    with open(package_filename(p)) as f:
        md = json.load(f)
    if 'time' in md:
        return p, md['time']

def deps(p):
    """
    """
    logger = logging.getLogger(__name__)
    logger.info('gettings dependencies of {}'.format(p))
    with open(package_filename(p)) as f:
        md = json.load(f)
    if 'versions' in md:
        versions = md['versions']
        return p, {v: deps.get('dependencies', None)
                   for v, deps in versions.items()}


if __name__ == '__main__':
    with open(os.path.join(OUTPUT_PATH, 'packages.json')) as f:
        packages = json.load(f)
    packages = packages_with_metadata(packages)
    packages.sort()

    # check_metadata(packages)
    # x, y = get_fields(packages)
    # x, y = get_field_types(packages)

    # Create a pool of (lazy) tasks
    pool = Pool(WORKERS)

    it = pool.imap_unordered(versions, packages, chunksize=1)
    versions = dict(x for x in tqdm.tqdm(it, desc='Versions', total=len(packages))
                    if x is not None)

    it = pool.imap_unordered(deps, packages, chunksize=1)
    deps = dict(x for x in tqdm.tqdm(it, desc='Dependencies', total=len(packages))
                if x is not None)

    with open(os.path.join(OUTPUT_PATH, 'versions.json'), 'w') as f:
        json.dump(versions, f)
    with gzip.GzipFile(os.path.join(OUTPUT_PATH, 'versions.json.gz'), 'w') as f:
        json.dump(versions, f)

    with open(os.path.join(OUTPUT_PATH, 'deps.json'), 'w') as f:
        json.dump(deps, f)
    with gzip.GzipFile(os.path.join(OUTPUT_PATH, 'deps.json.gz'), 'w') as f:
        json.dump(deps, f)
