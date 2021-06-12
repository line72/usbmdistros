# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Product:
    STOCK_OUT_OF_STOCK = 0
    STOCK_IN_STOCK = 1
    STOCK_UNKNOWN = -1
    
    def __init__(self, pId, sku, album, store, link, item_type, price, in_stock,
                 quantity, description = '', last_seen_at = None, updated_at = None):
        self.pId = pId
        self.sku = sku
        self.album = album
        self.store = store
        self.link = link
        self.item_type = item_type
        self.price = price
        self.in_stock = in_stock
        self.quantity = quantity
        self.description = description
        self.last_seen_at = last_seen_at
        self.updated_at = updated_at
        
    def __str__(self):
        return f"<Product::{self.album.artist}-{self.album.title}::{self.price}({self.quantity})::{self.store.name}>"
