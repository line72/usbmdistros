# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import feedparser
import re
import string

from .Parser import Parser
from ..Product import Product

class ArcaneAltar(Parser):
    def parse(self, db):
        feed = feedparser.parse(self.feed)

        entries = map(lambda e: self.parseItem(db, e), feed.entries)
        return list(filter(lambda x: x != None, entries))

    def parseItem(self, db, entry):
        pId = entry['g_id']
        description = entry['g_title']

        artist, title, extra, item_type = self.predictor.predict(description)

        if pId is None or artist is None or title is None or item_type not in ('Vinyl', 'CD', 'Cassette'):
            self.failure(description, pId, artist, title, item_type)
            return None
        
        price = int(float(self.get_price(entry['g_price'])) * 100)
        availability = entry['g_availability']
        img_link = entry['g_image_link']
        
        in_stock = Product.STOCK_IN_STOCK if availability == 'in stock' else Product.STOCK_OUT_OF_STOCK
        
        album = db.get_album(artist, title)
        db.add_cover(album, img_link)

        return Product(None, pId, album, self.store, entry['g_link'], item_type, price, in_stock, -1, extra)

    def get_price(self, p):
        r = re.compile(r'^\s*(\d+\.\d+)\s+.*$')
        if (match := re.match(r, p)) != None:
            return match.group(1)

        raise Exception(f'Error parsing price {p} {[ord(x) for x in p]}')
