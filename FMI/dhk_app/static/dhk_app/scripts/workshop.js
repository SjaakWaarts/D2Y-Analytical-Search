// script.js

'use strict';

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var get_recipe_url = $("input[name=get_recipe_url]").val();
var get_workshops_url = $("input[name=get_workshops_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

function yyyymmdd(dateIn) {
    var yyyy = dateIn.getFullYear();
    var mm = dateIn.getMonth() + 1; // getMonth() is zero-based
    var dd = dateIn.getDate();
    var yyyymmdd = String(yyyy + "-" + mm + "-" + dd); // Leading zeros for mm and dd
    return yyyymmdd;
}

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        filter_facets: {
            author: [],
            published_date: "",
            cook: [],
            categories: [],
            cooking_date: { 'start': null, 'end': null }
        },
        sort_facets: {},
        query_string: null,
        pager: { page_nr: 1, nr_hits: 0, page_size: 25, nr_pages: 0, page_nrs: [], nr_pages_nrs: 5 },
        workbook: null,
        hits: [],
        aggs: [],
        carousel_images : null,
        workshops: null,
    },
    methods: {
        accordion_collapse: function (hide) {
            var accordion_item_elms = document.getElementsByClassName("accordion-item");
            for (var ix = 0; ix < accordion_item_elms.length; ix++) {
                var accordion_item_elm = accordion_item_elms[ix];
                var field = accordion_item_elm.getAttribute("name");
                var accordion_arrow_elm = accordion_item_elm.getElementsByClassName("accordion_arrow")[0];
                var accordion_item_content_elm = accordion_item_elm.getElementsByClassName("accordion-item-content")[0];
                if (hide && accordion_arrow_elm.classList.contains('accordion_arrow--open')) {
                    accordion_arrow_elm.classList.remove('accordion_arrow--open');
                    accordion_item_content_elm.style.display = "none";
                }
                if (!hide && !accordion_arrow_elm.classList.contains('accordion_arrow--open')) {
                    accordion_arrow_elm.classList.add('accordion_arrow--open');
                    accordion_item_content_elm.style.display = "block";
                }
            }
        },
        accordion_arrow_toggle: function (event) {
            var accordion_header_elm = event.currentTarget;
            var accordion_item_elm = accordion_header_elm.closest(".accordion-item");
            var field = accordion_item_elm.getAttribute("name");
            var accordion_arrow_elm = accordion_item_elm.getElementsByClassName("accordion_arrow")[0];
            var accordion_item_content_elm = accordion_item_elm.getElementsByClassName("accordion-item-content")[0];
            if (accordion_arrow_elm.classList.contains('accordion_arrow--open')) {
                accordion_arrow_elm.classList.remove('accordion_arrow--open');
                accordion_item_content_elm.style.display = "none";
            } else {
                accordion_arrow_elm.classList.add('accordion_arrow--open');
                accordion_item_content_elm.style.display = "block";
            }
        },
        bind_stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
        calendar_item_click: function (calendar_item) {
            this.id = calendar_item.id;
            var cooking_club = calendar_item.extendedProps;
            this.jump_to_recipe(this.id);
        },
        facet_filter: function (facet_name) {
            var facet = this.workbook.facets[facet_name];
            this.get_cooking_clubs();
        },
        get_workshops: function (sort = null) {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            if (sort) {
                if (sort in this.sort_facets) {
                    this.sort_facets[sort] = (this.sort_facets[sort] === 'asc' ? 'desc' : 'asc');
                }
                else {
                    this.sort_facets[sort] = 'asc';
                }
            } else {
                this.sort_facets = {};
            }
            if (this.workbook) {
                for (var fix = 0; fix < this.workbook.filters.length; fix++) {
                    var facet_name = this.workbook.filters[fix];
                    var facet = this.workbook.facets[facet_name];
                    this.filter_facets[facet_name] = facet.value;
                }
            }
            this.$http.post(get_workshops_url, {
                'csrfmiddlewaretoken': csrftoken,
                filter_facets: this.filter_facets,
                sort_facets: this.sort_facets,
                pager: this.pager,
                q: this.query_string
            },
                { 'headers': headers }).then(response => {
                    //this.hits = JSON.parse(response.bodyText);
                    this.workbook = response.body.workbook;
                    this.pager = response.body.pager;
                    if ('hits' in response.body.hits) {
                        this.hits = response.body.hits.hits;
                    }
                    if ('aggs' in response.body) {
                        this.aggs = response.body.aggs;
                    }
                    this.workbook = response.body.workbook;
                    this.workshops = response.body.workshops;
                    this.pager.nr_hits = response.body.hits.total;
                    // nr_pages needed to call computed component.page_nrs
                    this.pager.nr_pages = Math.ceil(this.pager.nr_hits / this.pager.page_size);
                    this.carousel_images = [];
                    var pathname = window.location.pathname.split('/');
                    for (var wix = 0; wix < this.workshops.length; wix++) {
                        for (var iix = 0; iix < this.workshops[wix].images.length; iix++) {
                            this.carousel_images.push(this.workshops[wix].images[iix]);
                        }
                    }
                });
        },
        jump_to_recipe(id) {
            var url = this.recipe_url('recipe', id);
            window.location.href = url;
        },
        recipe_url(url, id) {
            return url + '?id=' + id;
        },
        reset_search: function () {
            for (var fix = 0; fix < this.workbook.filters.length; fix++) {
                var facet_name = this.workbook.filters[fix];
                var facet = this.workbook.facets[facet_name];
                if (facet.type == 'terms') {
                    facet.value = [];
                } else if (['term', 'text'].includes(facet.type)) {
                    facet.value = null;
                } else if (facet.type == 'period') {
                    facet.value.start = null;
                    facet.value.end = null;
                } else {
                    facet.value = null;
                }
            }
            this.get_cooking_clubs();
        },
    },
    computed: {
    },
    mounted: function () {
        var today = new Date();
        this.get_workshops();
    },
});

