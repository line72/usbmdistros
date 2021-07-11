# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import re
import requests
import urllib
import itertools

from .Parser import Parser
from ..Product import Product

class MeteorGem(Parser):
    # This is a shopify store
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
        
            p = itertools.chain.from_iterable(map(lambda e: self.parseItem(db, e), products))
            entries.extend(list(p))

        return entries

    def parseItem(self, db, entry):
        products = []

        print(f'parsing {entry["title"]}')
        t = entry['title']
        if t.startswith('USED'):
            t = t.strip('USED - ')
            
        try:
            artist, title = t.split(sep = '-', maxsplit = 1)
        except ValueError:
            try:
                # some have a unicode '–'
                artist, title = t.split(sep = '–', maxsplit = 1)
            except ValueError:
                # Some don't have an album name
                print(f'Unable to parse {t}')
                return []

        artist = artist.strip()
        title = self.split_album_type(title)
        print(f' --> {artist} | {title}')
        item_type = self.get_product_type(entry['product_type'])
        images = [i['src'] for i in entry['images']]

        handle = entry['handle']
        u = urllib.parse.urlparse(self.feed)
        link = f'{u.scheme}://{u.netloc}/products/{handle}'

        album = db.get_album(artist, title)
        for img in images:
            db.add_cover(album, img)
        
        # An entry can have multiple variants
        for variant in entry['variants']:
            pId = variant['id']
            price = int(float(variant['price']) * 100)
            description = variant['title']

            products.append(Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1, description))

        return products

    def split_album_type(self, s):
        retests = [
            re.compile(r'^\s*(.*?)\s+2xLP$'),
            re.compile(r'^\s*(.*?)\s+3xLP$'),
            re.compile(r'^\s*(.*?)\s+7"$'),
            re.compile(r'^\s*(.*?)\s+7"\s+EP$'),
            re.compile(r'^\s*(.*?)\s+7"\s+Box\s+Set$'),
            re.compile(r'^\s*(.*?)\s+10"$'),
            re.compile(r'^\s*(.*?)\s+10"\s+EP$'),
            re.compile(r'^\s*(.*?)\s+12"$'),
            re.compile(r'^\s*(.*?)\s+12"\s+EP$'),
            re.compile(r'^\s*(.*?)\s+12"\s+\([a-zA-Z0-9\s]+\)$'),
            re.compile(r'^\s*(.*?)\s+LP\s+\(Music\s+On\s+Vinyl\)$'),
            re.compile(r'^\s*(.*?)\s+LP\s+\(Listenable\s+Records\)$'),
            re.compile(r'^\s*(.*?)\s+LP\s+\+\s+DVD$'),
            re.compile(r'^\s*(.*?)\s+LP\s+Box\s+Set$'),
            re.compile(r'^\s*(.*?)\s+LP$'),
            re.compile(r'^\s*(.*?)\s+EP$'),
            re.compile(r'^\s*(.*?)\s+Cassette$'),
            re.compile(r'^\s*(.*?)\s+Cassette\sTape$'),
            re.compile(r'^\s*(.*?)\s+Tape$'),
            re.compile(r'^\s*(.*?)\s+tape$'),
            re.compile(r'^\s*(.*?)\s+CD$'),
            re.compile(r'^\s*(.*?)\s+Season\s+Of\s+Mist$'),
        ]

        for r in retests:
            if (match := re.match(r, s)) != None:
                return match.group(1).strip()

        # No matches, probably doesn't have extra junk in it
        print(f'!!!! Unable to match |{s}| !!!!')
        return s.strip()

    def get_product_type(self, t):
        if t in ('12"', '10"', '7"'):
            return 'Vinyl'
        elif t in ('Cassette', 'Cassette Tape'):
            return 'Cassette'
        elif t == 'CD':
            return 'CD'

        raise Exception(f'Unknown product type {t}')
