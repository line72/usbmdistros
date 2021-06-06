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
    def __init__(self, store, feed):
        super().__init__(store, feed)

        # known suffixes:
        # - 12" LP
        # - 7" EP
        # - 7’’ EP
        # - 2xLP
        # - 2x10" MLP
        # - CD
        # - Tape
        self.retests = [
            ('12', 'Vinyl', re.compile(r'^\s*(.*?)\s+12"$')),
            ('12lp', 'Vinyl', re.compile(r'^\s*(.*?)\s+12"\s+LP$')),
            ('12lp with extra', 'Vinyl', re.compile(r'^\s*(.*?)\s+12"\s+LP\s+\(.*?\)$')),
            ('12sslp', 'Vinyl', re.compile(r'^\s*(.*?)\s+SS12"\s+LP$')),
            ('lp', 'Vinyl', re.compile(r'^\s*(.*?)\s+LP$')),
            ('12mlp', 'Vinyl', re.compile(r'^\s*(.*?)\s+12"\s+MLP$')),
            ('10mlp', 'Vinyl', re.compile(r'^\s*(.*?)\s+10"\s+MLP$')),
            ('10mlp', 'Vinyl', re.compile(r'^\s*(.*?)\s+10"$')),
            ('10mlp', 'Vinyl', re.compile(r'^\s*(.*?)\s+10″$')),
            ('7ep', 'Vinyl', re.compile(r'^\s*(.*?)\s+7"\s+EP$')),
            ('7ep', 'Vinyl', re.compile(r'^\s*(.*?)\s+7’’\s+EP$')),
            ('7ep', 'Vinyl', re.compile(r'^\s*(.*?)\s+7″\s+EP$')),
            ('7ep', 'Vinyl', re.compile(r'^\s*(.*?)\s+7”\s+EP$')),
            ('2xlp', 'Vinyl', re.compile(r'^\s*(.*?)\s+\dxLP$')),
            ('2xmlp', 'Vinyl', re.compile(r'^\s*(.*?)\s+2x10"\s+MLP$')),
            ('2xmlp', 'Vinyl', re.compile(r'^\s*(.*?)\s+2x10’’\s+MLP$')),
            ('cd', 'CD', re.compile(r'^\s*(.*?)\s+CD$')),
            ('mcd', 'CD', re.compile(r'^\s*(.*?)\s+MCD$')),
            ('cd', 'CD', re.compile(r'^\s*(.*?)\s+CD\s\+.*$')),
            ('2cd', 'CD', re.compile(r'^\s*(.*?)\s+2CD$')),
            ('3xcd', 'CD', re.compile(r'^\s*(.*?)\s+3xCD$')),
            ('tape', 'Tape', re.compile(r'^\s*(.*?)\s+Tape$')),
        ]
        
    def parse(self, db):
        feed = feedparser.parse(self.feed)

        entries = map(lambda e: self.parseItem(db, e), feed.entries)
        return list(filter(lambda x: x != None, entries))

    def parseItem(self, db, entry):
        try:
            artist, rest = entry['g_title'].split(sep = '-', maxsplit = 1)
        except ValueError:
            try:
                # some have a unicode '–'
                artist, rest = entry['g_title'].split(sep = '–', maxsplit = 1)
            except ValueError:
                # Some don't have an album name
                print(f'Unable to parse {entry["g_title"]}')
                return None

        artist = artist.strip(string.whitespace + chr(8206) + chr(160))
        
        album, item_type = self.split_album_type(rest)
        price = self.get_price(entry['g_price'])
        availability = entry['g_availability']
        #img_link = entry['g_image_link']
        
        in_stock = Product.STOCK_IN_STOCK if availability == 'in stock' else Product.STOCK_OUT_OF_STOCK
        
        album = db.get_album(artist, album, item_type)

        return Product(album, self.store, entry['g_link'], price, in_stock, -1)

    def split_album_type(self, s):
        for (i, t, r) in self.retests:
            if (match := re.match(r, s)) != None:
                return (match.group(1).strip(), t)
            
        raise Exception(f'Error, Unknown type {s}')

    def get_price(self, p):
        r = re.compile(r'^\s*(\d+\.\d+)\s+.*$')
        if (match := re.match(r, p)) != None:
            return match.group(1)

        raise Exception(f'Error parsing price {p} {[ord(x) for x in p]}')
