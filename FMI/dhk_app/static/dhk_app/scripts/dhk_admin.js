// script.js
'use strict';

//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var upload_file_url = $("input[name=upload_file_url]").val();
var delete_recipe_url = $("input[name=delete_recipe_url]").val();
var get_uploaded_files_url = $("input[name=get_uploaded_files_url]").val();
var recipe_scrape_url = $("input[name=recipe_scrape_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        errors: [],
        filter_facets: {
            author: [],
            published_date: ""
        },
        sort_facets: {},
        query_string: null,
        pager: { page_nr: 1, nr_hits: 0, page_size: 25, nr_pages: 0, page_nrs: [], nr_pages_nrs: 5 },
        workbook: null,
        hits: [],
        aggs: [],
        current_recipe: '',
        current_recipeIX: null,
        m_domain: null,
        m_page: '',
        m_page_type: null,
        m_site_page: '',
        recipe: null,
        recipe_scrape_results: [],
        rows: [
            {
                "id": 1,
                "author": "Vladimir",
                "published_date": "2018-10-11",
                "title": "franecki.anastasia@gmail.com",
            },
            {
                "id": 2,
                "author": "Vladimir",
                "published_date": "2018-10-11",
                "title": "franecki.anastasia@gmail.com",
            },
            {
                "id": 3,
                "author": "Vladimir",
                "published_date": "2018-10-11",
                "title": "franecki.anastasia@gmail.com",
            }
        ],
        columns: [
            {
                label: "id",
                name: "id",
                filter: {
                    type: "simple",
                    placeholder: "id"
                },
                sort: true,
            },
            {
                label: "Van",
                name: "author",
                filter: {
                    type: "simple",
                    placeholder: "Van"
                },
                sort: true,
            },
            {
                label: "Datum",
                name: "published_date",
                sort: true,
            },
            {
                label: "Titel",
                name: "title",
                filter: {
                    type: "simple",
                    placeholder: "Titel"
                },
            }
        ],
        actions: [
            {
                btn_text: "Bekijk Recept",
                event_name: "on-edit",
                class: "btn btn-primary",
                event_payload: {
                    msg: "edit"
                }
            },
            {
                btn_text: "Verwijder Recept",
                event_name: "on-delete",
                class: "btn btn-primary",
                event_payload: {
                    msg: "delete"
                }
            }
        ],
        config: {
            checkbox_rows: false,
            rows_selectable: true,
            selected_rows_info: true,
            card_title: "Mijn Recepten"
        }
    },
    methods: {
        select_recipe(event) {
            var selected_item = event.selected_item;
            var selected_items = event.selected_items;
            var n = selected_items.length;
            for (var i = 0; i < n; i++) {
                selected_items.pop();
            }
            selected_items.push(selected_item);
        },
        // recipe_edit(event) {
        recipe_edit(id) {
            //var event_payload = event.event_payload;
            //var selected_items = event.selectedItems;
            var url = this.recipe_url('recipe', id);
            window.location.href = url;
        },
        delete_recipe(id) {
            //var event_payload = event.event_payload;
            //var selected_items = event.selectedItems;
            if (confirm('Weet je het zeker dat je dit recept wil verwijderen?')) {
                var csrftoken_cookie = getCookie('csrftoken');
                var headers = { 'X-CSRFToken': csrftoken_cookie }
                this.$http.post(delete_recipe_url, {
                    'csrfmiddlewaretoken': csrftoken,
                    'id': id,
                },
                    { 'headers': headers }).then(response => {
                        this.get_uploaded_files();
                    });
            }
        },
        facet_filter: function (facet_name) {
            var facet = this.workbook.facets[facet_name];
            this.get_uploaded_files();
        },
        get_uploaded_files: function (sort = null, uploaded_file_id = null) {
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
            this.$http.post(get_uploaded_files_url, {
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
                    this.pager.nr_hits = response.body.hits.total;
                    // nr_pages needed to call computed component.page_nrs
                    this.pager.nr_pages = Math.ceil(this.pager.nr_hits / this.pager.page_size);
                    if (uploaded_file_id) {
                        for (ix = 0; ix < this.hits.length; ix++) {
                            if (this.hits[ix]['id'] === uploaded_file_id) {
                                this.current_recipe = this.hits[ix];
                            }
                        }
                    }
                });
        },
        recipe_scrape_click: function (mode) {
            this.pages_scraped = [];
            this.errors = [];
            this.recipe_scrape_results = [];
            if (this.m_domain == null) {
                this.errors.push('Selecteer een site')
            }
            if (this.m_page_type == null) {
                this.errors.push('Selecteer een pagina type')
            }
            if (this.errors.length > 0) { return }
            this.$http.get(recipe_scrape_url, { params: { page_type : this.m_page_type, page: this.m_page, mode: mode } }).then(response => {
                var recipe = response.body.recipe;
                this.recipe_scrape_results = response.body.recipe_scrape_results;
            });
        },
        recipe_url(url, id) {
            if (id == '#') {
                return id
            } else {
                return url + '?id=' + id;
            }
        },
        reset_search: function () {
            for (var fix = 0; fix < this.workbook.filters.length; fix++) {
                var facet_name = this.workbook.filters[fix];
                var facet = this.workbook.facets[facet_name];
                facet.value = null;
            }
            this.get_uploaded_files();
        },
        select_site_page_change(event) {
            this.m_page = this.m_site_page;
        }
    },
    computed: {
    },
    mounted: function () {
    },

});
