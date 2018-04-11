// script.js

'use strict';

// var accord_piechart = dc.pieChart('#accord_chart');
// var perfumes_table = dc.dataTable("#perfumes_table", 'dashboard_accords');
var accords_barchart = dc.barChart('#accords_chart', 'dashboard_accords');
var perfaccord_piechart = dc.pieChart('#perfaccord_chart', 'dashboard_accords');
var votes_barchart = dc.barChart('#votes_chart', 'dashboard_votes');
var perfvote_piechart = dc.pieChart('#perfvote_chart', 'dashboard_votes');
var notes_barchart = dc.barChart('#notes_chart', 'dashboard_notes');
var perfnote_piechart = dc.pieChart('#perfnote_chart', 'dashboard_notes');
var sentiment_linechart = dc.lineChart('#sentiment_chart', 'dashboard_sentiment');
var perfumes = {};
var accords_ndx = crossfilter();
var votes_ndx = crossfilter();
var notes_ndx = crossfilter();
var sentiment_ndx = crossfilter();
var accords_perfume_dim, notes_perfume_dim, votes_perfume_dim, sentiment_perfume_dim;

function on_renderlet_transform_y_labels(chart) {
    // rotate x-axis labels
    chart.selectAll('g.x text')
        .attr('transform', 'translate(-10,10) rotate(315)')
}

function fakedim_top_x(source_group, x) {
    return {
        all: function () {
            return source_group.top(x);
        }
    };
}

function remove_empty_bins(source_group) {
    return {
        all: function () {
            return source_group.all().filter(function (d) {
                return d.value != 0;
            });
        }
    };
}


var dashboard_accords = function (data) {
    accords_ndx = crossfilter(data);
    accords_perfume_dim = accords_ndx.dimension(function (d) { return d.perfume; });
    var accord_dim = accords_ndx.dimension(function (d) { return d.accord; });
    var rank_dim = accords_ndx.dimension(function (d) { return d.rank; });
    var perfume_dim_group = accords_perfume_dim.group().reduce(
        //add
        function (p, v) {
            p.count++;
            p.sum += v.strength;
            p.avg = p.sum / p.count;
            return p;
        },
        //remove
        function (p, v) {
            p.count--;
            p.sum -= v.strength;
            p.avg = (p.count == 0) ? 0 : p.sum / p.count;
            return p;
        },
        //init
        function () {
            return { count: 0, sum: 0, avg: 0 }
        });
//    perfume_dim.filter(function (p) { p.count; });
    var perfume_dim_group_empty = remove_empty_bins(perfume_dim_group)
    var nrperf_accord = accord_dim.group().reduceCount();
    var nraccord_perfume = accords_perfume_dim.group().reduceCount();
    var strengthaccord_perfume = accords_perfume_dim.group().reduceSum(function (d) { return +d.strength })
    var nraccord_perfume_empty = remove_empty_bins(nraccord_perfume);

    //accord_piechart
    //    .height(200)
    //    .width(400)
    //    .dimension(accord_dim)
    //    .group(nrperf_accord)
    //    .innerRadius(10)
    //    .renderLabel(false)
    //    .legend(dc.legend().x(210).y(10).itemHeight(13).gap(5))
    //;
    //accord_piechart.cx(100);
    //accord_piechart.cy(100);

    //perfume_barchart
    //    .height(300)
    //    .width(600)
    //    .margins({ top: 10, right: 10, bottom: 150, left: 50 })
    //    .dimension(accords_perfume_dim)
    //    .group(nraccord_perfume_empty)
    //    .x(d3.scale.ordinal())
    //    .xUnits(dc.units.ordinal)
    //    .elasticX(true)
    //    .xAxisLabel('Perfume')
    //    .yAxisLabel('Nr Accord')
    //    .brushOn(true)
    //    .elasticY(true)
    //    .on("renderlet", on_renderlet_transform_y_labels)
    //;


    accords_barchart
        .height(200)
        .width(600)
        .margins({ top: 10, right: 10, bottom: 50, left: 50 })
        .dimension(accord_dim)
        .group(nrperf_accord)
        .x(d3.scale.ordinal())
        .xUnits(dc.units.ordinal)
        .elasticX(true)
        .xAxisLabel('Accord')
        .yAxisLabel('Nr Perfumes')
        .elasticY(true)
        .on("renderlet", on_renderlet_transform_y_labels)
        //.on("filtered",
        //    function (chart) {
        //        dc.events.trigger(function () {
        //            var filter = chart.filter();
        //            perfumes_table.filter(filter);
        //        });
        //    })
    ;

    var max_nraccord_perfume = nraccord_perfume.top(1)[0].count;
    perfaccord_piechart
        .height(200)
        .width(600)
        .dimension(accords_perfume_dim)
        .group(strengthaccord_perfume)
        .slicesCap(20)
        .innerRadius(10)
        .renderLabel(true)
//        .legend(dc.legend().x(310).y(10).itemHeight(13).gap(5))
    ;
    perfaccord_piechart.cx(150);
    perfaccord_piechart.cy(100);

    //perfumes_table
    //    .dimension(perfume_dim_group)
    //    .order(d3.descending)
    //    .group(function (p) { return "perfume" })
    //    .showGroups(false)
    //    .keyAccessor(function (p) {
    //        return p.key;
    //    })
    //    .valueAccessor(function (p) {
    //        return p.value.count;
    //    })
    //    .size(Infinity)
    //    .columns([
    //        function (p) { return p.key },
    //        function (p) { return p.value.count }])
    //;

    //perfumes_table
    //    .dimension(accords_perfume_dim)
    //    .order(d3.descending)
    //    .group(function (p) { return "perfume" })
    //    .showGroups(false)
    //    .keyAccessor(function (d) {
    //        return d.key;
    //    })
    //    .valueAccessor(function (d) {
    //        return d.value;
    //    })
    //    .size(Infinity)
    //    .columns([
    //        function (d) { return d.perfume },
    //        function (d) { return d.strength }])
    //;

};


var dashboard_votes = function (data) {
    votes_ndx = crossfilter(data);
    votes_perfume_dim = votes_ndx.dimension(function (d) { return d.perfume; });
    var vote_dim = votes_ndx.dimension(function (d) { return d.vote; });
    var nrperf_vote = vote_dim.group().reduceCount();
    var strength_vote = vote_dim.group().reduceSum(function (d) { return +d.strength })
    var nrvote_perfume = votes_perfume_dim.group().reduceCount();
    var strengthvote_perfume = votes_perfume_dim.group().reduceSum(function (d) { return +d.strength })
    var nrvote_perfume_empty = remove_empty_bins(nrvote_perfume);

    votes_barchart
        .height(200)
        .width(600)
        .margins({ top: 10, right: 10, bottom: 50, left: 50 })
        .dimension(vote_dim)
        .group(strength_vote)
        .x(d3.scale.ordinal())
        .xUnits(dc.units.ordinal)
        .elasticX(true)
        .xAxisLabel('Vote')
        .yAxisLabel('Strength')
        .elasticY(true)
        .on("renderlet", on_renderlet_transform_y_labels)
    ;

    perfvote_piechart
        .height(200)
        .width(600)
        .dimension(votes_perfume_dim)
        .group(strengthvote_perfume)
        .slicesCap(20)
        .innerRadius(10)
        .renderLabel(true)
    //        .legend(dc.legend().x(310).y(10).itemHeight(13).gap(5))
    ;
    perfvote_piechart.cx(150);
    perfvote_piechart.cy(100);

};

var dashboard_notes = function (data) {
    notes_ndx = crossfilter(data);
    notes_perfume_dim = notes_ndx.dimension(function (d) { return d.perfume; });
    var note_dim = notes_ndx.dimension(function (d) { return d.note; });
    var nrperf_note = note_dim.group().reduceCount();
    var strength_note = note_dim.group().reduceSum(function (d) { return +d.strength })
    var strength_note_empty = remove_empty_bins(strength_note);
    var nrnote_perfume = notes_perfume_dim.group().reduceCount();
    var strengthnote_perfume = notes_perfume_dim.group().reduceSum(function (d) { return +d.strength })
    var nrnote_perfume_empty = remove_empty_bins(nrnote_perfume);

    notes_barchart
        .height(200)
        .width(600)
        .margins({ top: 10, right: 10, bottom: 50, left: 50 })
        .dimension(note_dim)
//      .group(nrperf_note)
        .group(strength_note_empty)
        .x(d3.scale.ordinal())
        .xUnits(dc.units.ordinal)
        .elasticX(true)
        .xAxisLabel('Note')
        .yAxisLabel('Nr Votes')
        .elasticY(true)
        .on("renderlet", on_renderlet_transform_y_labels)
    ;

    var max_nrnote_perfume = nrnote_perfume.top(1)[0].count;
    perfnote_piechart
        .height(200)
        .width(600)
        .dimension(notes_perfume_dim)
        .group(strengthnote_perfume)
        .slicesCap(20)
        .innerRadius(10)
        .renderLabel(true)
    //        .legend(dc.legend().x(310).y(10).itemHeight(13).gap(5))
    ;
    perfnote_piechart.cx(150);
    perfnote_piechart.cy(100);

};

var dashboard_sentiment = function (data) {
    var dateFormat = d3.time.format('%Y/%m/%d');
    data.forEach(function (d) {
        var dt1 = new Date(d.date);
        var month = dt1.getFullYear() + "/" + (dt1.getMonth() + 1);
        var dt2 = dateFormat.parse(d.date);
        d.month = d3.time.month(dt2);
        d.date = dt2;
    });
    sentiment_ndx = crossfilter(data);
    sentiment_perfume_dim = sentiment_ndx.dimension(function (d) { return d.perfume; });
    var date_dim = sentiment_ndx.dimension(function (d) { return d.date; });
    var month_dim = sentiment_ndx.dimension(function (d) { return d.month; });
    var label_dim = sentiment_ndx.dimension(function (d) { return d.label; });
    var nrreview_perf = sentiment_perfume_dim.group().reduceCount();
    var nrreview_date = date_dim.group().reduceCount();
    var nrreview_month = month_dim.group().reduceCount();
    var nrreview_label = label_dim.group().reduceCount();
    var nrreview_month_pos = month_dim.group().reduce(
        //add
        function (p, v) { if (v.label == "pos") { p.count++; } return p; },
        //remove
        function (p, v) { if (v.label == "pos") { p.count--; } return p; },
        //init
        function () { return { count: 0 }
        });
    var nrreview_month_neg = month_dim.group().reduce(
        //add
        function (p, v) { if (v.label == "neg") { p.count++; } return p; },
        //remove
        function (p, v) { if (v.label == "neg") { p.count--; } return p; },
        //init
        function () { return { count: 0 }
        });
    var nrreview_month_neutral = month_dim.group().reduce(
        //add
        function (p, v) { if (v.label == "neutral") { p.count++; }; return p; },
        //remove
        function (p, v) { if (v.label == "neutral") { p.count--; }; return p; },
        //init
        function () { return { count: 0 }
        });
    var nrreview_month_init = month_dim.group().reduce(
        //add
        function (p, v) { if (v.label == "init") { p.count++; } return p; },
        //remove
        function (p, v) { if (v.label == "init") { p.count--; } return p; },
        //init
        function () { return { count: 0 }
        });
    sentiment_linechart
        .height(200)
        .width(1100)
        .margins({ top: 10, right: 10, bottom: 50, left: 50 })
        .dimension(month_dim)
        .group(nrreview_month_init, "init")
        .stack(nrreview_month_neutral, "neutral")
        .stack(nrreview_month_pos, "pos")
        .stack(nrreview_month_neg, "neg")
        .x(d3.time.scale())
        .xUnits(d3.time.months)
        .y(d3.scale.linear())
        .elasticX(true)
        .xAxisLabel('Time')
        .yAxisLabel('Nr Reviews')
        .elasticY(true)
        .keyAccessor(function (p) {
            var key = p.key.getFullYear() + "/" + p.key.getMonth();
            return p.key;
        })
        .valueAccessor(function (p) {
            return p.value.count;
        })
        .brushOn(false)
        .legend(dc.legend().x(70).y(10).itemHeight(13).gap(5))
        .mouseZoomable(true)
        .on("renderlet", on_renderlet_transform_y_labels)
    ;
};

d3.select('#version').text('v' + dc.version);


//d3.json('/api/scrape_accords', function (error, accords) {
//    if (error) {
//        console.log(error)
//    }
//    dashboard_accords(accords);
//    dc.renderAll('dashboard_accords');
//});

d3.json('/api/scrape_votes', function (error, votes) {
    if (error) {
        console.log(error)
    }

    dashboard_votes(votes);
    dc.renderAll('dashboard_votes');
});

d3.json('/api/scrape_notes', function (error, notes) {
    if (error) {
        console.log(error)
    }

    dashboard_notes(notes);
    dc.renderAll('dashboard_notes');
});


// JQuery

$.get("/api/scrape_reviews", function (data, status) {
    var perfume;
    var cb, cbd, cbl, cbo;

    dashboard_sentiment(data);
    dc.renderAll('dashboard_sentiment');
});

$(document).ready(function () {

    $("#perfumes_jquery").append("The JQuery generated Perfumes list");

//    $("#perfumes_jquery").click(function () {
//      $(this).hide();
//        $.get("/api/scrape_accords", function (data, status) { alert("Data: " + data + "\nStatus: " + status); });
//    });


    var $table = $("#perfreview_table").tablesorter({
        headers: {
            0: { sorter: true },
            1: { sorter: true },
            2: { sorter: false , filter: false },
            3: { sorter: true}
        },
        widgets: ["zebra", "filter"],
        widgetOptions: {
            // class name applied to filter row and each input
            filter_cssFilter: 'tablesorter-filter',
            // search from beginning
            filter_startsWith: true,
            // Set this option to false to make the searches case sensitive
            filter_ignoreCase: true,
            filter_reset: '.reset'
        },
    });
    $.tablesorter.filter.bindSearch($table, $('.search'));

    $.get("/api/scrape_accords", function (data, status) {
        var perfume;
        var cb, cbd, cbl, cbo;

        dashboard_accords(data);
        dc.renderAll('dashboard_accords');

        for (var i = 0; i < data.length; i++) {
            perfume = data[i].perfume
            perfumes[perfume] = 1
        }
        cb = document.getElementById("perfume_checkbox");
        for (perfume in perfumes) {
            cbd = document.createElement("div");
            cbd.setAttribute('class', 'checkbox');
            cbo = document.createElement("input");
            cbo.type = 'checkbox'
            cbo.name = 'perfume';
            cbo.value = perfume;
            cbo.onclick = function (event) {
                var perfume = event.target.value;
                var checked = event.target.checked;
                perfaccord_piechart.filter(perfume);
                perfaccord_piechart.redrawGroup();
                perfvote_piechart.filter(perfume);
                perfvote_piechart.redrawGroup();
                perfnote_piechart.filter(perfume);
                perfnote_piechart.redrawGroup();
                var perfume_filters = perfaccord_piechart.filters();
                if (perfume_filters.length > 0) {
                    sentiment_perfume_dim.filter(perfume_filters);
                } else {
                    sentiment_perfume_dim.filterAll();
                }
                sentiment_linechart.redrawGroup();
                //              notes_perfume_dim.filter(perfume);
                //              notes_barchart.redrawGroup();
                var input = document.getElementById("perfreview_search")
                if (checked) { input.value = perfume } else { input.value = "" };
                var e = jQuery.Event("keypress");
                e.which = 13; //choose the one you want
                e.keyCode = 13;
                $('#perfreview_search').trigger(e)
            }
            cbl = document.createElement("label");
            cbl.appendChild(cbo)
            cbl.appendChild(document.createTextNode(perfume));
            cbd.appendChild(cbl);
            cb.appendChild(cbd);
        };
    });

});




