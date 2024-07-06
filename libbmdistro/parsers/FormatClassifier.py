# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

classifications = {
    'lp': 'Vinyl',
    '10”': 'Vinyl',
    '10” ep': 'Vinyl',
    '12"': 'Vinyl',
    '12”': 'Vinyl',
    '12” ep': 'Vinyl',
    '12"': 'Vinyl',
    "12''": 'Vinyl',
    '12” lp': 'Vinyl',
    '12" lp': 'Vinyl',
    '12” mlp': 'Vinyl',
    '2xlp': 'Vinyl',
    '2x10" mlp': 'Vinyl',
    '10"': 'Vinyl',
    '7"': 'Vinyl',
    "7’’": 'Vinyl',
    '7" ep': 'Vinyl',
    "7’’ ep": 'Vinyl',
    'cd': 'CD',
    'tape': 'Cassette',
    'tapes': 'Cassette',
}
    
def classify(text):
    if text is None:
        return None
    
    t = classifications.get(text.lower(), None)
    if t is None:
        print(f'Unknown classification type: {text}')
        return None
        #raise Exception(f'Unknown classification type: {text}')
    
    return t
        
