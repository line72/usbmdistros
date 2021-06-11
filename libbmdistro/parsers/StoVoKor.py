# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import requests
import urllib

from .Parser import Parser
from ..Product import Product

class StoVoKor(Parser):
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
            entries.extend(list(p))

        return entries

    def parseItem(self, db, entry):
        artist, album = entry['title'].split(sep = '-', maxsplit = 1)
        artist = artist.strip()
        album = album.strip()
        item_type = entry['product_type']
        price = entry['variants'][0]['price']

        handle = entry['handle']
        u = urllib.parse.urlparse(self.feed)
        link = f'{u.scheme}://{u.netloc}/products/{handle}'

        album = db.get_album(artist, album, item_type)
        
        return Product(album, self.store, link, price, Product.STOCK_UNKNOWN, -1)
