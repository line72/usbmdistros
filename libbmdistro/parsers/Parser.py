# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Parser:
    def __init__(self, store, feed, predictor):
        self.store = store
        self.feed = feed
        self.predictor = predictor
        self.failures = []

    def parse(self, db):
        return []

    def failure(self, description, sku, artist, title, format_):
        self.failures.append((description, sku, artist, title, format_))
