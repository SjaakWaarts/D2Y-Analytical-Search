
Vue.component('pager', {
    data: function () {
        return {}
    },
    props: {
        pager: Object
    },
    computed: {
        //nr_pages: function () { return Math.ceil(this.nr_hits / this.page_size) }
        page_nrs: function () {
            this.pager.nr_pages = Math.ceil(this.pager.nr_hits / this.pager.page_size);
            if (this.pager.nr_pages > this.pager.nr_pages_nrs) {
                page_nr_high = this.pager.page_nr + Math.floor(this.pager.nr_pages_nrs / 2);
                page_nr_low = this.pager.page_nr - Math.floor(this.pager.nr_pages_nrs / 2);
                if (page_nr_high > this.pager.nr_pages) {
                    page_nr_low = page_nr_low - (page_nr_high - this.pager.nr_pages);
                    page_nr_high = this.pager.nr_pages
                }
                if (page_nr_low < 1) {
                    page_nr_high = page_nr_high + (1 - page_nr_low);
                    page_nr_low = 1
                }
            } else {
                page_nr_high = this.pager.nr_pages;
                page_nr_low = 1;
            }
            this.pager.page_nrs = [];
            if (page_nr_low > 1) {
                this.pager.page_nrs.push(1)
            }
            for (page_nr = page_nr_low; page_nr <= page_nr_high; page_nr++) {
                this.pager.page_nrs.push(page_nr)
            }
            if (page_nr_high < this.pager.nr_pages) {
                this.pager.page_nrs.push(this.pager.nr_pages)
            }
            return this.pager.page_nrs;
        }
    },
    methods: {
        process_check: function (page_nr) {
            this.pager.page_nr = page_nr;
            this.$emit('update:pager', this.pager)
            this.$emit('pager')
        }
    },
    template:
        `<div class="pager">
            <ul v-if="pager.nr_pages>0" class="pagination">
                <div v-if="pager.nr_pages==0">
                    <li><a href="#" class="page-link" data-page="1">1 &hellip;</a></li>
                </div>
                <li v-for="(p, index) in page_nrs" v-bind:class="{active : p==pager.page_nr}">
                    <a href="#" v-on:click="process_check(p)" class="page-link" data-page="[[ p ]]">
                        <span v-if="index==1 && p!=2"> &hellip;</span>
                        {{ p }}
                        <span v-if="index==pager.nr_pages_nrs && p!=pager.nr_pages-1"> &hellip;</span>
                    </a>
                </li>
            </ul>
        </div>`
});


Vue.component('namen', {
    data: function () {
        return {}
    },
    props: {
        namen: String
    },
    template:
        `<div class="namen">
            <span v-for="naam in namen">
                {{ naam }}
            </span>
        </div>`
});

Vue.component('approved-checkbox', {
    data: function () {
        return {}
    },
    props: {
        latest_status: Number,
        approved: Boolean
    },
    template:
        `<div class="latest-status">
	    <span v-if="latest_status < 200">
		    <i class="fa fa-hourglass divault-busy" title="Bezig"></i>
	    </span>
		    <span v-if="latest_status >= 200 && latest_status < 300">
		    <i class="fa fa-check divault-done" title="Klaar"></i>
	    </span>
		    <span v-if="latest_status >= 300">
		    <i class="fa fa-times divault-error" title="Fout"></i>
	    </span>
        </div>`
});

Vue.component('latest-status-mark', {
    data: function () {
        return {}
    },
    props: {
        latest_status: Number
    },
    template:
        `<div class="latest-status">
	    <span v-if="latest_status < 200">
		    <i class="fa fa-hourglass divault-busy" title="Bezig"></i>
	    </span>
		    <span v-if="latest_status >= 200 && latest_status < 300">
		    <i class="fa fa-check divault-done" title="Klaar"></i>
	    </span>
		    <span v-if="latest_status >= 300">
		    <i class="fa fa-times divault-error" title="Fout"></i>
	    </span>
        </div>`
});


Vue.component('aggr-icon', {
    data: function () {
        return {}
    },
    props: {
        aggregatieniveau: String,
        identificatiekenmerk: String
    },
    template:
        `<div class="aggr-icon">
            <div v-if="aggregatieniveau=='archief'" class= "archief" >
                <i class="fas fa-archive" v-bind:title="aggregatieniveau"></i>
            </div>
            <div v-if="aggregatieniveau=='serie'" class="serie">
                <i class="far fa-file-archive" v-bind:title="aggregatieniveau"></i>
            </div>
            <div v-if="aggregatieniveau=='dossier'" class="dossier">
                <i class="far fa-folder" v-bind:title="aggregatieniveau"></i>
            </div>
            <div v-if="aggregatieniveau=='archiefstuk'" class="archiefstuk">
                <i class="fas fa-file" v-bind:title="aggregatieniveau"></i>
            </div>
            <div v-if="aggregatieniveau=='content'" class="file">
                <i class="far fa-file" v-bind:title="aggregatieniveau"></i>
            </div>
        </div>`
});

Vue.component('aggr-select', {
    data: function () {
        return {
            //comp_checked_aggregatieniveaus: this.checked_aggregatieniveaus
            //comp_checked_aggregatieniveaus: Vue.util.extend({}, this.checked_aggregatieniveaus)
            // make a copy instead of a refernce !!
            comp_checked_aggregatieniveaus: []
        }
    },
    props: {
        upper_aggregatieniveaus: Array,
        checked_aggregatieniveaus: Array
    },
    computed: {
        //comp_checked_aggregatieniveaus: function () {
        //    return this.checked_aggregatieniveaus
        //},
        get_checked_aggregatieniveaus() {
            return this.checked_aggregatieniveaus;
        }
    },
    //created: function () {
    //    for (ix = 0; ix < this.checked_aggregatieniveaus.length; ix++) {
    //        this.comp_checked_aggregatieniveaus.push(this.checked_aggregatieniveaus[ix]);
    //    }
    //},
    methods: {
        process_check: function () {
            this.$emit('update:checked_aggregatieniveaus', this.checked_aggregatieniveaus)
        }
    },
    template:
        `<div class="aggr-select">
            <div class="input-group">
                <label class="checkbox-inline" v-if="upper_aggregatieniveaus.includes('archief')">
                    <input type="checkbox" id="archief_check" value="archief" v-model="checked_aggregatieniveaus"
                        v-on:change="process_check()">Archief
                </label>
                <label class="checkbox-inline" v-if="upper_aggregatieniveaus.includes('serie')">
                    <input type="checkbox" id="serie_check" value="serie" v-model="checked_aggregatieniveaus""
                        v-on:change="process_check()">Serie
                </label>
                <label class="checkbox-inline" v-if="upper_aggregatieniveaus.includes('dossier')">
                    <input type="checkbox" id="dossier_check" value="dossier" v-model="checked_aggregatieniveaus"
                        v-on:change="process_check()">Dossier
                </label>
                <label class="checkbox-inline" v-if="upper_aggregatieniveaus.includes('archiefstuk')">
                    <input type="checkbox" id="archiefstuk_check" value="archiefstuk" v-model="checked_aggregatieniveaus"
                        v-on:change="process_check()">Archiefstuk
                </label>
            </div>
        </div>`
});

Vue.component('pager', {
    data: function () {
        return {}
    },
    props: {
        pager: Object
    },
    computed: {
        //nr_pages: function () { return Math.ceil(this.nr_hits / this.page_size) }
        page_nrs: function () {
            this.pager.nr_pages = Math.ceil(this.pager.nr_hits / this.pager.page_size);
            if (this.pager.nr_pages > this.pager.nr_pages_nrs) {
                page_nr_high = this.pager.page_nr + Math.floor(this.pager.nr_pages_nrs / 2);
                page_nr_low = this.pager.page_nr - Math.floor(this.pager.nr_pages_nrs / 2);
                if (page_nr_high > this.pager.nr_pages) {
                    page_nr_low = page_nr_low - (page_nr_high - this.pager.nr_pages);
                    page_nr_high = this.pager.nr_pages
                }
                if (page_nr_low < 1) {
                    page_nr_high = page_nr_high + (1 - page_nr_low);
                    page_nr_low = 1
                }
            } else {
                page_nr_high = this.pager.nr_pages;
                page_nr_low = 1;
            }
            this.pager.page_nrs = [];
            if (page_nr_low > 1) {
                this.pager.page_nrs.push(1)
            }
            for (page_nr = page_nr_low; page_nr <= page_nr_high; page_nr++) {
                this.pager.page_nrs.push(page_nr)
            }
            if (page_nr_high < this.pager.nr_pages) {
                this.pager.page_nrs.push(this.pager.nr_pages)
            }
            return this.pager.page_nrs;
        }
    },
    methods: {
        process_check: function (page_nr) {
            this.pager.page_nr = page_nr;
            this.$emit('update:pager', this.pager)
            this.$emit('pager')
        }
    },
    template:
        `<div class="pager">
            <ul v-if="pager.nr_pages>0" class="pagination">
                <div v-if="pager.nr_pages==0">
                    <li><a href="#" class="page-link" data-page="1">1 &hellip;</a></li>
                </div>
                <li v-for="(p, index) in page_nrs" v-bind:class="{active : p==pager.page_nr}">
                    <a href="#" v-on:click="process_check(p)" class="page-link" data-page="[[ p ]]">
                        <span v-if="index==1 && p!=2"> &hellip;</span>
                        {{ p }}
                        <span v-if="index==pager.nr_pages_nrs && p!=pager.nr_pages-1"> &hellip;</span>
                    </a>
                </li>
            </ul>
        </div>`
});

Vue.component('rating', {
    data: function () {
        return {}
    },
    props: {
        stars: Number,
        rate: Boolean
    },
    computed: {
    },
    methods: {
        rate_click: function (event) {
            var i_tag = event.target;
            var rate_item_tag = i_tag.parentElement;
            var rate_tag = rate_item_tag.parentElement;
            rate_tag.classList.add('selected');
            var active_rate_item_tag = rate_tag.querySelectorAll('.active');
            if (active_rate_item_tag.length > 0) {
                active_rate_item_tag[0].classList.remove('active');
            }
            rate_item_tag.classList.add('active');
            this.stars = Number(rate_item_tag.id.slice(-1));
            this.$emit('update:stars', this.stars)
            this.$emit('rating')
        },
    },
    template:
        `<div class="rating">
        <ul v-if="rate == false" class="item-rating p-0">
            <li v-bind:class="{'single-item':true, 'star-fill':n<=stars, 'star-empty':n>stars}"
                v-for="n in 5" :key="n">
                <i class="fas fa-star"></i>
            </li>
            <li class="single-item"><span>{{stars}} / 5</span> </li>
        </ul>
        <div v-else id="comment_rate" class="rate" v-on:click="rate_click(event)">
            <div id="rating_1" class="rate-item"><i class="fa fa-star" aria-hidden="true"></i></div>
            <div id="rating_2" class="rate-item"><i class="fa fa-star" aria-hidden="true"></i></div>
            <div id="rating_3" class="rate-item"><i class="fa fa-star" aria-hidden="true"></i></div>
            <div id="rating_4" class="rate-item"><i class="fa fa-star" aria-hidden="true"></i></div>
            <div id="rating_5" class="rate-item"><i class="fa fa-star" aria-hidden="true"></i></div>
        </div>
    </div>`
});