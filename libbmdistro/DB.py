# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import datetime
import sqlite3

from .Album import Album
from .Product import Product
from .Store import Store

class DB:
    VERSION = 1
    
    def __init__(self):
        self.conn = sqlite3.connect('bmdistro.db', detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row # allow using dictionary for access
        self.cursor = self.conn.cursor()

        self.create_verify_database()

    def get_all_stores(self):
        # a cursors iterator is shared
        #  so create a new one
        cur = self.conn.cursor()
        resp = cur.execute('''SELECT * FROM stores ORDER BY name''')
        return map(lambda i: Store(i['id'], i['name'], i['url']), resp)
        
    def get_all_albums(self):
        # a cursors iterator is shared
        #  so create a new one
        cur = self.conn.cursor()
        resp = cur.execute('''SELECT * FROM albums ORDER BY id''')
        return map(lambda i: Album(i['id'], i['artist'], i['title']), resp)

    def get_products_for_album(self, album):
        # a cursors iterator is shared
        #  so create a new one
        cur = self.conn.cursor()
        resp = cur.execute(
            '''
            SELECT 
              p.id AS id,
              p.sku AS sku,
              p.item_type AS item_type,
              p.link AS link,
              p.price AS price,
              p.in_stock AS in_stock,
              p.quantity AS quantity,
              p.description AS description,
              p.last_seen_at AS "last_seen_at [timestamp]",
              p.updated_at AS "updated_at [timestamp]",
              s.id as store_id,
              s.name as store_name,
              s.url as store_url
            FROM 
              products AS p,
              stores AS s
            WHERE
              p.album_id = ? AND
              p.store_id = s.id
            ORDER BY
              p.id
            ''', (album.aId,))
        
        return map(lambda i: Product(i['id'], i['sku'], album,
                                     Store(i['store_id'], i['store_name'], i['store_url']),
                                     i['link'], i['item_type'], i['price'], i['in_stock'],
                                     i['quantity'], i['description'], i['last_seen_at'],
                                     i['updated_at']), resp)
        
        
    def get_album(self, artist, title):
        def fetchone():
            resp = self.cursor.execute(
                '''
                SELECT * FROM albums
                WHERE
                  LOWER(artist) = LOWER(?) AND
                  LOWER(title) = LOWER(?)
                ''', (artist, title))

            return resp.fetchone()
        
        e = fetchone()
        if not e:
            self.cursor.execute(
                '''
                INSERT INTO albums (artist, title)
                VALUES (?, ?)
                ''', (artist, title))
            self.conn.commit()
            e = fetchone()

        return Album(e['id'], e['artist'], e['title'])

    def get_store(self, store):
        def fetchone():
            resp = self.cursor.execute('''SELECT * from stores WHERE name = ? LIMIT 1''', (store.name,))
            return resp.fetchone()

        e = fetchone()
        if not e:
            self.cursor.execute(
                '''
                INSERT INTO stores (name, url)
                VALUES (?, ?)
                ''', (store.name, store.url))
            self.conn.commit()
            e = fetchone()

        return Store(e['id'], e['name'], e['url'])
    
    def add_product(self, product):
        def fetchone():
            resp = self.cursor.execute(
                '''
                SELECT * FROM products 
                WHERE
                  sku = ? AND
                  store_id = ? AND
                  album_id = ? AND
                  item_type = ?
                LIMIT 1                                        
                ''', (product.sku, product.store.sId, product.album.aId, product.item_type))
            return resp.fetchone()

        p = fetchone()
        if not p:
            self.cursor.execute(
                '''
                INSERT INTO products 
                  (sku, album_id, store_id, item_type, link, price,
                   in_stock, quantity, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (product.sku, product.album.aId, product.store.sId, product.item_type,
                      product.link, product.price, product.in_stock, product.quantity, product.description))
            self.conn.commit()
        else:
            # potentially update
            if product.link != p['link'] or \
               product.price != p['price'] or \
               product.in_stock != p['in_stock'] or \
               product.quantity != p['quantity'] or \
               product.description != p['description']:
                self.cursor.execute(
                    '''
                    UPDATE products
                    SET
                      link = ?,
                      price = ?,
                      in_stock = ?,
                      quantity = ?,
                      description = ?,
                      last_seen_at = (datetime(current_timestamp)),
                      updated_at = (datetime(current_timestamp))
                    WHERE id = ?
                    ''', (product.link, product.price, product.in_stock,
                          product.quantity, product.description, p['id']))
            else:
                # definitely set the last_seen_at
                self.cursor.execute('''UPDATE products SET last_seen_at = (datetime(current_timestamp))''')

            self.conn.commit()
            
        return True

        
    ## Private ##
    def create_verify_database(self):
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS albums (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              artist TEXT,
              title TEXT,
              cover TEXT,
              thumbnail TEXT,
              inserted_at TEXT default (datetime(current_timestamp)),
              updated_at TEXT default (datetime(current_timestamp))
            )
            ''')
        
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS stores (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              url TEXT,
              inserted_at TEXT default (datetime(current_timestamp)),
              updated_at TEXT default (datetime(current_timestamp))
            )
            ''')

        
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS products (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sku TEXT,
              album_id INTEGER,
              store_id INTEGER,
              item_type TEXT,
              link TEXT,
              price INTEGER DEFAULT 0,
              in_stock INTEGER DEFAULT -1,
              quantity INTEGER DEFAULT 0,
              description TEXT DEFAULT '',
              last_seen_at TEXT default (date(current_timestamp)),
              inserted_at TEXT default (datetime(current_timestamp)),
              updated_at TEXT default (datetime(current_timestamp)),
              FOREIGN KEY(album_id) REFERENCES albums(id),
              FOREIGN KEY(store_id) REFERENCES store(id)
            )
            ''')

        self.cursor.execute('''CREATE INDEX IF NOT EXISTS sku_index ON products(sku)''')
        
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS version (
              version INTEGER default 1
            );
            ''')

        self.conn.commit()

        # verify the version
        e = self.cursor.execute('''SELECT version from version LIMIT 1''')
        r = e.fetchone()
        if r is None:
            # first time, set the version
            self.cursor.execute('''INSERT INTO version VALUES (?)''', (DB.VERSION,))
            self.conn.commit()
        elif r[0] != DB.VERSION:
            raise Exception('Database is out of date. Please migrate or remove')

        return True
