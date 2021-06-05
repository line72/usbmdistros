# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Product:
    def __init__(self, album, store, link, price, quantity):
        self.album = album
        self.store = store
        self.link = link
        self.price = price
        self.quantity = quantity
        
    def __str__(self):
        return f"<Product::{self.album.artist}-{self.album.title}::{self.price}({self.quantity})>"
