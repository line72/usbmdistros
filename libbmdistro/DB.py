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
            self.items[artist][album][item_type] = Album(artist, album, item_type)

        return self.items[artist][album][item_type]
