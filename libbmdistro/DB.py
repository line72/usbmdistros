# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import datetime
import sqlite3

from .Album import Album
from .Artist import Artist
from .Cover import Cover
from .Product import Product
from .Store import Store

class DB:
    VERSION = 3
    
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

    def get_all_artists(self, preload_genres = False):
        # a cursors iterator is shared
        #  so create a new one
        cur = self.conn.cursor()
        resp = cur.execute('''SELECT * FROM artists ORDER BY id''')

        def load_genres(i):
            artist = Artist(i['id'], i['name'], i['genre_updated_at'])

            if preload_genres:
                cur2 = self.conn.cursor()
                resp = cur2.execute(
                    '''
                    SELECT 
                      g.name AS name
                    FROM
                      genres AS g,
                      artists AS a,
                      artists_genres as ag
                    WHERE
                      a.id = ? AND
                      ag.artist_id = a.id AND
                      ag.genre_id = g.id
                    ''', (artist.aId,))
                
                artist.genres = list(x['name'] for x in resp)
                
            return artist
        
        return map(load_genres, resp)
    
    def get_all_albums(self, preload_covers = False):
        # a cursors iterator is shared
        #  so create a new one
        cur = self.conn.cursor()
        resp = cur.execute(
            '''
            SELECT
              a.id AS artist_id,
              a.name AS name,
              a.genre_updated_at AS genre_updated_at,
              al.id AS album_id,
              al.title AS title
            FROM
              albums AS al,
              artists AS a
            WHERE
              al.artist_id = a.id
            ORDER BY 
              al.id
            ''')

        def load_covers(i):
            artist = Artist(i['artist_id'], i['name'],i['genre_updated_at'])
            a = Album(i['album_id'], artist, i['title'])
            
            if preload_covers:
                cur2 = self.conn.cursor()
                resp = cur2.execute('''SELECT * from covers WHERE album_id = ? ORDER BY id''', (i['album_id'],))
                a.covers = list(map(lambda c: Cover(c['id'], c['url'], c['official']), resp))

            return a
        
        return map(load_covers, resp)

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
        

    def get_artist(self, name, preload_genres = False):
        def load_genres(i):
            artist = Artist(i['id'], i['name'], i['genre_updated_at'])

            if preload_genres:
                cur2 = self.conn.cursor()
                resp = cur2.execute(
                    '''
                    SELECT 
                      g.name AS name
                    FROM
                      genres AS g,
                      artists AS a,
                      artists_genres as ag
                    WHERE
                      a.id = ? AND
                      ag.artist_id = a.id AND
                      ag.genre_id = g.id
                    ''', (artist.aId,))
                
                artist.genres = list(x['name'] for x in resp)
                
            return artist
        
        r = self.cursor.execute(
            '''
            SELECT * FROM artists
            WHERE
              LOWER(name) = LOWER(?)
            ''', (name,))
        a = r.fetchone()
        if a:
            artist = load_genres(a)
            return artist
        else:
            return None
    
    def get_album(self, artist, title):
        def fetch_artist():
            resp = self.cursor.execute(
                '''
                SELECT * FROM artists
                WHERE
                  LOWER(name) = LOWER(?)
                ''', (artist,))

            return resp.fetchone()
        
        def fetch_album(artist_id):
            resp = self.cursor.execute(
                '''
                SELECT * FROM albums
                WHERE
                  artist_id = ? AND
                  LOWER(title) = LOWER(?)
                ''', (artist_id, title))

            return resp.fetchone()

        a = fetch_artist()
        if not a:
            self.cursor.execute(
                '''
                INSERT INTO artists (name)
                VALUES (?)
                ''', (artist,))
            self.conn.commit()
            a = fetch_artist()
        
        e = fetch_album(a['id'])
        if not e:
            self.cursor.execute(
                '''
                INSERT INTO albums (artist_id, title)
                VALUES (?, ?)
                ''', (a['id'], title))
            self.conn.commit()
            e = fetch_album(a['id'])

        art = Artist(a['id'], a['name'], a['genre_updated_at'])
        return Album(e['id'], art, e['title'])

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
                   in_stock, quantity, description, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (product.sku, product.album.aId, product.store.sId, product.item_type,
                      product.link, product.price, product.in_stock, product.quantity, product.description,
                      datetime.datetime.utcnow()))
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

    def add_cover(self, album, url, official = False):
        def fetchone():
            resp = self.cursor.execute(
                '''
                SELECT * FROM covers
                WHERE
                  album_id = ? AND
                  url = ?
                LIMIT 1
                ''', (album.aId, url))
            return resp.fetchone()

        p = fetchone()
        if not p:
            self.cursor.execute(
                '''
                INSERT INTO covers
                  (album_id, url, official)
                VALUES (?, ?, ?)
                ''', (album.aId, url, official))
            self.conn.commit()

        return True

    def add_genre(self, artist, genre):
        def fetchone():
            resp = self.cursor.execute(
                '''SELECT * FROM genres WHERE name = ?''', (genre,))
            return resp.fetchone()

        g = fetchone()
        if not g:
            self.cursor.execute(
                '''
                INSERT INTO genres
                  (name)
                VALUES (?)
                ''', (genre,))
            self.conn.commit()
            g = fetchone()

        try:
            self.cursor.execute(
                '''
                INSERT INTO artists_genres
                  (artist_id, genre_id)
                VALUES (?, ?)
                ''', (artist.aId, g['id']))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # We already have this inserted
            #  and are getting an error due to
            #  the unique index.
            pass

        return True

    def artist_update_genre_timestamp(self, artist):
        self.cursor.execute(
            '''
            UPDATE artists
            SET
              genre_updated_at = (datetime(current_timestamp))
            WHERE
              id = ?
            ''', (artist.aId,))
        self.conn.commit()
    
    ## Private ##
    def create_verify_database(self):
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS version (
              version INTEGER default %s
            );
            ''' % DB.VERSION)

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

        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS artists (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              genre_updated_at timestamp default (datetime(0, 'unixepoch')),
              inserted_at timestamp default (datetime(current_timestamp)),
              updated_at timestamp default (datetime(current_timestamp))
            )
            ''')
        
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS albums (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              artist_id INTEGER,
              title TEXT,
              inserted_at timestamp default (datetime(current_timestamp)),
              updated_at timestamp default (datetime(current_timestamp)),
              FOREIGN KEY(artist_id) REFERENCES artists(id)
            )
            ''')
        
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS genres (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              inserted_at timestamp default (datetime(current_timestamp)),
              updated_at timestamp default (datetime(current_timestamp))
            )
            ''')
        
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS artists_genres (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              artist_id INTEGER,
              genre_id INTEGER,
              inserted_at timestamp default (datetime(current_timestamp)),
              updated_at timestamp default (datetime(current_timestamp)),
              FOREIGN KEY(artist_id) REFERENCES artists(id),
              FOREIGN KEY(genre_id) REFERENCES genres(id)
            )
            ''')
        
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS stores (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              url TEXT,
              inserted_at timestamp default (datetime(current_timestamp)),
              updated_at timestamp default (datetime(current_timestamp))
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
              last_seen_at timestamp default (datetime(current_timestamp)),
              inserted_at timestamp default (datetime(current_timestamp)),
              updated_at timestamp default (datetime(current_timestamp)),
              FOREIGN KEY(album_id) REFERENCES albums(id),
              FOREIGN KEY(store_id) REFERENCES stores(id)
            )
            ''')

        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS covers (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              album_id INTEGER,
              url TEXT,
              official INTEGER,
              inserted_at timestamp default (datetime(current_timestamp)),
              updated_at timestamp default (datetime(current_timestamp)),
              FOREIGN KEY(album_id) REFERENCES albums(id)
            )
            ''')

        self.cursor.execute('''CREATE INDEX IF NOT EXISTS sku_index ON products(sku)''')
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS artists_index on artists(name)''')
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS genres_index on genres(name)''')
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS artists_genres_index on artists_genres(artist_id,genre_id)''')

        self.conn.commit()
        
        return True
