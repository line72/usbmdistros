# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import re
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
            p2 = filter(lambda x: x != None, p)
            entries.extend(list(p2))

        return entries

    def parseItem(self, db, entry):
        pId = entry['id']

        description = f"{entry['title']} - {entry['product_type']}"
        artist, title, extra, item_type = self.predictor.predict(description)

        if pId is None or artist is None or title is None:
            self.failure(description, pId, artist, title, item_type)
            return None
        
        item_type = self.parse_item_type(entry)
            
        price = int(float(entry['variants'][0]['price']) * 100)

        handle = entry['handle']
        u = urllib.parse.urlparse(self.feed)
        link = f'{u.scheme}://{u.netloc}/products/{handle}'

        images = [i['src'] for i in entry['images']]
        
        album = db.get_album(artist, title)
        for img in images:
            db.add_cover(album, img)

        return Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1)

    def parse_item_type(self, entry):
        item_type = entry['product_type']
        if item_type == 'Tape':
            item_type = 'Cassette'

        return item_type
