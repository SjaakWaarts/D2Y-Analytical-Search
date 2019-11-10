/* Facet components for Beheer and such */

Vue.component('facet-filter', {
    data: function () {
        return {}
    },
    props: {
        facet_name : String,
        workbook : Object
    },
    computed: {
        facet: function () {
            var f = this.workbook.facets[this.facet_name];
            if (!('multiple' in f)) {
                f['multiple'] = true;
}            if (!('size' in f)) {
                f['size'] = "8";
            }
            return this.workbook.facets[this.facet_name];
        }
    },
    methods: {
        process_check: function () {
            this.$emit('update:workbook', this.workbook);
            this.$emit('facet-filter');
        }
    },
    template:
        `<div class="facet-filter">
            <div v-if="facet.type == 'terms'">
                <div class="box filter-box" v-if="facet.buckets">
                    <label v-if="facet.label" v-bind:for="this.facet_name + '-select'">{{facet.label}}</label>
                    <select v-bind:name="'facet-' + this.facet_name" v-model="facet.value" v-bind:size="facet.size" style="height:auto"
                            class="form-control facet-select" v-bind:multiple="facet.multiple" v-bind:id="this.facet_name + '-select'"
                            v-on:change="process_check()">
                        <option v-for="bucket in facet.buckets"
                                v-bind:value="bucket.key"
                                v-bind:class="{selected : (facet.multiple ? bucket.key in facet.value : bucket.key == facet.value)}">
                            {{bucket.key}} ({{bucket.doc_count}})
                        </option>
                    </select>
                </div>
            </div>
            <div v-if="facet.type == 'text'">
                <div class="input-group">
                    <input v-model="facet.value" type="text" placeholder="Zoek">
                    <div class="input-group-append">
                        <span class="input-group-text" v-on:click="process_check()">Zoek</span>
                    </div>
                </div>
            </div>
            <div v-if="facet.type == 'date'">
                <input v-model="facet.value" type="date" v-on:change="process_check()">
            </div>
            <div v-if="facet.type == 'period'" class="box">
                <div class="table-responsive">
                    <table class="table">
                        <tbody>
                            <tr>
                                <td>Start</td>
                                <td><input class="form-control" v-model="facet.value.start" type="date" v-on:change="process_check()"></td>
                            </tr>
                            <tr>
                                <td>Eind</td>
                                <td><input class="form-control" v-model="facet.value.end" type="date" v-on:change="process_check()"></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>`
});