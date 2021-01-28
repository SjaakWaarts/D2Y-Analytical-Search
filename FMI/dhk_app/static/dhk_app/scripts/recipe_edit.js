// script.js

'use strict';

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var recipe_get_url = $("input[name=recipe_get_url]").val();
var recipe_edit_url = $("input[name=recipe_edit_url]").val();
var recipe_post_url = $("input[name=recipe_post_url]").val();
var recipe_carousel_images_search_url = $("input[name=recipe_carousel_images_search_url]").val();
var recipe_carousel_post_url = $("input[name=recipe_carousel_post_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        alert: null,
        average_rating: null,
        carousel_checked: [],
        carousel_unchecked: [],
        error_messages: {},
        image_search : '',
        hits: [],
        id: '',
        m_featured_ix: 0,
        recipe: null,
        shopping_basket: [],
    },
    methods: {
        bind_recipe_edit_url() {
            var url = recipe_edit_url + '?id=' + this.id;
            return encodeURI(url);
        },
        bind_recipe_get_url(format = 'json') {
            var url = recipe_get_url + '?id=' + this.id + '&format=pdf';
            return encodeURI(url);
        },
        bind_recipe_mail_review_url() {
            var url = "mailto:review@deheerlijkekeuken.nl?subject=" + this.id + "&body=<Plaats hier uw review EN foto's...>%0D%0A%0D%0AVoor een correcte verwerking, verander het Onderwerp niet!%0D%0ABedankt voor u review.";
            return url;
        },
        bind_stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
        recipe_get: function () {
            this.$http.get(recipe_get_url, { params: { id: this.id, format: 'json'  } }).then(response => {
                this.recipe = response.body.recipe;
                this.reviews = response.body.reviews;
                for (var ix = 0; ix < this.recipe.images.length; ix++) {
                    var src = this.recipe.images[ix].location;
                    if (['image', 'media'].includes(this.recipe.images[ix].type)) {
                        src = encodeURI(api_stream_file_url + '?location=' + this.recipe.images[ix].location)
                    }
                    var slide = {
                        'location': this.recipe.images[ix].location,
                        'src' : src,
                        'featured': (ix === 0) ? true : false,
                        'checked': true,
                        'type': this.recipe.images[ix].type
                    }
                    this.carousel_checked.push(slide)
                }
                this.image_search = this.recipe.title;
            });
        },
        recipe_image_radio_click(slide_ix) {
            this.carousel_checked[0].featured = false;
            const slide = this.carousel_checked.splice(slide_ix, 1)[0];
            slide.featured = true;
            this.carousel_checked.splice(0, 0, slide)
            // repeat in updated hook to force the radio button to be set
            this.m_featured_ix = 0
        },
        recipe_image_select_click(slide_ix, checked) {
            if (checked) {
                var slide = this.carousel_checked.splice(slide_ix, 1)[0]
                slide.checked = false;
                this.carousel_unchecked.push(slide)
            } else {
                var slide = this.carousel_unchecked.splice(slide_ix, 1)[0]
                slide.checked = true;
                this.carousel_checked.push(slide);
            }
        },
        recipe_image_shift_click(slide_ix, direction) {
            const slide = this.carousel_checked.splice(slide_ix, 1)[0];
            var offset = (direction == 'right') ? 1 : -1;
            this.carousel_checked.splice(slide_ix + offset, 0, slide);
            if (slide_ix + offset == 0) {
                this.carousel_checked[1].featured = false;
                this.carousel_checked[0].featured = true;
                this.m_featured_ix = 0
            }
        },
        recipe_carousel_images_search_click: function () {
            var review = {};
            var textarea_tag = document.getElementById("search_text");
            this.image_search = textarea_tag.value;
            this.alert = "Zoekt...";
            this.$http.get(recipe_carousel_images_search_url, { params: { id: this.id, q: this.image_search } }).then(response => {
                var thumbnails = response.body.thumbnails;
                if (thumbnails) {
                    this.alert = null
                } else {
                    this.alert = "Fout!"
                    return;
                };
                this.carousel_unchecked = this.carousel_unchecked.filter(function (slide) {return slide.type != 'search'});
                for (var ix = 0; ix < thumbnails.length; ix++) {
                    var slide = {
                        'location': null,
                        'src': thumbnails[ix]['src'],
                        'alt': thumbnails[ix]['alt'],
                        'featured': false,
                        'checked': false,
                        'type' : 'search'
                    }
                    this.carousel_unchecked.push(slide)
                }
            });
        },
        recipe_carousel_post: function () {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            this.alert = "Save...";
            this.$http.post(recipe_carousel_post_url, {
                'csrfmiddlewaretoken': csrftoken,
                'id': this.recipe.id,
                'carousel' : this.carousel_checked,
            },
                { 'headers': headers }).then(response => {
                    this.recipe = response.body.recipe;
                    this.alert = null;
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
    updated: function () {
        this.m_featured_ix = 0;
    },
});


function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


