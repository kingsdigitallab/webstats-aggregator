#!/usr/bin/python3

from bs4 import  BeautifulSoup
from urllib.request import urlopen
from urllib.error import URLError
from ssl import CertificateError
import json
import unicodedata

AWSTATS_PATH = 'awstats.pl?month=all&output=main&config=languageacts-webstats.kdl.kcl.ac.uk&framename=mainright&year='
VHOSTS_FILE='/vol/csg/auto/allvhosts'
WEBSTATS_HOSTS = []

WEBSTATS = {}

WEBSTATS['_all'] = {}
WEBSTATS['_all']['totals'] = {}
WEBSTATS['_all']['totals']['unique'] = 0
WEBSTATS['_all']['totals']['visits'] = 0
WEBSTATS['_all']['totals']['views'] = 0
WEBSTATS['_all']['totals']['hits'] = 0

# Let's get all of our 'webstats' urls:

with open(VHOSTS_FILE, 'r') as f:
    for line in f:
        hosts = line.split(':')
        for host in hosts:
            if 'webstats' in host and '.log' not in host:
                WEBSTATS_HOSTS.append(host.replace('\n', ''))

# Remove duplicates and sort
WEBSTATS_HOSTS = list(set(WEBSTATS_HOSTS))
WEBSTATS_HOSTS.sort()

# Lets fetch them all!
for host in WEBSTATS_HOSTS:
    print('Fetching {}'.format(host))
    try:
        html = urlopen('http://{}/{}'.format(host, AWSTATS_PATH))
        soup = BeautifulSoup(html, 'html.parser')

        years =  soup.select('select[name=year] option')
        years = [year['value'] for year in years]
        if len(years):

            WEBSTATS[host] = {}
            WEBSTATS[host]['totals'] = {}
            WEBSTATS[host]['totals']['unique'] = 0
            WEBSTATS[host]['totals']['visits'] = 0
            WEBSTATS[host]['totals']['views'] = 0
            WEBSTATS[host]['totals']['hits'] = 0

            for year in years:
                year_html = urlopen('http://{}/{}{}'.format(host, AWSTATS_PATH, year))
                year_soup = BeautifulSoup(year_html, 'html.parser')

                tbl = year_soup.select_one("table:nth-of-type(3)")

                if tbl:
                    vals = tbl.select_one("tr:nth-of-type(7)").findAll('td')

                    # 1 = Unique visitors, 2 = num visits, 3 = page views, 4 = hits
                    # We are good to try/catch here - if no digits in the number, we have no hits
                    try:
                        unique = ([i for i in vals[1].find('b').text.replace(',','').split() if i.isdigit()])[0]
                    except:
                        unique = 0

                    try:
                        visits = ([i for i in vals[2].find('b').text.replace(',','').split() if i.isdigit()])[0]
                    except:
                        visits = 0

                    try:
                        views = ([i for i in vals[3].find('b').text.replace(',','').split() if i.isdigit()])[0]
                    except:
                        views = 0

                    try:
                        hits = ([i for i in vals[4].find('b').text.replace(',','').split() if i.isdigit()])[0]
                    except:
                        hits = 0

                    WEBSTATS[host][year] = {}
                    WEBSTATS[host][year]['unique'] = int(unique) 
                    WEBSTATS[host][year]['visits'] = int(visits)
                    WEBSTATS[host][year]['views'] = int(views)
                    WEBSTATS[host][year]['hits'] = int(hits)

                    WEBSTATS[host]['totals']['unique'] += int(unique)
                    WEBSTATS[host]['totals']['visits'] += int(visits)
                    WEBSTATS[host]['totals']['views'] += int(views)
                    WEBSTATS[host]['totals']['hits'] += int(hits)

                    WEBSTATS[host][year]['countries'] = {}
                    countries = year_soup.select_one("table:nth-of-type(23)").select_one("table").findAll('tr')
                    countries = countries[1:-1]

                    total_pct = 100

                    for c in countries:
                        try:
                            name = c.select_one('td:nth-of-type(2)').text
                            pages = int(c.select_one('td:nth-of-type(4)').text.replace(',',''))
                            pct = 100*(pages/WEBSTATS[host][year]['views'])
                            pct = round(pct, 2)
                            total_pct -= pct
                            WEBSTATS[host][year]['countries'][name] = '{}%'.format(pct)
                        except:
                            pass

                    WEBSTATS[host][year]['countries']['other'] = '{}%'.format(round(total_pct, 2))


            WEBSTATS['_all']['totals']['unique'] += int(WEBSTATS[host]['totals']['unique'])
            WEBSTATS['_all']['totals']['visits'] += int(WEBSTATS[host]['totals']['visits'])
            WEBSTATS['_all']['totals']['views'] += int(WEBSTATS[host]['totals']['views'])
            WEBSTATS['_all']['totals']['hits'] += int(WEBSTATS[host]['totals']['hits'])

        else:

            print('AWStats configured incorrectly for {}'.format(host))
    except URLError:
        print('Failed to fetch {}'.format(host))
    except CertificateError:
        print('Invalid Certificate for {}'.format(host))

print()
print('Output (JSON Format)')
print()


print(json.dumps(WEBSTATS, sort_keys=True, indent=4, separators=(',', ': ')))