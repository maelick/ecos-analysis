import pandas

def cmp_versions(v1, v2):
    v1, v2 = v1.split('.'), v2.split('.')
    v1 = [int(x) for x in v1 if len(x)]
    v2 = [int(x) for x in v2 if len(x)]
    for x1, x2 in zip(v1, v2):
        if x1 < x2:
            return -1
        elif x1 > x2:
            return 1
    return len(v1) - len(v2)

def latest_version(v1, v2):
    if cmp_versions(v1, v2) < 0:
        return v2
    else:
        return v1

def max_version(versions):
    return reduce(latest_version, versions, '0')

def last_version(group):
    if len(group) == 1:
        return group
    else:
        versions = group.version.str.replace('[a-zA-Z]+', '')
        return group[versions == max_version(versions)].head(1)

def replace_subset(packages, q):
    sub = packages.query(q).groupby('package').apply(last_version)
    sub = sub.reset_index(drop=True)
    return packages.query('not ({})'.format(q)).append(sub)

packages = pandas.read_csv('data/packages.csv').drop_duplicates(['package', 'version'])
packages = replace_subset(packages, "time >= '2014-08-10 18:53:00' and time < '2014-08-11 09:26:00'")
packages = replace_subset(packages, "time >= '2009-07-25' and time < '2009-07-26'")
packages = packages.set_index(['package', 'version'])

packages.to_csv('data/packages.csv')

deps = pandas.read_csv('data/deps.csv').set_index(['package', 'version'])[['dependency', 'constraint']]
deps = deps.reset_index().merge(packages, right_index=True, left_on=['package', 'version'])
deps = deps[['dependency', 'constraint']]
deps.to_csv('data/deps.csv')
