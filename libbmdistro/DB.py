# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

from libbmdistro.Album import Album

class DB:
    def __init__(self):
        self.items = {}

    def get(self, artist, album, item_type):
        if not artist in self.items:
            self.items[artist] = {}

        if not album in self.items[artist]:
            self.items[artist][album] = {}

        if not item_type in self.items[artist][album]:
            self.items[artist][album][item_type] = {
                'album': Album(artist, album, item_type),
                'products': []
            }

        return self.items[artist][album][item_type]

    def get_album(self, artist, album, item_type):
        t = self.get(artist, album, item_type)
        return t['album']

    def add_product(self, product):
        t = self.get(product.album.artist, product.album.title, product.album.item_type)
        t['products'].append(product)

        
