// script.js

'use strict';

// JQuery

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var get_recipe_url = $("input[name=get_recipe_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        iframe_src: null,
        id : '',
        recipe : null,
        hits: [],
        current_course: '',
    },
    methods: {
        get_recipe: function () {
            this.$http.get(get_recipe_url, { params: { id: this.id }}).then(response => {
                this.recipe = response.body.recipe;
            });
        },
        stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
    },
    computed: {
    },
    mounted: function () {
        var urlParams = new URLSearchParams(window.location.search);
        this.id = decodeURI(urlParams.has('id') ? urlParams.get('id') : '');
        this.get_recipe();
    },
});

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


