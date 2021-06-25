# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Artist:
    def __init__(self, aId, name):
        self.aId = aId
        self.name = name
        self.genres = []

    def __str__(self):
        return f"<Aritst::{self.name}>"
