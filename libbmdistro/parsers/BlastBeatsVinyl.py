# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import re
import requests
import urllib
import sys

from .Parser import Parser
from ..Product import Product

class BlastBeatsVinyl(Parser):
    def __init__(self, store, feed):
        super().__init__(store, feed)

        self.unknown_types = set()
        
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
            p = filter(lambda x: x != None, p)
            entries.extend(list(p))

        if len(self.unknown_types) > 0:
            print('=====BlastBeatVinyl Unknown Types========', file = sys.stderr)
            for i in self.unknown_types:
                print(f'BlastBeatVinyl Unknown Type: {i}', file = sys.stderr)
            print('=========================================', file = sys.stderr)
            
        return entries

    def parseItem(self, db, entry):
        print('BlastBeatVinyl: parsing', entry['title'])

        try:
            pId = entry['id']
            title = entry['title'].replace('–', '-').replace(chr(8206), '').replace(chr(8220), '"').replace(chr(8221), '"')

            artist, title = title.split(sep = ' - ', maxsplit = 1)
            artist = self.clean_artist(artist)
            title, desc = self.split_album_type(title)
            item_type = self.parse_item_type(entry)
            
            price = int(float(entry['variants'][0]['price']) * 100)

            handle = entry['handle']
            u = urllib.parse.urlparse(self.feed)
            link = f'{u.scheme}://{u.netloc}/products/{handle}'

            images = [i['src'] for i in entry['images']]

            album = db.get_album(artist, title)
            for img in images:
                db.add_cover(album, img)

            # print(f'  Artist: {artist}')
            # print(f'  Album:  {title}')
            # print(f'  Desc:   {desc}')
            # print(f'  Type:   {item_type}')
            # print(f'  Price:  {price}')

            return Product(None, pId, album, self.store, link, item_type, price, Product.STOCK_UNKNOWN, -1, desc)
        except ValueError as e:
            print('BlastBeatVinyl: Error parsing ', entry['title'], file = sys.stderr)
            return None

    def clean_artist(self, a):
        # try to remove [XXX] at the beginning
        r = re.compile(r'^\[.+\]\s+(.*?)$')
        if (match := re.match(r, a)) != None:
            return match.group(1).strip()

        return a.strip()
        
    def split_album_type(self, s):
        split = s.split(sep = ' - ')
        if len(split) == 1:
            split = s.split(sep = '- ')
        
        title = split[0]
        desc = ' - '.join(split[1:])

        # sometimes, we have a *NUMBERED* in the title too
        # knock that over to the desc
        if '*NUMBERED*' in title:
            i = title.index('*NUMBERED*')

            # set the desc before title, since
            #  we modify title in place
            desc = f'{title[i:]} - {desc}'
            title = title[:i]
        
        return (title.strip(), desc.strip())

    def parse_item_type(self, entry):
        item_type = entry['product_type']

        vinyl_types = (
            '12"',
            '2 x 12"',
            '7"',
            '*Boxset* 4LP Red Vinyl Ltd 200',
            'Boxset',
            'Picturedisc',
            '10"',
            '12" + 7"',
            '3 x 12"'
        )
        
        if item_type in vinyl_types:
            return 'Vinyl'

        #raise Exception(f'Unknown Item Type: {item_type}')
        self.unknown_types.add(item_type)

        return 'Unknown'

