# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class DB:
    def __init__(self):
        pass

    def get_all_stores(self):
        raise NotImplementedError()

    def get_all_artists(self, preload = False):
        raise NotImplementedError()

    def get_all_albums(self, preload = False):
        raise NotImplementedError()

    def get_products_for_album(self, album, last_seen_at):
        raise NotImplementedError()

    def get_artist(self, name, preload = False):
        raise NotImplementedError()

    def get_album(self, artist, title):
        raise NotImplementedError()

    def get_store(self, store):
        raise NotImplementedError()

    def add_product(self, product):
        raise NotImplementedError()

    def add_cover(self, album, url, official = False):
        raise NotImplementedError()

    def add_genre(self, artist, genre):
        raise NotImplementedError()

    def artist_update_genre_timestamp(self, artist):
        raise NotImplementedError()
