import libbmdistro

if __name__ == '__main__':
    
    class FakeDB:
        def get_album(self, a, t):
            return libbmdistro.Album(1, a, t)
        
        def add_cover(self, _a, _i):
            pass

    db = FakeDB()
    entry = {
        'id': 1,
        'handle': 'xyz',
        'title': '[NESI-Rarity] Dark Tranquillity - The Gallery *NUMBERED* Ltd 200 Black + Red/Gold Splatter Vinyl - Asian Market Exclusive',
        'images': [],
        'product_type': '12"',
        'variants': [
            {
                'price': 20
            }
        ]
    }

    bbv = libbmdistro.parsers.BlastBeatsVinyl(None, None)
    p = bbv.parseItem(db, entry)
    assert p.album.artist == 'Dark Tranquillity'
    assert p.album.title == 'The Gallery'
    assert p.description == '*NUMBERED* Ltd 200 Black + Red/Gold Splatter Vinyl - Asian Market Exclusive'
