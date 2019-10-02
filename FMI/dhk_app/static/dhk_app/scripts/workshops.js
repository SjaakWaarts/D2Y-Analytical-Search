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
        average_rating: 0,
        carousel_images: null,
        workshop_participant: {
            'user': "",
            'email': "",
            'comment': ""
        },
        hits: [],
        id: '',
        leave_review: {
            'name': "",
            'email': "",
            'website': "",
            'stars': 0
        },
        recipe: null,
        shopping_basket: [],
        workshop: null,
    },
    methods: {
        bind_stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
        club_participant_update_click: function (index) {
            this.workshop_participant.user = this.workshop.participants[index].user;
            this.workshop_participant.email = this.workshop.participants[index].email;
            this.workshop_participant.comment = this.workshop.participants[index].comment;
            var textarea_tag = document.getElementById("participant_textarea");
            textarea_tag.value = this.workshop_participant.comment;
            var button_tag = document.getElementById("participate_button");
            button_tag.innerHTML = "UPDATE AANMELDING";
            button_tag.value = "update-" + index;
        },
        club_participant_delete_click: function (workshop_ix, index) {
            this.workshop.participants.splice(index, 1);
            this.workshop_participant.user = "";
            this.workshop_participant.email = "";
            this.workshop_participant.comment = "";
            var textarea_tag = document.getElementById("participant_textarea");
            textarea_tag.value = this.workshop_participant.comment;
            var button_tag = document.getElementById("participate_button");
            button_tag.innerHTML = "AANMELDEN ETENTJE";
            button_tag.value = "new";
            //this.post_recipe();
        },
        post_workshop_participant_click: function () {
            var participant = {};
            var textarea_tag = document.getElementById("participant_textarea");
            this.workshop_participant.comment = textarea_tag.value;
            participant.user = this.workshop_participant.user;
            participant.email = this.workshop_participant.email;
            participant.comment = this.workshop_participant.comment;
            var button_tag = document.getElementById("participate_button");
            if (button_tag.value == "new") {
                var found = false;
                for (var ix = 0; ix < this.workshop.participants.length; ix++) {
                    if (participant.user == this.workshop.participants[ix].user ||
                        participant.email == this.workshop.participants[ix].email) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    this.workshop.participants.push(participant);
                }
            } else {
                var index = parseInt(button_tag.value.split('-')[1]);
                this.workshop.participants[index] = participant;
            }
            //this.post_recipe();
        },
        workshop_click(workshop_ix) {
            this.workshop = workshops[workshop_ix];
        },
    },
    computed: {
    },
    mounted: function () {
        this.workshop = workshops[0];
        this.carousel_images = [];
        for (var w_ix = 0; w_ix < workshops.length; w_ix++) {
            for (var i_ix = 0; i_ix < workshops[w_ix].images.length; i_ix++) {
                this.carousel_images.push(workshops[w_ix].images[i_ix]);
            }
        }
        var urlParams = new URLSearchParams(window.location.search);
        this.id = decodeURI(urlParams.has('id') ? urlParams.get('id') : '');
        if (user.username != "") {
            this.workshop_participant.user = user.username;
            this.workshop_participant.email = user.email;
            this.leave_review.name = user.username;
            this.leave_review.email = user.email;
        }
    },
});



