# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import requests
from bs4 import BeautifulSoup
import re
import urllib
import sys

from .Parser import Parser
from ..Product import Product

class DebemurMorti(Parser):
    def parse(self, db):
        r = requests.get(self.feed)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, 'html.parser')

        product_list = soup.find('ul', 'product-list')
        if product_list is None:
            raise Exception('DebemurMorti::Unable to find product-list')

        items = product_list.find_all('li')

        entries = map(lambda e: self.parseItem(db, e), items)
        entries = filter(lambda x: x != None, entries)

        return list(entries)

    def parseItem(self, db, entry):
        # Here is the format:
        # <li class="l">
        # <a class="pImg" href="/item/67780">
        #   <img alt="The Sublime" src="https://proassets.monopile.cloud/67780/39504a297b2acb38d86de52c1253cbb1_m.jpg" width="160"/>
        # </a>
        # <div class="p">
        #   <strong>Yeruselem</strong>
        #   <a href="/item/67780">The Sublime</a>
        #   <a class="cat" href="/category/261">(12")</a>
        # </div>
        # <div class="price">
        #   <strong>$22.99</strong>
        # </div>
        # </li>

        artist = entry.find('div', 'p').strong.text
        album = entry.find('div', 'p').find('a').text
        category = entry.find('a', 'cat')['href']
        
        # create a custom description from several fields
        description = f"{artist} | {album} | {category}"

        artist, title, extra, item_type = self.predictor.predict(description)

        link = entry.find('div', 'p').find('a')['href']
        # use the url as the id
        pId = link
        
        if pId is None or artist is None or title is None or item_type not in ('Vinyl', 'CD', 'Cassette'):
            self.failure(description, pId, artist, title, item_type)
            return None
        
        # sometimes the price is in a <strong></strong>, sometimes it isn't
        if entry.find('div', 'price').strong:
            price = int(float(self.parse_price(entry.find('div', 'price').strong.text)) * 100)
        else:
            price = int(float(self.parse_price(entry.find('div', 'price').text)) * 100)


        u = urllib.parse.urlparse(self.feed)
        url = f'{u.scheme}://{u.netloc}{link}'

        img_url = entry.find('a', 'pImg').find('img')['src']
        
        in_stock = Product.STOCK_UNKNOWN
        quantity = -1

        
        album = db.get_album(artist, album)
        db.add_cover(album, img_url)
        
        return Product(None, pId, album, self.store, url, item_type, price, in_stock, quantity, extra)

    def parse_price(self, p):
        r = re.compile(r'^\s*\$(\d+\.\d+)\s*.*$')
        if (match := re.match(r, p)) != None:
            return match.group(1)

        raise Exception(f'Error parsing price {p} {[ord(x) for x in p]}')
