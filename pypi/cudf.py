from packaging.version import Version, InvalidVersion
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name
import logging
import csv
import tqdm

DEBUG = False

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR if not DEBUG else logging.DEBUG)


INPUT_FILEPATH = 'data/metadata.csv'
OUTPUT_FILEPATH = 'data/cudf.txt'


def matched_versions(versions, specifier):
    """
    Return items from versions that match given specifier 
    (a packaging.specifier.SpecifierSet object). 
    """
    return list(specifier.filter(versions))


def load_data(csv_filepath, show_progress=False):
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
    if show_progress:
        content = tqdm.tqdm(content, smoothing=0.9)

    for i, distribution in enumerate(content): 
        name = canonicalize_name(distribution[headers['info_name']])
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
            except InvalidRequirement as e:
                LOGGER.debug('Invalid dependency %s for %s, %s' % (dependency, name, version))

    if show_progress:
        print()

    return d
    

if __name__ == '__main__':
    # Get data
    print('Loading data')
    data = load_data(INPUT_FILEPATH, show_progress=True)

    # For each package, create a mapping between "python version" to "canonical version"
    print('Create versions mapping')
    mapping = {}
    for package, distributions in tqdm.tqdm(data.items()):
        versions = distributions.keys()
        mapping[package] = {v: i + 1 for i, v in enumerate(sorted(versions))}


    print('Canonicalizing requirements')
    output = []
    for package, distributions in tqdm.tqdm(data.items(), smoothing=0.9):
        for version, requirements in tqdm.tqdm(distributions.items(), desc=package[:8], leave=False):
            canonical_requirements = {}

            for requirement in requirements:
                name = canonicalize_name(requirement.name)
                versions = mapping.get(name, None)
                                
                if versions is None:
                    LOGGER.info('Unknown package %s for requirement %s (%s, %s)' % (name, requirement, package, version))
                    canonical_requirements[name] = []
                    continue

                matched = matched_versions(versions.keys(), requirement.specifier)
                canonical_matched = [versions[v] for v in matched]
                canonical_requirements[name] = canonical_matched

            output.append((package, mapping[package][version], canonical_requirements))

    print('Export to CUDF')
    with open(OUTPUT_FILEPATH, 'w') as f:
        for package, version, requirements in tqdm.tqdm(output):
            f.write('package: %s\n' % package)
            f.write('version: %d\n' % version)
            f.write('conflicts: %s\n' % package)
            if len(requirements) > 0:
                f.write('depends: ')

                depends = []
                for name, versions in requirements.items():
                    s = ' | '.join(['{} = {}'.format(name, version) for version in versions])
                    if len(s) > 0:
                        depends.append(s)
                    else:
                        depends.append(name)

                f.write(', '.join(depends))
                f.write('\n')
            f.write('\n')     
    print('Done')
