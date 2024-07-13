# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import html
import re
import requests
import urllib

from .Parser import Parser
from ..Product import Product

class MetalToTheCore1986(Parser):
    def parse(self, db):
        # this only returns 20 products at a time.
        entries = []

        page = 1
        while True:
            # Site blocks python-requests user-agent
            #  pretent to be curl
            headers = {'user-agent': 'curl/8.0.1'}
            r = requests.get(self.feed, params = {'page': page}, headers = headers)
            r.raise_for_status()
            page += 1

            products = r.json()
            if len(products) == 0:
                break

            p = map(lambda e: self.parseItem(db, e), products)
            entries.extend(list(filter(lambda x: x != None, p)))

        return entries

    def parseItem(self, db, entry):
        pId = entry['sku']

        description = entry['name']
        artist, title, extra, item_type = self.predictor.predict(description)
        
        if pId is None or artist is None or title is None:
            self.failure(description, pId, artist, title, item_type)
            return None

        item_type = self.parse_category(entry['categories'])
        # filter out item types we don't want
        if item_type == None:
            return None
        
        price = int(entry['prices']['price'])
        link = entry['permalink']

        images = [i['src'] for i in entry['images']]

        album = db.get_album(artist, title)
        for img in images:
            db.add_cover(album, img)
        
        return Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1, extra)

    def parse_category(self, c):
        for cat in c:
            if cat['name'] == 'Cassettes':
                return 'Cassette'
            elif cat['name'] == 'Vinyl':
                return 'Vinyl'
            elif cat['name'] == 'CDs':
                return 'CD'
            elif cat['name'] == 'Clothing':
                return None
        return None
