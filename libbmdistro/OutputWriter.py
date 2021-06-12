# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import glob
import os
import requests
import shutil
import subprocess
import functools
import itertools

template = '''
---
title: "Fake Artist - Fake Album"
date: 2021-02-04T12:38:56-06:00
draft: false
artist: Fake Artist
album: Fake Album
categories:
    - Vinyl
    - Tape
actualPrice: $24.00
---
'''

class OutputWriter:
    def write(self, db, base_directory):
        image_dir = os.path.join(base_directory, 'static', 'images', 'covers')
        try: os.makedirs(image_dir)
        except OSError: pass

        for album in db.get_all_albums():
            print('parsing', album)

            products = list(db.get_products_for_album(album))
            grouped_products = itertools.groupby(sorted(products,
                                                        key = lambda x: x.item_type),
                                                 key = lambda x: x.item_type)
            # make sure to turn iterators into lists!
            product_dict = functools.reduce(lambda acc, v: dict(list(acc.items()) + [(v[0], list(v[1]))]), grouped_products, {})
            variants = list(sorted(product_dict.keys(), reverse = True))

            s = f'{album.artist}-{album.title}'
            s = s.lower()
            s = s.replace('/', '-').replace('*', '').replace(' ', '_')
            
            # check the cache or download the artwork
            (cover, thumb) = self.download_artwork(album.artist, album.title, s)
            if cover:
                shutil.copy(cover, os.path.join(image_dir, os.path.basename(cover)))
            if thumb:
                shutil.copy(thumb, os.path.join(image_dir, os.path.basename(thumb)))

            def get_prices():
                prices = [p.price for p in products]
                min_price, max_price = min(prices), max(prices)
                if min_price != max_price:
                    return f'{self.format_price(min_price)} - {self.format_price(max_price)}'

                return self.format_price(max_price)
                
            prices = get_prices()

            # get the most recent modified date of any product
            last_modified = max([p.updated_at for p in products])
            

            with open(os.path.join(base_directory, 'content', 'products', f'{s}.md'), 'w') as f:
                f.write('---\n')
                f.write(f'title: "{album.artist} - {album.title}"\n')
                f.write(f'date: {last_modified.isoformat()}\n')
                f.write('draft: false\n')
                f.write(f'artist: "{album.artist}"\n')
                f.write(f'album: "{album.title}"\n')
                f.write('categories:\n')
                for i in variants:
                    f.write(f'    - {i}\n')
                f.write('images:\n')
                if cover:
                    f.write(f'    - "/images/covers/{os.path.basename(cover)}"\n')
                else:
                    f.write(f'    - /images/blank-record.svg\n')
                if thumb:
                    f.write(f'thumbnailImage: "/images/covers/{os.path.basename(thumb)}"\n')
                else:
                    f.write(f'thumbnailImage: /images/blank-record.svg\n')
                f.write(f'actualPrice: ${prices}\n')
                f.write('inStock: true\n')
                f.write('---\n')
                f.write('\n')

                for item_type in variants:
                    variant_products = list(product_dict[item_type])
                    f.write(f'## {item_type}\n')
                    for p in variant_products:
                        if p.description:
                            f.write(f'* Purchase from [{p.store.name}]({p.link}) for ${self.format_price(p.price)} :: {p.description}\n')
                        else:
                            f.write(f'* Purchase from [{p.store.name}]({p.link}) for ${self.format_price(p.price)}\n')

    def format_price(self, p):
        return '{0:.2f}'.format(p / 100.)
        
    def download_artwork(self, artist, album, name):
        print(f'Downloading artwork for {artist} - {album}')
        try: os.makedirs('__cache__')
        except OSError: pass
        
        cover, cover_thumbnail = self.get_covers(name)
        # if the file exists, don't re-download
        if cover and cover_thumbnail:
            print('Skipping...cover already exists')
            return (cover, cover_thumbnail)

        cover = os.path.join('__cache__', name + '.jpg')
        cover_thumbnail = os.path.join('__cache__', name + '-thumb.jpg')
        
        params = {
            'query': f'artist:{artist} AND album:{album}'
        }
        r = requests.get('https://musicbrainz.org/ws/2/release/',
                         params = params,
                         headers = {'accept': 'application/json'})
        r.raise_for_status()
        # get the first release
        try:
            releases = r.json()['releases']

            while True:
                release = releases.pop()
                if release['score'] < 100:
                    continue
                
                rid = release['id']

                print('Downloading', rid)
                try:
                    r = requests.get(f'https://coverartarchive.org/release/{rid}/front')
                    r.raise_for_status()

                    with open(cover, 'wb') as f:
                        f.write(r.content)

                    # generate the thumbnail
                    self.generate_thumbnail(cover, cover_thumbnail)

                    return (cover, cover_thumbnail)
                except requests.exceptions.HTTPError as e:
                    print('Error', e)
                    pass


        except Exception as e:
            print('Exception', e)
            c = os.path.join('__cache__', name + '.png')
            t = os.path.join('__cache__', name + '-thumb.png')
            self.copy_default(c, t)
            return (c, t)

    def get_covers(self, name):
        covers = glob.glob(os.path.join('__cache__', name + '.*'))
        thumbs = glob.glob(os.path.join('__cache__', name + '-thumb.*'))

        cover = None
        thumb = None
        if len(covers) > 0:
            cover = covers[0]
        if len(thumbs) > 0:
            thumb = thumbs[0]

        return (cover, thumb)
        
    def generate_thumbnail(self, img, thumb):
        subprocess.run(['convert', img, '-resize', '128x', thumb])
        
        return True

    def copy_default(self, cover, thumb):
        shutil.copy('resources/blank-vinyl.png', cover)
        self.generate_thumbnail(cover, thumb)
        
        return True
