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
        album, description = self.parse_album(entry.find('div', 'p').find('a').text)
        category = entry.find('a', 'cat')['href']

        # sometimes the price is in a <strong></strong>, sometimes it isn't
        if entry.find('div', 'price').strong:
            price = int(float(self.parse_price(entry.find('div', 'price').strong.text)) * 100)
        else:
            price = int(float(self.parse_price(entry.find('div', 'price').text)) * 100)

        link = entry.find('div', 'p').find('a')['href']

        u = urllib.parse.urlparse(self.feed)
        url = f'{u.scheme}://{u.netloc}{link}'

        img_url = entry.find('a', 'pImg').find('img')['src']
        
        in_stock = Product.STOCK_UNKNOWN
        quantity = -1

        try:
            item_type = self.get_item_type(category)
        except Exception as e:
            print(f'DebemurMorti: Error parsing {artist} {album} - {url}', file = sys.stderr)
            raise e;

        # use the url as the id
        pId = link
        
        album = db.get_album(artist, album)
        db.add_cover(album, img_url)
        
        return Product(None, pId, album, self.store, url, item_type, price, in_stock, quantity, description)

    def parse_price(self, p):
        r = re.compile(r'^\s*\$(\d+\.\d+)\s*.*$')
        if (match := re.match(r, p)) != None:
            return match.group(1)

        raise Exception(f'Error parsing price {p} {[ord(x) for x in p]}')

    def parse_album(self, a):
        # Some albums have a description in parens at the end
        #  indicating a variant, try to pull that out.
        r = re.compile(r'^\s*(.*?)(?:\s+\((.+?)\)\s*)?$')
        if (match := re.match(r, a)) != None:
            album, description = (match.group(1), match.group(2))
            if not description:
                description = ''

            return (album, description.strip())

        raise Exception(f'Error parsing album {a} {[ord(x) for x in a]}')
    
    def get_item_type(self, category):
        if category == '/category/26':
            return 'CD'
        elif category == '/category/267':
            return 'CD'
        elif category == '/category/250':
            return 'Vinyl'
        elif category == '/category/251':
            return 'Vinyl'
        elif category == '/category/261':
            return 'Vinyl'
        elif category == '/category/263':
            return 'Vinyl'
        elif category == '/category/353':
            return 'Vinyl'
        elif category == '/category/303':
            return 'Cassette'
        else:
            raise Exception(f'Unknown category type {category}')
