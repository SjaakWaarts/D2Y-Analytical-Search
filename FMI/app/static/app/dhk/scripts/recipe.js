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

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        upper_aggregatieniveaus: ['archief', 'serie', 'dossier', 'archiefstuk'],
        checked_aggregatieniveaus: ['archief', 'serie', 'dossier', 'archiefstuk'],
        iframe_src: null,
        ziplist: [],
        currentZip: '',
        currentZipIX: null,
        structure: null,
        currentXml: null,
        bestandformaat: null,
        currentAggr: null,
        searchLinkablesInput: null,
        relatie_hits: null,
        current_relatie_hit: null,
        relaties_pager: { page_nr: 1, nr_hits: 0, page_size: 5, nr_pages: 0, page_nrs: [], nr_pages_nrs: 5 }
    },
    methods: {
        get_uploaded_files: function (uploaded_file_id = null) {
            this.$http.get(get_uploaded_files_url).then(response => {
                //this.ziplist = JSON.parse(response.bodyText);
                this.ziplist = response.body;
                if (uploaded_file_id) {
                    for (ix = 0; ix < this.ziplist.length; ix++) {
                        if (this.ziplist[ix]['id'] === uploaded_file_id) {
                            this.currentZip = this.ziplist[ix];
                            this.structure = this.currentZip.aggrs;
                        }
                    }
                }
            });
        },
        indexZipList: function () {
            var raise_alert = true;
            var ingest_zip_bewaar = 0;
            for (var ix = 0; ix < this.ziplist.length; ix++) {
                zip = this.ziplist[ix]
                if (zip['approved'] === true) {
                    ingest_zip_bewaar++;
                    for (jx = 0; jx < zip['aggrs'].length; jx++) {
                        aggr = zip['aggrs'][jx];
                        if (aggr['approved'] == true) {
                            raise_alert = false;
                        }
                    }
                }
            }
            if (raise_alert) {
                alert("Nog geen zip bestand en/of dossier goedgekeurd!");
                index_zip_bewaar = 0;
                return;
            }
            ingest_zip_total = ingest_zip_bewaar;
            ingest_zip_cnt = 0;
            display_progress_header();
            var textarea = document.getElementById("ingest_progress_textarea");
            textarea.value = "Bewaar gestart\n";
            poll_queue();
            var bewaar_opnamen_btn = document.getElementById("bewaar_opnamen_btn");
            bewaar_opnamen_btn.disabled = true;
            this.$http.post(index_zips_url, { ziplist: this.ziplist }).then(response => {
                bewaar_opnamen_btn.disabled = false;
                if (response.body['status'] === true) {
                    this.getZipList();
                }
                alert(response.body['msg'])
            })
        }
    },
    computed: {
        statusList() {
            return this.currentAggr ? this.currentAggr.status : this.currentZip ? this.currentZip.status : [];
        }
    },
    mounted: function () {
        this.get_uploaded_files();
    },

});

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


