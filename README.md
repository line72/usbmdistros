# US Black Metal Distributors Index
Copyright (c) 2021 Marcus Dillavou <line72@line72.net>

[U.S. Black Metal Distributors Index](https://www.usbmdistros.com)

This repo consists of two parts:

1. A python script/module to parse feeds of various US Black Metal distributor websites to catalog their products
2. A static website based on hugo

## Building the Site

You can build the site by running:

```sh
python3 bmdistro
```

This will cache over art in the `__cache__` folder. Cover art is
pulled from musicbrainz, and a lot of it fails.

Once complete, this will write everything in the `website/` directory.

## Running the Site

The website uses hugo to generate the static site.

```sh
cd website/
hugo server -D
```

Then open up your browser to http://localhost:1313


## License

Everything is licensed under the GPLv3.
