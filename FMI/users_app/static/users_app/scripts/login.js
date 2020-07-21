// script.js

'use strict';

var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var unlock_url = $("input[name=unlock_url]").val();
var login_url = $("input[name=login_url]").val();
var logout_url = $("input[name=logout_url]").val();
var register_url = $("input[name=register_url]").val();
var profile_url = $("input[name=profile_url]").val();

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function unlock_click() {
    var login_form = document.getElementById('login_form');
    if (login_form.checkValidity()) {
        var username_input = document.getElementById('username_input');
        var url = unlock_url;
        //url = url + "?username=" + username_input.value;
        //document.location.href = url;
        var csrftoken_cookie = getCookie('csrftoken');
        var headers = { 'X-CSRFToken': csrftoken_cookie }
        var xhr = new XMLHttpRequest();
        xhr.open('POST', unlock_url, true);
        xhr.setRequestHeader('X-CSRFToken', csrftoken_cookie);
        var body = 'csrfmiddlewaretoken=' + csrftoken + '&username=' + username_input.value;
        var formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrftoken);
        formData.append('username', username_input.value);
        xhr.send(formData);
        document.getElementById("login_message_div").innerHTML = "Mail send to reset password!";
    } else {
        // Create the temporary button, click and remove it
        var tmpSubmit = document.createElement('button')
        login_form.appendChild(tmpSubmit)
        tmpSubmit.click()
        login_form.removeChild(tmpSubmit)
    }
}

var app = new Vue({
    el: '#login-modal-root',
    delimiters: ['[[', ']]'],
    data: {
        username: "",
        password: "",
        is_authenticated: false,
    },
    methods: {
        post_login: function () {
            var login_modal_div = document.getElementById('login-modal');
            this.username = document.getElementById('username_input').value;
            this.password = document.getElementById('password_input').value;
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            this.$http.post(login_url, {
                'csrfmiddlewaretoken': csrftoken,
                'username': this.username,
                'password': this.password,
            },
                { 'headers': headers }).then(response => {
                    this.is_authenticated = response.body.is_authenticated;
                    var next = response.body.next;
                    if (this.is_authenticated) {
                        login_modal_div.classList.remove("show");
                        window.location.reload(true);
                    } else {
                        var login_message_div = document.getElementById('login_message_div');
                        login_message_div.innerHTML = "Login mislukt";
                    }
                });
        },
        post_logout: function () {
            var login_modal_div = document.getElementById('login-modal');
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            this.$http.post(logout_url, {
                'csrfmiddlewaretoken': csrftoken,
            },
                { 'headers': headers }).then(response => {
                    this.is_authenticated = response.body.is_authenticated;
                    var next = response.body.next;
                    if (!this.login) {
                        login_modal_div.classList.remove("show");
                        window.location.reload(true);
                    }
                });
        },
    },
    computed: {
    },
    mounted: function () {
        this.is_authenticated = user.is_authenticated;

    },
});