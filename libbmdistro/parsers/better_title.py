# bmdistro
# (c) 2021 Marcus Dillavou <line72@line72.net>
#
# Released under the GPLv3

import re

def better_title(s):
    '''
    A smarter title function.

    Create by ChatGPT:
    https://chatgpt.com/c/e91d8c3d-0f2d-422f-a63e-ba7101e0917f
    '''
    # special names where the beginning isn't caps
    special = (
        re.compile(r"^(d')([a-zA-Z].*)$"), # d'Suisse
    )
    # special names where the part after the ' is caps
    special2 = (
        re.compile(r"^(o')([a-zA-Z].*)$"), # O'Reilly
    )
    keep_lower = ("van", "von", "de", "des" "da", "du" "la", "le", "di", "del")

    if s is None:
        return None
    
    def valid_roman_numeral(s):
        # Searching the input string in expression and
        # returning the boolean value
        return bool(re.search(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", s.upper()))

    def matches_special(s):
        # checks for d'Suisse style
        for r in special:
            if (m := r.match(s)):
                return f'{m.group(1)}{m.group(2).capitalize()}'
        return False

    def matches_special2(s):
        # checks for O'Reilly style
        for r in special2:
            if (m := r.match(s)):
                return f'{m.group(1).capitalize()}{m.group(2).capitalize()}'
        return False

    # split at non character boundaries (although include ')
    words = re.split(r'([^\w\'])', s)
    capitalized_words = []

    for i, word in enumerate(words):
        # special cases
        if valid_roman_numeral(word):
            capitalized_words.append(word.upper())
        elif word in keep_lower:
            capitalized_words.append(word)
        elif (m := matches_special(word)):
            capitalized_words.append(m)
        elif (m := matches_special2(word)):
            capitalized_words.append(m)
        elif word.startswith("'"):
            capitalized_words.append(f"'{word[1:].capitalize()}")
        else:
            capitalized_words.append(word.capitalize())

    return ''.join(capitalized_words)


if __name__ == '__main__':
    def test(x, expected):
        r2 = better_title(x)
        success = '✅' if r2 == expected else '❌'
        print(f"{success}: {x} == {expected} | {r2}")
    
    # Test cases
    test("thorup van orman", "Thorup van Orman")
    test("john d'suisse", "John d'Suisse")
    test("mark paul iii", "Mark Paul III")
    test("they're", "They're")
    test("hello world!", "Hello World!")
    test("'tis the season", "'Tis The Season")
    test("well-known fact", "Well-Known Fact")
    test('"quoted" words', '"Quoted" Words')
    test("john o'reilly", "John O'Reilly")
    test("mcXii", "MCXII")
    test("miim", "Miim")
    test("død", "Død")
    test("sombre héritage", "Sombre Héritage")
