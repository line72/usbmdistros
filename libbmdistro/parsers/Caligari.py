# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import re
import requests
import urllib

from .Parser import Parser
from ..Product import Product

class Caligari(Parser):
    def parse(self, db):
        # this only returns 30 products at a time.
        # Unfortunately, there is no information about
        #  the number of items or pages, so we'll
        #  just have to paginate until there are no items
        entries = []
        
        page = 1
        while True:
            r = requests.get(self.feed, params = {'page': page})
            r.raise_for_status()
            page += 1

            products = r.json()
            if len(products) == 0:
                # all done
                break
        
            p = map(lambda e: self.parseItem(db, e), products)
            p2 = filter(lambda e: e != None, p)
            entries.extend(list(p2))

        return entries

    def parseItem(self, db, entry):
        pId = entry['id']
        try:
            artist, title = entry['name'].split(sep = '-', maxsplit = 1)
        except ValueError:
            try:
                # some have a unicode –
                artist, title = entry['name'].split(sep = '–', maxsplit = 1)
            except ValueError:
                # Some don't have an album name
                print(f'Unable to parse {entry["name"]}')
                return None
                
        artist = artist.strip().title()
        title = self.split_album(title).title()
        item_type = self.parse_item_type(entry['marketplace_category'])
        price = int(float(entry['price']) * 100)

        link = entry['url']

        if item_type == None:
            return None

        album = db.get_album(artist, title)

        return Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1)

    def split_album(self, s):
        r = re.compile(r'^\s*(.*?)(?:\s+\(Cal\-\d+\))?\s*$')

        if (match := re.match(r, s)) != None:
            return match.group(1).strip()

        return s.strip()
    
    def parse_item_type(self, t):
        if t == 'music-cassette-tapes':
            return 'Tape'
        elif t == 'music-cds':
            return 'CD'
        elif t == 'music-vinyl':
            return 'Vinyl'
        elif t == 'home-art-prints-posters':
            return None

        raise Exception(f'Unknown item type {t}')
