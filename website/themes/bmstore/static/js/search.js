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
            searchBox.addEventListener('keypress', (evt) => {
                // Only do something upon pressing enter
                if (evt.keyCode == 13 && evt.target.value.length > 2) {
                    let results = search(evt.target.value, lunrIndex, pagesIndex);
                    render(results);
                }
            });
            
            // enable search
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

function render(results) {
    // remove anything in the search-results
    let body = document.querySelector('#search-results');

    let article = document.createElement('article');
    article.classList.add('container-fluid');

    let row = document.createElement('div');
    row.classList.add('row');
    article.appendChild(row);

    // add the results
    if (results.length > 0) {
        results.forEach((r) => {
            let a = document.createElement('a');
            a.classList.add('col-6', 'col-lg-3');
            a.setAttribute('href', `/products${r.href}`);

            // create the image preview
            let d = document.createElement('div');
            d.classList.add('album-list-preview-container');
            let img = document.createElement('img');
            img.classList.add('img-fluid', 'text-center', 'album-list-preview');
            img.setAttribute('src', r.thumbnail);
            d.appendChild(img);
            a.appendChild(d);

            // and the title
            let p = document.createElement('p');
            p.classList.add('text-left');
            let span = document.createElement('span');
            span.style.fontSize = '13px';
            let title = document.createTextNode(r.title);
            span.appendChild(title);
            p.appendChild(span);
            a.appendChild(p);
            
            row.appendChild(a);
        });
    } else {
        let h = document.createElement('h2');
        h.appendChild(document.createTextNode('No Results Found...'));
        row.appendChild(h);
    }

    // replace whatever is in body with the article
    body.replaceChildren(article);

    // show the modal
    $('#search-results-modal').modal({backdrop: 'static', keyboard: false});
}

// function createModal() {
//     // create a div overlay to put the results in
//     let modal = document.createElement('div');
//     modal.classList.add('modal', 'fade');

//     // the dialog
//     let modalDialog = document.createElement('div')
//     modalDialog.classList.add('modal-dialog');
//     modal.appendChild(modalDialog);

//     // the content
//     let modalContent = document.createElement('div');
//     modalContent.classList.add('modal-content');
//     modalDialog.appendChild(modalContent);

//     // the header
//     let modalHeader = document.createElement('div');
//     modalHeader.classList.add('modal-header');
//     modalContent.appendChild(modalHeader);

//     let h5 = document.createElement('h5');
//     h5.classList.add('modal-title');
//     h5.appendChild(document.createTextNode('Search Results'));
//     modalHeader.appendChild(h5);

//     let closeButton = document.createElement('button');
//     closeButton.classList.add('close');
//     closeButton.setAttribute('type', 'button');
//     closeButton.setAttribute('aria-label', 'Close');
//     closeButton.addEventListener('onclick', () => closeModal(modal));
//     modalHeader.appendChild(closeButton);

//     let s = document.createElement('span');
//     s.setAttribute('aria-hidden', 'true');
//     s.appendChild(document.createTextNode('&times;'));
//     closeButton.appendChild(s);

//     // the body
//     let body = document.createElement('div');
//     body.classList.add('modal-body');
//     modalContent.appendChild(body);

//     // tmp
//     let p = document.createElement('p');
//     p.appendChild(document.createTextNode('Doing a search...'));
//     body.appendChild(p);

//     return [modal, body];
// }

// function closeModal(modal) {
    
// }
    
window.addEventListener('load', () => {
    initSearch();
});
