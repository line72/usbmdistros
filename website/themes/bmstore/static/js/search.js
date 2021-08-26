/**
 * search.js
 * Copyright (C) 2021 Marcus Dillavou <line72@line72.net>
 * License: GPLv3
 */

function initSearch() {
    let searchBox = document.querySelector('#search-box');
    searchBox.setAttribute('disabled', '');
    
    // retrieve the index file
    fetch("/js/lunr/PagesIndex.json")
        .then((r) => {
            if (!r.ok) {
                throw new Error(`Error downloading search index: ${r.status}`);
            }
            return r.json();
        })
        .then((r) => {
            // save this.
            const pagesIndex = r;

            const lunrIndex = lunr(function() {
                this.field("title");
                this.ref("href");

                pagesIndex.forEach((page) => {
                    this.add(page);
                });
            });


            // hook up a key-up to the search
            searchBox.addEventListener('keyup', (evt) => {
                console.log(evt);

                if (evt.target.value.length > 2) {
                    console.log('searching for', evt.target.value);

                    let results = search(evt.target.value, lunrIndex, pagesIndex);
                    console.log(results);
                    //render(results);
                }
            });
            
            // enable search
            console.log('enabling');
            searchBox.removeAttribute('disabled');
        })
        .catch((e) => {
            // disable search
            searchBox.style.display = 'none';
            
            console.warn(e);
        });
}

function search(term, lunrIndex, pagesIndex) {
    return lunrIndex
        .search(`${term}~1`) // add in a fuzziness of 1
        .sort((a, b) => b.score - a.score )
        .map((result) => {
            return pagesIndex.filter((p) => {
                return p.href == result.ref;
            })[0];
        });
}

window.addEventListener('load', () => {
    initSearch();
});
