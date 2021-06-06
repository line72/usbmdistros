# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

class Album:
    def __init__(self, artist, title, item_type):
        self.artist = artist
        self.title = title
        self.item_type = item_type
        self.image_links = set()

    def add_image_link(self, link):
        self.image_links.add(link)
        
