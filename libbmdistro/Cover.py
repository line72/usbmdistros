# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Cover:
    def __init__(self, cId, url, official):
        self.cId = cId
        self.url = url
        self.official = official

    def __str__(self):
        return f"<Cover::{self.cId}:{self.url}({self.official})>"
