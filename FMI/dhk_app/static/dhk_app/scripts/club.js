// script.js

'use strict';

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var get_recipe_url = $("input[name=get_recipe_url]").val();
var post_recipe_url = $("input[name=post_recipe_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        filter_facets: {
            rel_id_path: [],
            dekking_date: { start: null, end: null },
            typevergadering: []
        },
        sort_facets: {},
        query_facets: {
            query_spreker: null,
            query_agenda: null,
            query_string: null,
        },
        webcasts: null,
        recipe: null,
        calendar: null,
        calendar_header: {
            left: 'prevYear, nextYear',
            center: 'title',
            right: 'today prev,next'
        },
        hits: [],
        aggs: {},
    },
    methods: {
    },
    computed: {
    },
    mounted: function () {
        var today = new Date();
        var startdt = today;
        startdt = startdt.setMonth(today.getMonth() - 3);

        var calendarEl = document.getElementById('calendar');
        this.calendar = new FullCalendar.Calendar(calendarEl, {
            locale: 'nl',
            plugins: ['dayGrid'],
            header: this.calendar_header,
            defaultDate: "2019-09-01",
            eventClick: function (info) {
                var identificatiekenmerk = info.event.id;
                app.fetch_webcast_edepot(identificatiekenmerk);
                info.el.style.borderColor = 'red';
            }
        });
        this.calendar.render();
    },
});

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


