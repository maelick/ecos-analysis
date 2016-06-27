from packaging.version import Version, InvalidVersion
from packaging.requirements import Requirement
import logging
import csv

DEBUG = False

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR if not DEBUG else logging.DEBUG)


INPUT_FILEPATH = 'data/packages.csv'

def order_versions(versions):
    """
    Return an ordered list of versions (containing version strings)
    """
    return sorted(versions, key=Version)


def is_version(version):
    """
    Return True if given string is a proper version number.
    """
    try:
        Version(version)
        return True
    except (TypeError, InvalidVersion) as e: 
        return False


def load_data(csv_filepath):
    """
    Return a dict d of dict v of list m such that:
    d is a mapping from package name to a dict of distributions v. 
    v is a mapping from versions (packaging.version.Version object) to a list of 
    dependencies (packaging.requirements.Requirement objects).
    """
    with open(INPUT_FILEPATH) as f: 
        content = csv.reader(f.readlines())

    # Drop headers
    headers = {value: index for index, value in enumerate(content.__next__())}


    d = {}
    for distribution in content: 
        name = distribution[headers['info_name']]
        version = distribution[headers['info_version']]
        requires = distribution[headers['info_requires']]
        requires_dist = distribution[headers['info_requires_dist']]

        try:
            version = Version(version)
        except (TypeError, InvalidVersion) as e: 
            LOGGER.warning('Invalid version %s for %s' % (version, name))
            continue

        v = d.setdefault(name, {})
        m = v.setdefault(version, [])

        try:
            requires = eval(requires) if len(requires) > 0 else []
        except Exception as e: 
            LOGGER.debug('Parse error for %s in %s, %s' % (requires, name, version))
            raise

        try:
            requires_dist = eval(requires_dist) if len(requires_dist) > 0 else []
        except Exception as e: 
            LOGGER.debug('Parse error for %s in %s, %s' % (requires_dist, name, version))
            raise

        dependencies = set(requires).union(requires_dist)

        for dependency in dependencies:
            try:
                m.append(Requirement(dependency))
            except Exception as e:
                LOGGER.debug('Invalid dependency %s for %s, %s' % (dependency, name, version))

    return d
    

