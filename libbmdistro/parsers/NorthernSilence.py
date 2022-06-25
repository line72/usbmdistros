# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

from .Parse import Parser
from ..Product import Product

URL='https://store.northern-silence.de/en/lpsmlps/blackfolkpagan/'

class NorthernSilence(Parser):
    def __init__(self, store, cookie = None):
        super().__init__(store, URL)

        self.cookies = {}
        if cookie:
            self.cookies = self.split_cookie_str(cookie)
        
    def parse(self, db):
        entries = []

        page = 1
        while True:
            r = requests.get(self.feed, params = {'p': page}, cookies = cookies)
            r.raise_for_status()
            page += 1

            soupe = BeautifulSoup(r.text, features = 'lxml')
            products = soup.find_all('div', 'product--box')
            if len(products) == 0:
                break

            p = itertools.chain.from_iterable(map(lambda e: self.parseItem(db, e), products))
            entries.extend(list(p))
        
        return entries

    def parseItem(self, db, entry):
        products = []

        sku = entry['data-ordernumber']
        product_title = entry.find('a', 'product--title')
        desc = entry.find('div', 'product--description')
        description = lambda: desc.text.strip() if desc else ''

        price = self.parse_price(entry.find('span', 'price--default').text)
        
        artist, title, extra, format_ = self.parse_title(product_title['title'])
        item_type = self.parse_format(format_)

        album = db.get_album(artist, title)
        products.append(Product(None, sku, album, self.store, '', item_type, price, Product.STOCK_UNKNOWN, -1, extra))
        
        return products

    def parse_title(self, t):
        # sometimes we have some weird unicode - (8206 8211)
        r = re.compile(r'^(?P<artist>.*?)(-|‎–)(?P<album>.*?)(\[(?P<extra>.*)\])?,? (?P<format>[a-zA-Z0-9"\+]+)$')
        g = r.match(t)
        if g:
            extra = g.group('extra').strip() if g.group('extra') else ''
            format_ = g.group('format').strip() if g.group('format') else ''
            return (g.group('artist').strip(), g.group('album').strip(), extra, format_)
        else:
            raise Exception(f'Unable to parse title: {t}')

    def parse_price(self, p):
        r = re.compile(r'.*?(?P<price>\d+\.\d+) .*?')
        g = r.match(p)
        if g:
            return g.group('price')
        else:
            raise Exception(f'Unable to parse price: {p}')

    def parse_format(self, format_):
        #!mwd - TODO
        return 'Vinyl'
        
    def split_cookie_str(self, cookie):
        cookies = {}
        for i in cookie.split(';'):
            s = i.split('=', maxsplit = 1)
            if len(s) == 2:
                k, v = s
                cookies[k] = v

        return cookies
        
