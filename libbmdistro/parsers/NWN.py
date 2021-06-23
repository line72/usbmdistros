# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import re
import requests
import socket
import time
import urllib
from bs4 import BeautifulSoup

from .Parser import Parser
from ..Product import Product

class NWN(Parser):
    def parse(self, db):
        entries = []

        categories = (
            (75, 'Vinyl'),
            (76, 'Vinyl'),
            (93, 'CD'),
            (73, 'Cassette')
        )

        for (category, t) in categories:
            entries.extend(self.parse_category(db, category, t))

        return entries

    def parse_category(self, db, category, t):
        entries = []
        
        page = 1
        while True:
            try:
                r = requests.get(self.feed, params = {'page': page,
                                                      'route': 'product/category',
                                                      'path': category,
                                                      'sort': 'pd.name',
                                                      'order': 'ASC'})
                r.raise_for_status()
                page += 1

                soup = BeautifulSoup(r.text, 'html.parser')
                items = soup.find_all('div', 'product-thumb')

                if len(items) == 0:
                    return entries

                ents = map(lambda e: self.parseItem(db, e, t), items)
                ents = filter(lambda x: x != None, ents)

                entries.extend(list(ents))
            except (socket.gaierror, requests.exceptions.ConnectionError) as e:
                print(f'Socket Error: {e}. Backing off...')
                time.sleep(1)

        return entries

    def parseItem(self, db, entry, t):
        # Here is the format:
        # <div class="product-thumb">
        #  <div class="image">
        #   <a href="http://shop.nwnprod.com/index.php?route=product/product&amp;path=75&amp;product_id=14463&amp;sort=pd.name&amp;order=ASC">
        #    <img alt='Abruptum "Orchestra of Dark" LP' class="img-responsive" src="https://shop.nwnprod.com/image/cache/catalog/March%2026/a2284688190_10-228x228.jpg" title='Abruptum "Orchestra of Dark" LP'/>
        #   </a>
        #  </div>
        #  <div>
        #   <div class="caption">
        #    <h4>
        #     <a href="http://shop.nwnprod.com/index.php?route=product/product&amp;path=75&amp;product_id=14463&amp;sort=pd.name&amp;order=ASC">
        #      Abruptum "Orchestra of Dark" LP
        #     </a>
        #    </h4>
        #    <p>
        #     Orchestra of Dark by Abruptum..
        #    </p>
        #    <p class="price">
        #     $25.00
        #    </p>
        #   </div>
        #   <div class="button-group">
        #    <button onclick="cart.add('14463', '1');" type="button">
        #     <i class="fa fa-shopping-cart">
        #     </i>
        #     <span class="hidden-xs hidden-sm hidden-md">
        #      Add to Cart
        #     </span>
        #    </button>
        #    <button data-toggle="tooltip" onclick="wishlist.add('14463');" title="Add to Wish List" type="button">
        #     <i class="fa fa-heart">
        #     </i>
        #    </button>
        #    <button data-toggle="tooltip" onclick="compare.add('14463');" title="Compare this Product" type="button">
        #     <i class="fa fa-exchange">
        #     </i>
        #    </button>
        #   </div>
        #  </div>
        # </div>

        try:
            p_id = self.parse_id(entry.find('div', 'button-group').button['onclick'])
            url = entry.find('div', 'image').a['href'].strip()
            artist_title = entry.find('div', 'caption').h4.a.text.strip()
            artist, title = self.parse_aritst_album(artist_title)
            price = int(float(self.parse_price(entry.find('p', 'price').text.strip())) * 100)

            img_url = entry.find('div', 'image').a.img['src'].strip()

            album = db.get_album(artist, title)
            db.add_cover(album, img_url)
            
            return Product(None, p_id, album, self.store, url, t, price, Product.STOCK_UNKNOWN, -1, '')
        except Exception as e:
            print(e)
            return None

    def parse_price(self, p):
        r = re.compile(r'^\s*\$(\d+\.\d+)\s*.*$')
        if (match := re.match(r, p)) != None:
            return match.group(1)

        raise Exception(f'Error parsing price {p} {[ord(x) for x in p]}')

    def parse_aritst_album(self, p):
        r = re.compile(r'^\s*(.*?)\s+[\"\“](.*?)[\"\”]\s+.*?$')
        if (match := re.match(r, p)) != None:
            return (match.group(1), match.group(2))

        raise Exception(f'Error parsing artist/album {p}')

    def parse_id(self, p):
        r = re.compile(r"^\s*cart\.add\('(\d+)',\s+'\d+'\);\s*$")
        if (match := re.match(r, p)) != None:
            return match.group(1)

        raise Exception(f'Error parsing id {p}')
        
