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
        (title, description) = self.split_album(title)
        item_type = self.parse_item_type(entry['marketplace_category'])
        price = int(float(entry['price']) * 100)

        link = entry['url']

        if item_type == None:
            return None

        
        album = db.get_album(artist, title)
        for img in entry['photos']:
            db.add_cover(album, f"https:{img['photo']['original']}")

        return Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1, description)

    def split_album(self, s):
        retests = [
            re.compile(r'^\s*(.*?)(?:\s+\(Cal\-\d+\))(?:\s+\((.*?)\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Cal\-\d+\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Caligari\s+Records\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Vinyl\s+Cal\-\d+\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Vinyl\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Cd\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(CD\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Dvd\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(DVD\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(EP\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Ep\s+Compilation\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(EP\s+Compilation\))\s*$'),
            re.compile(r'^\s*(.*?)(?:\s+\(Vinyl\s+\+\s+Cassette\))\s*$'),
        ]

        for r in retests:
            if (match := re.match(r, s)) != None:
                album = match.group(1).strip()
                if len(match.groups()) > 1:
                    description = match.group(2)
                    if not description:
                        description = ''
                else:
                    description = ''
            
                return (album.title(), description)

        return (s.strip().title(), '')
    
    def parse_item_type(self, t):
        if t == 'music-cassette-tapes':
            return 'Tape'
        elif t == 'music-cds':
            return 'CD'
        elif t == 'music-vinyl':
            return 'Vinyl'
        elif t == 'home-art-prints-posters':
            return None
        elif t == 'music-band-merch-posters':
            return None

        raise Exception(f'Unknown item type {t}')
