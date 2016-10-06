import pandas

gems = pandas.read_csv('data/versions.csv')
sizes = pandas.read_csv('data/sizes.csv')

packages = gems[['package', 'version', 'created_at']]
packages = packages.rename(columns={'created_at': 'time'})
packages['time'] = pandas.to_datetime(packages.time)
packages = packages.merge(sizes, how='outer')
packages.to_csv('data/packages.csv')
