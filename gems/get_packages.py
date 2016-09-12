import logging
import requests
import tqdm
import pandas
import itertools
from lxml import html
from multiprocessing import Pool

WORKERS = 10
ROOT_URL = 'https://rubygems.org/{}'
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def parse(url):
    logger.info('Parsing {}'.format(url))
    page = requests.get(url)
    if page.status_code == 200:
        return page.content, html.fromstring(page.content)
    else:
        logger.warning('HTTP {} for {}'.format(page.status_code, url))

def get_gem(e):
    link = e.get('href')
    package = e.xpath('.//h2[@class="gems__gem__name"]/text()')
    desc = e.xpath('.//p[@class="gems__gem__desc t-text"]/text()')
    downloads = e.xpath('.//p[@class="gems__gem__downloads__count"]/text()')
    return (link,
            package[0].strip(),
            desc[0] if desc else '',
            downloads[0].strip())

def get_pages():
    _, tree = parse(ROOT_URL.format('gems'))
    return tree.xpath('//a[@class="gems__nav-link"]/@href')

def get_next_page(tree):
    return tree.xpath('//a[@class="next_page"]/@href')

def get_gems(page):
    next_page = [page]
    gems = []
    while next_page:
        _, tree = parse(ROOT_URL.format(next_page[0]))
        gems.extend(map(get_gem, tree.xpath('//a[@class="gems__gem"]')))
        next_page = get_next_page(tree)
    return gems

pages = get_pages()

pool = Pool(WORKERS)
it = pool.imap_unordered(get_gems, pages, chunksize=1)
gems = list(it)

gems = pandas.DataFrame(list(itertools.chain.from_iterable(gems)),
                        columns=('url', 'package', 'desc', 'downloads'))
gems[['url', 'package', 'downloads']].to_csv('data/gems.csv', encoding='utf-8', index=False)
