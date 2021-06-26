# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import datetime
import requests
import time

class GenreFinder:
    def go(self, db):
        for artist in db.get_all_artists(True):
            if len(artist.genres) == 0:
                self.fetch_genres(db, artist)

    def fetch_genres(self, db, artist):
        print('fetch_genres', artist)

        if datetime.datetime.utcnow() - artist.genre_updated_at < datetime.timedelta(days = 7):
            print('Skipping, recently updated...')
            return True
        
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
            return self.fetch_genres(db, artist)
