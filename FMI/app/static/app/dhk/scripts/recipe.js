// script.js

'use strict';

// JQuery

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var upload_file_url = $("input[name=upload_file_url]").val();
var get_uploaded_files_url = $("input[name=get_uploaded_files_url]").val();

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


