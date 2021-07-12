# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import datetime
import requests
import time
import concurrent.futures

from .DB import DB

class GenreFinder:
    LAST_FM_API_KEY = '88465cb34653ed17ec3755f1e4179ffd'
    
    def go(self, db):
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
            for artist in db.get_all_artists(True):
                if len(artist.genres) == 0:
                    print('fetch_genres', artist)

                    if datetime.datetime.utcnow() - artist.genre_updated_at < datetime.timedelta(days = 7):
                        print('Skipping, recently updated...')
                        continue

                    futures.append(executor.submit(self.fetch_genres_lastfm, None, artist))

        # wait until all futures complete
        for f in futures:
            f.result()
            
    def fetch_genres_lastfm(self, db, artist):
        if db is None:
            # create a new DB for this thread
            db = DB(False)
        
        try:
            params = {
                'method': 'artist.gettoptags',
                'artist': artist.name,
                'autocorrect': 0,
                'api_key': GenreFinder.LAST_FM_API_KEY,
                'format': 'json'
            }
            r = requests.get('https://ws.audioscrobbler.com/2.0/',
                             params = params,
                             headers = {'accept': 'application/json'})
            r.raise_for_status()

            resp = r.json()
            if 'error' in resp:
                if resp['error'] == 29:
                    # rate limit exceeded
                    print('Backing off...')
                    time.sleep(.1)
                    return self.fetch_genres_lastfm(db, artist)
                else:
                    print('Exception', resp)
            else:
                for tag in resp['toptags']['tag']:
                    if tag['count'] > 30:
                        db.add_genre(artist, tag['name'].lower())

            # update the artist
            db.artist_update_genre_timestamp(artist)
                        
        except requests.exceptions.HTTPError:
            # back-off
            print('Backing off...')
            time.sleep(.1)
            return self.fetch_genres_lastfm(db, artist)
            
                
    def fetch_genres_musicbrainz(self, db, artist):
        if db is None:
            # create a new DB for this thread
            db = DB(False)
        
        try:
            params = {
                'query': f'artist:{artist.name}'
            }
            r = requests.get('https://musicbrainz.org/ws/2/artist/',
                             params = params,
                             headers = {'accept': 'application/json'})
            r.raise_for_status()
            # get the first release
            try:
                artists = r.json()['artists']
                #print(artists)

                while len(artists) > 0:
                    a = artists.pop()
                    if a['score'] < 100:
                        continue

                    rid = a['id']
                    # lookup the genres
                    params = {
                        'inc': 'genres'
                    }
                    r2 = requests.get(f'https://musicbrainz.org/ws/2/artist/{rid}',
                                      params = params,
                                      headers = {'accept': 'application/json'})
                    r.raise_for_status()

                    j = r2.json()
                    genres = [g['name'] for g in j['genres']]
                    for g in genres:
                        db.add_genre(artist, g)

            except Exception as e:
                print('Exception', e)

            # update the artist
            db.artist_update_genre_timestamp(artist)

        except requests.exceptions.HTTPError:
            # back-off
            print('Backing off...')
            time.sleep(.1)
            return self.fetch_genres_musicbrainz(db, artist)
