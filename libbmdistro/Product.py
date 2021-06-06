# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Product:
    STOCK_OUT_OF_STOCK = 0
    STOCK_IN_STOCK = 1
    STOCK_UNKNOWN = -1
    
    def __init__(self, album, store, link, price, in_stock, quantity):
        self.album = album
        self.store = store
        self.link = link
        self.price = price
        self.in_stock = in_stock
        self.quantity = quantity
        
    def __str__(self):
        return f"<Product::{self.album.artist}-{self.album.title}::{self.price}({self.quantity})>"
