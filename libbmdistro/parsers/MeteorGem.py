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

        # create a custom description from several fields
        description = entry["title"]

        artist, title, extra, item_type = self.predictor.predict(description)
            
        if artist is None or title is None or item_type not in ('Vinyl', 'CD', 'Cassette'):
            self.failure(description, '', artist, title, item_type)
            return []
        
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

            if pId is None:
                continue
            
            products.append(Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1, description))

        return products
