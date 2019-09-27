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

function login_navbar_click() {
    var login_model_div = document.getElementById('login-modal');
    $('#login-modal').modal('show');
}

function login_request_ready(xhr) {
    document.getElementById("login_message_div").innerHTML = xhr.responseText;
}

function login_click() {
    var login_form = document.getElementById('login_form');
    var username_input = document.getElementById('username_input');
    var password_input = document.getElementById('password_input');
    var url = login_url;
    var csrftoken_cookie = getCookie('csrftoken');
    var headers = { 'X-CSRFToken': csrftoken_cookie }
    var xhr = new XMLHttpRequest();
    //xhr.onreadystatechange = function () {
    //    if (this.readyState == 4 && this.status == 200) {
    //        login_request_ready(this);
    //    }
    //};
    xhr.open('POST', login_url, true);
    xhr.setRequestHeader('X-CSRFToken', csrftoken_cookie);
    var body = 'csrfmiddlewaretoken=' + csrftoken + '&username=' + username_input.value;
    var formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrftoken);
    formData.append('username', username_input.value);
    formData.append('password', password_input.value);
    xhr.send(formData);
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