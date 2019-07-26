// script.js

'use strict';

// JQuery

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var upload_file_url = $("input[name=upload_file_url]").val();
var get_uploaded_files_url = $("input[name=get_uploaded_files_url]").val();

var previewNode = document.querySelector("#template");
previewNode.id = "";
var previewTemplate = previewNode.parentNode.innerHTML;
previewNode.parentNode.removeChild(previewNode);
var ingest_zip_total = 0;
var ingest_zip_dropzone = 0;
var ingest_zip_bewaar = 0;
var ingest_zip_cnt = 0;

Dropzone.autoDiscover = false;
var myDropzone = new Dropzone(document.body, {
    url: upload_file_url,
    thumbnailWidth: 80,
    thumbnailHeight: 80,
    parallelUploads: 20,
    previewTemplate: previewTemplate,
    autoQueue: false,
    previewsContainer: "#previews",
    clickable: ".fileinput-button",
    params: { 'csrfmiddlewaretoken' : csrftoken },
    headers: { 'X-CSRF-Token': csrftoken },
    acceptedFiles: ".zip,.docx",
    maxFilesize: 500, // MB
    timeout: 0
});

myDropzone.on('success', function () {
    var args = Array.prototype.slice.call(arguments);
    app.get_uploaded_files();
});

myDropzone.on("addedfile", function (file) {
    ingest_zip_dropzone++;
    file.previewElement.querySelector(".start").onclick = function () {
        myDropzone.enqueueFile(file);
    };
});

myDropzone.on("removedfile", function (file) {
    ingest_zip_dropzone--;
});

myDropzone.on("totaluploadprogress", function (progress) {
    //document.querySelector("#total-progress .progress-bar").style.width = progress + "%";
});

myDropzone.on("sending", function (file) {
    console.log(file);
    //document.querySelector("#total-progress").style.opacity = "1";
    file.previewElement.querySelector(".start").setAttribute("disabled", "disabled");
});

myDropzone.on("queuecomplete", function (progress) {
    //document.querySelector("#total-progress").style.opacity = "0";
    app.get_uploaded_files();
});

myDropzone.on("complete", function (file) {
    myDropzone.removeFile(file);
    app.get_uploaded_files();
});

document.querySelector("#actions .start").onclick = function () {
    myDropzone.enqueueFiles(myDropzone.getFilesWithStatus(Dropzone.ADDED));
    ingest_zip_total = ingest_zip_dropzone;
    ingest_zip_cnt = 0;
};

document.querySelector("#actions .cancel").onclick = function () {
    myDropzone.removeAllFiles(true);
    ingest_zip_dropzone = 0;
    ingest_zip_total = 0;
    app.get_uploaded_files();
};

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

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        pager: { page_nr: 1, nr_hits: 0, page_size: 25, nr_pages: 0, page_nrs: [], nr_pages_nrs: 5 },
        hits: [],
        current_recipe: '',
        current_recipeIX: null,
    },
    methods: {
        get_uploaded_files: function (uploaded_file_id = null) {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie}
            this.$http.post(get_uploaded_files_url, {
                'csrfmiddlewaretoken': csrftoken,
                'pager': this.pager,
                },
                { 'headers': headers }).then(response => {
                //this.hits = JSON.parse(response.bodyText);
                this.pager = response.body.pager;
                if ('hits' in response.body.hits) {
                    this.hits = response.body.hits.hits;
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
        recipe_url(url, id) {
            return url + '?id=' + id;
        },
    },
    computed: {
    },
    mounted: function () {
        this.get_uploaded_files();
    },

});

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


