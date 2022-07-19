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
            r = requests.get(self.feed, params = {'page': page})
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

        item_type = self.parse_category(entry['categories'])
        # filter out item types we don't want
        if item_type == None:
            return None
        
        at = self.split_artist_title(entry['name'], item_type)
        if not at:
            return None
        
        artist, title = at
        price = int(entry['prices']['price'])
        link = entry['permalink']

        images = [i['src'] for i in entry['images']]

        album = db.get_album(artist, title)
        for img in images:
            db.add_cover(album, img)
        
        return Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1)
        

    def split_artist_title(self, t, item_type):
        r = re.compile(r'^\s*(.*?)\s+&#8211;\s+(.*?)\s*$')

        known_types = [
            re.compile(r'^(.*?)\s+CD\s*$'),
            re.compile(r'^(.*?)\s+CD\s+\[.*\]\s*$'),
            re.compile(r'^(.*?)\s+CASSETTE\s*$'),
            re.compile(r'^(.*?)\s+CASSETTE\s+\[.*\]\s*$'),
            re.compile(r'^(.*?)\s+d+"\s+EP\s*$'),
            re.compile(r'^(.*?)\s+\d+″\s+EP\s*$'),
            re.compile(r'^(.*?)\s+\d+″\s+GATEFOLD\s+DOUBLE\s+LP\s+[A-Z]+\s*$'),
            re.compile(r'^(.*?)\s+\d+"\s+LP\s+[A-Z]+\s*$'),
            re.compile(r'^(.*?)\s+\d+″\s+LP\s*[A-Z]+\s*$'),
            re.compile(r'^(.*?)\s+\d+″\s+[A-Z\s]+\s+LP\s*$'),
            re.compile(r'^(.*?)\s+\d+"\s+LP\s*$'),
            re.compile(r'^(.*?)\s+\d+″\s+LP\s*$'),
            re.compile(r'^(.*?)\s+CD\s+/\s+DVD\s*$'),
            re.compile(r'^(.*?)\s+CD\s+IN\s+DVD\s+CASE\s*$'),
            re.compile(r'^(.*?)\s+CD\s+IN\s+CLOTH\s+BAG\s*$'),
            re.compile(r'^(.*?)\s+CASSETTE\s+IN\s+BAG\s*$'),
            re.compile(r'^(.*?)\s+2014\s*$'),
        ]
        
        print('artist/title', t)
        if (match := re.match(r, t)) != None:
            artist = match.group(1).strip()
            artist = html.unescape(artist)
            artist = artist.title()

            # deal with the rest...
            #  convert any html codes to regular unicode
            rest = html.unescape(match.group(2))

            for kt in known_types:
                if (m := re.match(kt, rest)) != None:
                    album = m.group(1).strip()

                    return (artist, album)

            raise Exception(f'Unable to parse rest: {rest}')

        print(f'Unable to parse: {t}')
        return None

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
