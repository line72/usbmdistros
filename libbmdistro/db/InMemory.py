# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

from .DB import DB

class InMemory(DB):
    def __init__(self):
        self.artists = []
        self.albums = []
        self.stores = []
        self.products = []

    def get_all_stores(self):
        return self.stores

    def get_all_artists(self, preload = False):
        return self.artists

    def get_all_albums(self, preload = False):
        return self.albums

    def get_products_for_album(self, album, last_seen_at):
        return []

    def get_artist(self, name, preload = False):
        return self.artists.find(lambda x: x.name == name)

    def get_album(self, artist, title):
        return self.albums.find(lambda x: x.title == title and x.artist.name == artist)

    def get_store(self, store):
        return self.stores.find(lambda x: x.name == store)

    def add_product(self, product):
        self.products.append(product)

    def add_cover(self, album, url, official = False):
        pass

    def add_genre(self, artist, genre):
        pass

    def artist_update_genre_timestamp(self, artist):
        pass
