# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import feedparser
from bs4 import BeautifulSoup

from .Parser import Parser
from ..Product import Product

class StoVoKor(Parser):
    def parse(self, db):
        feed = feedparser.parse(self.feed)

        entries = map(lambda e: self.parseItem(db, e), feed['entries'])
        return list(entries)

    def parseItem(self, db, entry):
        #print('parseItem', entry)
        artist, album = entry['title'].split(sep = '-', maxsplit = 1)
        artist = artist.strip()
        album = album.strip()
        item_type = entry['s_type']
        price = entry['s_variant']

        # pull the price out of the summary
        #print(entry['summary'])
        # soup = BeautifulSoup(entry['summary'], 'html.parser')
        # print(soup.prettify())

        album = db.get(artist, album, item_type)
        
        return Product(album, self.store, entry['link'], price, -1)
