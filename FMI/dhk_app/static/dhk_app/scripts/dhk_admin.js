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
Vue.component('treeselect', VueTreeselect.Treeselect)

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
        m_treeselect_value: null,
        recipe: null,
        recipe_scrape_results: [],
        treeselect_options: [],
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
        recipe_scrape_click: function () {
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
            var sub = this.m_treeselect_value;
            var page = this.m_page;
            if (page == "All Categories") {
                page = ""
            }
            this.$http.get(recipe_scrape_url, { params: { domain: this.m_domain, page_type: this.m_page_type, sub: sub, page: page } }).then(response => {
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
            if (this.m_page_type == 'index_page') {
                this.m_page = this.m_site_page;
            } else {
                this.m_page = this.m_site_page[1];
                this.m_treeselect_value = this.m_site_page[0];
            }
        }
    },
    computed: {
    },
    mounted: function () {
        for (const cat in taxonomy) {
            var cat_node = { id: cat, label: cat };
            var children = [];
            for (var ix = 0; ix < taxonomy[cat].length; ix++) {
                var sub = taxonomy[cat][ix];
                var sub_node = { id: sub, label: sub }
                children.push(sub_node);
            }
            cat_node['children'] = children;
            this.treeselect_options.push(cat_node);
        }
    },

});
