// script.js

'use strict';

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var recipe_get_url = $("input[name=recipe_get_url]").val();
var recipe_edit_url = $("input[name=recipe_edit_url]").val();
var recipe_post_url = $("input[name=recipe_post_url]").val();
var recipe_images_search_url = $("input[name=recipe_images_search_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        carousel_images: null,
        error_messages: {},
        hits: [],
        id: '',
        image_urls: [],
        recipe: null,
        shopping_basket: [],
    },
    methods: {
        bind_recipe_edit_url() {
            var url = recipe_edit_url + '?id=' + this.id;
            return encodeURI(url);
        },
        bind_recipe_get_url() {
            var url = recipe_get_url + '?id=' + this.id + '&format=pdf';
            return encodeURI(url);
        },
        bind_stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
        recipe_get: function () {
            this.$http.get(recipe_get_url, { params: { id: this.id, format: 'json'  } }).then(response => {
                this.recipe = response.body.recipe;
                this.reviews = response.body.reviews;
                this.carousel_images = this.recipe.images.concat(this.reviews);
            });
        },
        recipe_image_checkbox_click(image_url_ix) {
            var checkbox_tag = document.getElementById("image_url_" + image_url_ix);
            var checked = checkbox_tag.checked;
        },
        recipe_images_search_click: function () {
            var review = {};
            var textarea_tag = document.getElementById("search_text");
            var q = textarea_tag.value;
            this.$http.get(recipe_images_search_url, { params: { id: this.id, q: q } }).then(response => {
                this.image_urls = response.body.image_urls;
            });
        },
        recipe_post: function () {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            this.$http.post(recipe_post_url, {
                'csrfmiddlewaretoken': csrftoken,
                'recipe': this.recipe,
            },
                { 'headers': headers }).then(response => {
                    this.recipe = response.body.recipe;
                    this.draw_map();
                });
        },
    },
    computed: {
    },
    mounted: function () {
        var urlParams = new URLSearchParams(window.location.search);
        this.id = decodeURI(urlParams.has('id') ? urlParams.get('id') : '');
        this.recipe_get();
        if (user.username != "") {
        }
    },
});


function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


