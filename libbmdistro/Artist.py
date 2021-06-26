# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Artist:
    def __init__(self, aId, name, genre_updated_at = None):
        self.aId = aId
        self.name = name
        self.genre_updated_at = genre_updated_at
        self.genres = []

    def __str__(self):
        return f"<Aritst::{self.name}>"
