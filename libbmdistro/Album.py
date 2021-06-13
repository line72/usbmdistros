# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Album:
    def __init__(self, aId, artist, title):
        self.aId = aId
        self.artist = artist
        self.title = title

    def __str__(self):
        return f"<Album::{self.artist}-{self.title}>"
