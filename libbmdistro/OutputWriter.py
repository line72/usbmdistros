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
import time
import yaml
import concurrent.futures

from .DB import DB

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
    def write(self, db, base_directory, last_seen_at):
        image_dir = os.path.join(base_directory, 'static', 'images', 'covers')
        try: os.makedirs(image_dir)
        except OSError: pass

        # Write out the Stores
        with open(os.path.join(base_directory, 'content', 'distributors.md'), 'w') as f:
            f.write('---\n')
            f.write('title: Distributors\n')
            f.write('date: 2021-06-13T00:00:00-00:00\n')
            f.write('draft: false\n')
            f.write('---\n')
            f.write('\n')
            for store in db.get_all_stores():
                f.write(f' * [{store.name}]({store.url})\n')

        # Write out the products
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            for i, album in enumerate(db.get_all_albums(True)):
                print(f'parsing {i}', album)
                artist = db.get_artist(album.artist.name, True)

                products = list(db.get_products_for_album(album, last_seen_at))

                futures.append(executor.submit(self.write_product_for_album,
                                               base_directory, image_dir,
                                               artist, album, products))

        # wait until all futures complete
        for f in futures:
            f.result()

    def write_product_for_album(self, base_directory, image_dir, artist, album, products):
        if len(products) == 0:
            print(f'{album}: Album has no available products, skipping...')
            return

        if len(artist.genres) == 0 or not self.is_black_metal(artist.genres):
            print(f'{album}: Skipping non-black metal artist: {artist}')
            return

        grouped_products = itertools.groupby(sorted(products,
                                                    key = lambda x: x.item_type),
                                             key = lambda x: x.item_type)
        # make sure to turn iterators into lists!
        product_dict = functools.reduce(lambda acc, v: dict(list(acc.items()) + [(v[0], list(v[1]))]), grouped_products, {})
        variants = list(sorted(product_dict.keys(), reverse = True))

        s = f'{album.artist.name}-{album.title}'
        s = s.lower()
        s = s.replace('/', '-').replace('*', '').replace(' ', '_')

        # create a new DB object in this thread.
        db = DB(False)

        # check the cache or download the artwork
        (cover, thumb) = self.download_artwork(db, album, s)
        if cover and not os.path.exists(os.path.join(image_dir, os.path.basename(cover))):
            shutil.copy(cover, os.path.join(image_dir, os.path.basename(cover)))
        if thumb and not os.path.exists(os.path.join(image_dir, os.path.basename(thumb))):
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
            def get_cover():
                if cover:
                    return f"/images/covers/{os.path.basename(cover)}"
                else:
                    return '/images/blank-record.svg'

            def get_thumbnail():
                if thumb:
                    return f"/images/covers/{os.path.basename(thumb)}"
                else:
                    return '/images/blank-record.svg'

            front_matter = {
                'title': f'{album.artist.name} - {album.title}',
                'date': last_modified.isoformat(),
                'draft': False,
                'artist': album.artist.name,
                'album': album.title,
                'categories': [x for x in variants],
                'images': [get_cover()],
                'thumbnailImage': get_thumbnail(),
                'actualPrice': f'${prices}',
                'inStock': True
            }

            f.write('---\n')
            yaml.dump(front_matter, f)
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
        
    def download_artwork(self, db, album, name, retry = 1):
        print(f'{album}: Checking artwork...')
        try: os.makedirs('__cache__')
        except OSError: pass
        
        cover, cover_thumbnail = self.get_covers(name)
        # if the file exists, don't re-download
        if cover and cover_thumbnail:
            print(f'{album}: Skipping...cover already exists')
            return (cover, cover_thumbnail)

        cover = os.path.join('__cache__', name + '.jpg')
        cover_thumbnail = os.path.join('__cache__', name + '-thumb.jpg')
        

        # check if we have an official one our database
        officials = filter(lambda c: c.official, album.covers)
        for o in officials:
            try:
                return self.do_download(o.url, cover, cover_thumbnail)
            except requests.exceptions.HTTPError as e:
                pass

        try:
            # move on to downloading from music brainz
            params = {
                'query': f'artist:{album.artist.name} AND album:{album.title}'
            }
            r = requests.get('https://musicbrainz.org/ws/2/release/',
                             params = params,
                             headers = {'accept': 'application/json'})
            r.raise_for_status()
            # get the first release
            releases = r.json()['releases']

            while len(releases) > 0:
                release = releases.pop()
                if release['score'] < 100:
                    continue
                
                rid = release['id']

                print(f'{album}: Downloading', rid)
                try:
                    url = f'https://coverartarchive.org/release/{rid}/front'
                    result = self.do_download(url, cover, cover_thumbnail)

                    # save this to the DB as the official
                    db.add_cover(album, url, True)

                    return result
                except requests.exceptions.HTTPError as e:
                    print(f'{album}: Error', e)
                    pass

            # check if we have any un-official one our database
            unofficials = filter(lambda c: not c.official, album.covers)
            for o in unofficials:
                try:
                    return self.do_download(o.url, cover, cover_thumbnail)
                except requests.exceptions.HTTPError as e:
                    pass

            raise Exception('No covers found')
        except requests.exceptions.HTTPError as e:
            # failed to get the list of releases
            if retry < 5:
                print(f'{album}: Backing off...')
                # back off and try again
                time.sleep(.2)
                return self.download_artwork(db, album, name, retry + 1)
            else:
                print(f'{album}: Out of retries', e)
                c = os.path.join('__cache__', name + '.png')
                t = os.path.join('__cache__', name + '-thumb.png')
                self.copy_default(c, t)
                return (c, t)
                
        except Exception as e:
            print(f'{album}: Exception', e)
            c = os.path.join('__cache__', name + '.png')
            t = os.path.join('__cache__', name + '-thumb.png')
            self.copy_default(c, t)
            return (c, t)

    def do_download(self, url, cover, cover_thumbnail):
        print(f'Downloading {url}')
        r = requests.get(url)
        r.raise_for_status()

        with open(cover, 'wb') as f:
            f.write(r.content)

        # generate the thumbnail
        self.generate_thumbnail(cover, cover_thumbnail)

        return (cover, cover_thumbnail)
        
    def get_covers(self, name):
        b = os.path.join('__cache__', name)

        cover = None
        thumb = None
        if os.path.exists(b + '.jpg'):
            cover = b + '.jpg'
        elif os.path.exists(b + '.png'):
            cover = b + '.png'

        if os.path.exists(b + '-thumb.jpg'):
            thumb = b + '-thumb.jpg'
        elif os.path.exists(b + '-thumb.png'):
            thumb = b + '-thumb.png'
        
        return (cover, thumb)
        
    def generate_thumbnail(self, img, thumb):
        subprocess.run(['convert', img, '-resize', '128x', thumb])
        
        return True

    def copy_default(self, cover, thumb):
        shutil.copy('resources/blank-vinyl.png', cover)
        self.generate_thumbnail(cover, thumb)
        
        return True
    
    def is_black_metal(self, genres):
        for genre in genres:
            if 'black metal' in genre.lower():
                return True

        return False
