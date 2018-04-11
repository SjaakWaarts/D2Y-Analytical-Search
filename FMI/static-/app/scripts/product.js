// script.js

'use strict';

// JQuery


function display_message(data) {
    $("#scrape_progress").append("<p>" + data + "</p>");
}

function poll() {
    var poll_interval = 0;

    $.ajax({
        url: "api/product_pollresults",
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            display_message(data);
            poll_interval = 0;
        },
        error: function () {
            poll_interval = 1000;
        },
        complete: function () {
            setTimeout(poll, poll_interval);
        },
    });
}


//$('button[name^="retrieve"]').click(function () {
//    poll();
//})


function sentiment_pie(data) {
    //    var touchdowns = resp.aggregations.touchdowns.buckets;
    // d3 donut chart
    var width = 600,
        height = 300,
        radius = Math.min(width, height) / 2;
    var color = ['#ff7f0e', '#d62728', '#2ca02c', '#1f77b4'];
    var arc = d3.svg.arc()
        .outerRadius(radius - 60)
        .innerRadius(120);
    var pie = d3.layout.pie()
        .sort(null)
        .value(function (d) { return d.count; });
    var svg = d3.select("#donut-chart").append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", "translate(" + width/1.4 + "," + height/2 + ")");
    var g = svg.selectAll(".arc")
        .data(pie(data))
        .enter()
        .append("g")
            .attr("class", "arc")
            .on('mouseover', function (d) {
                $("#tooltip")
                    .html(d.data.name)
                    .show();
            })
            .on('mousemove', function (d) {
                $("#tooltip")
                    .css('left', d3.mouse(this)[0])
                    .css('top', d3.mouse(this)[1] - 20)
            })
            .on('mouseout', function (d) {
                $("#tooltip").html('').hide();
            })
        ;
    g.append("path")
        .attr("d", arc)
        .style("fill", function (d, i) { return color[i]; });
    g.append("text")
        .attr("transform", function (d) { return "translate(" + arc.centroid(d) + ")"; })
        .attr("dy", ".35em")
        .style("text-anchor", "middle")
        .style("fill", "white")
        .text(function (d) { return d.data.name; });
}

sentiment_pie(pie_data);



