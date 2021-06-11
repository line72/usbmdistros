# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import glob
import os
import requests
import shutil
import subprocess

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

        keys = sorted(db.items.keys())
        for artist in keys:
            v = db.items[artist]
            for album, v2 in v.items():
                variants = v2.keys()

                s = f'{artist}-{album}'
                s = s.lower()
                s = s.replace('/', '-').replace('*', '').replace(' ', '_')

                # check the cache or download the artwork
                (cover, thumb) = self.download_artwork(artist, album, s)
                if cover:
                    shutil.copy(cover, os.path.join(image_dir, os.path.basename(cover)))
                if thumb:
                    shutil.copy(thumb, os.path.join(image_dir, os.path.basename(thumb)))

                def get_prices():
                    prices = []
                    for v3 in v2.values():
                        for p in v3['products']:
                            prices.append(p.price)

                    min_price, max_price = min(prices), max(prices)
                    if min_price != max_price:
                        return f'{min_price} - {max_price}'
                    
                    return max_price

                prices = get_prices()
                    
                with open(os.path.join(base_directory, 'content', 'products', f'{s}.md'), 'w') as f:
                    f.write('---\n')
                    f.write(f'title: "{artist} - {album}"\n')
                    f.write('date: 2021-02-04T00:00:00-00:00\n')
                    f.write('draft: false\n')
                    f.write(f'artist: "{artist}"\n')
                    f.write(f'album: "{album}"\n')
                    f.write('categories:\n')
                    for i in variants:
                        f.write(f'    - {i}\n')
                    f.write('images:\n')
                    if cover:
                        f.write(f'    - /images/covers/{os.path.basename(cover)}\n')
                    else:
                        f.write(f'    - /images/blank-record.svg\n')
                    if thumb:
                        f.write(f'thumbnailImage: /images/covers/{os.path.basename(thumb)}\n')
                    else:
                        f.write(f'thumbnailImage: /images/blank-record.svg\n')
                    f.write(f'actualPrice: ${prices}\n')
                    f.write('inStock: true\n')
                    f.write('---\n')
                    f.write('\n')
                
                    for item_type, v3 in v2.items():
                        f.write(f'## {item_type}\n')
                        for p in v3['products']:
                            f.write(f'* Purchase from [{p.store.name}]({p.link}) for ${p.price}\n')

    def download_artwork(self, artist, album, name):
        print(f'Downloading artwork for {artist} - {album}')
        try: os.makedirs('__cache__')
        except OSError: pass
        
        cover, cover_thumbnail = self.get_covers(name)
        # if the file exists, don't re-download
        if cover and cover_thumbnail:
            print('Skipping...cover already exists')
            return (cover, cover_thumbnail)

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

