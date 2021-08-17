# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import re
import requests
import urllib

from .Parser import Parser
from ..Product import Product

class CWProductions(Parser):
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

            products = r.json()['products']
            if len(products) == 0:
                # all done
                break
        
            p = map(lambda e: self.parseItem(db, e), products)
            entries.extend(list(filter(lambda x: x != None, p)))

        return entries

    def parseItem(self, db, entry):
        pId = entry['id']

        # Format is:
        # Artist "Album" Format
        # remove any function whitespace, and funky quotes
        e = entry['title'].replace(chr(8206), ' ').replace(chr(8220), '"').replace(chr(8221), '"')
        r = re.compile(r'^\s*(.*?)\s+"(.*?)"\s+(.*?)\s*$')
        if (match := re.match(r, e)) != None:
            artist = match.group(1).strip()
            title = match.group(2).strip()
            item_type, description = self.parse_item_type(match.group(3).strip())
        else:
            print((f'Unable to parse |{e}| {list(ord(x) for x in e)}'))
            return None
        
        price = int(float(entry['variants'][0]['price']) * 100)

        handle = entry['handle']
        u = urllib.parse.urlparse(self.feed)
        link = f'{u.scheme}://{u.netloc}/products/{handle}'

        images = [i['src'] for i in entry['images']]
        
        album = db.get_album(artist, title)
        for img in images:
            db.add_cover(album, img)
        
        return Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1, description)

    def parse_item_type(self, s):
        if s in ('tape', 'split tape', 'double tape'):
            return ('Cassette', '')
        elif s in ('CD', 'split CD', '2CD', 'DCD', 'CDr'):
            return ('CD', '')
        elif s in ('LP', 'split LP', 'DLP', '2LP', '10"', 'LP (2nd press)', '7"', 'LP + 7"', 'pic LP',\
                   '12" EP', 'split 7"', 'DLP + DVD', 'Rehearsal 10"'):
            return ('Vinyl', '')
        elif (match := re.match(re.compile(r'^LP\s+\((.*?)\)\s*$'), s)) != None:
            return ('Vinyl', match.group(1).strip())
        elif (match := re.match(re.compile(r'^LP\s+\+\s+\d+"\s+\((.*?)\)\s*$'), s)) != None:
            return ('Vinyl', match.group(1).strip())
        else:
            raise Exception(f'Unknown item type {s}')
