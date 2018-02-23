//Practically all this code comes from https://github.com/alangrafu/radar-chart-d3
//I only made some additions and aesthetic adjustments to make the chart look better 
//(of course, that is only my point of view)
//Such as a better placement of the titles at each line end, 
//adding numbers that reflect what each circular level stands for
//Not placing the last level and slight differences in color
//
//For a bit of extra information check the blog about it:
//http://nbremer.blogspot.nl/2013/09/making-d3-radar-chart-look-bit-better.html

var RadarChart = {
    draw: function (id, chart_data, colIndexes, options) {
        var cfg = {
            radius: 5,
            w: 600,
            h: 600,
            factor: 1,
            factorLegend: .85,
            levels: 3,
            maxValue: 0,
            radians: 2 * Math.PI,
            opacityArea: 0.5,
            ToRight: 5,
            TranslateX: 80,
            TranslateY: 30,
            ExtraWidthX: 200,
            ExtraWidthY: 100,
            color: d3.scale.category10()
        };

        var data = [];
        var LegendOptions = [];
        for (var colnr = 1; colnr < chart_data[0].length; colnr++) {
            var series = [];
            for (var rownr = 1; rownr < chart_data.length; rownr++) {
                var axis = chart_data[rownr][0];
                var value = chart_data[rownr][colnr];
                series.push({ 'axis': axis, 'value': value });
            }
            if (colIndexes.indexOf(colnr) >= 0) {
                LegendOptions.push(chart_data[0][colnr]);
                data.push(series);
            }
        }

        if ('undefined' !== typeof options) {
            for (var i in options) {
                if ('undefined' !== typeof options[i]) {
                    cfg[i] = options[i];
                }
            }
        }
        cfg.maxValue = Math.max(cfg.maxValue, d3.max(data, function (i) { return d3.max(i.map(function (o) { return o.value; })) }));
        var allAxis = (data[0].map(function (i, j) { return i.axis }));
        var total = allAxis.length;
        var radius = cfg.factor * Math.min(cfg.w / 2, cfg.h / 2);
        var Format = d3.format('%');
        d3.select(id).select("svg").remove();

        var g = d3.select(id)
                .append("svg")
                .attr("width", cfg.w + cfg.ExtraWidthX)
                .attr("height", cfg.h + cfg.ExtraWidthY)
                .append("g")
                .attr("transform", "translate(" + cfg.TranslateX + "," + cfg.TranslateY + ")");
        ;

        var tooltip;

        //Circular segments
        for (var j = 0; j < cfg.levels - 1; j++) {
            var levelFactor = cfg.factor * radius * ((j + 1) / cfg.levels);
            g.selectAll(".levels")
             .data(allAxis)
             .enter()
             .append("svg:line")
             .attr("x1", function (d, i) { return levelFactor * (1 - cfg.factor * Math.sin(i * cfg.radians / total)); })
             .attr("y1", function (d, i) { return levelFactor * (1 - cfg.factor * Math.cos(i * cfg.radians / total)); })
             .attr("x2", function (d, i) { return levelFactor * (1 - cfg.factor * Math.sin((i + 1) * cfg.radians / total)); })
             .attr("y2", function (d, i) { return levelFactor * (1 - cfg.factor * Math.cos((i + 1) * cfg.radians / total)); })
             .attr("class", "line")
             .style("stroke", "grey")
             .style("stroke-opacity", "0.75")
             .style("stroke-width", "0.3px")
             .attr("transform", "translate(" + (cfg.w / 2 - levelFactor) + ", " + (cfg.h / 2 - levelFactor) + ")");
        }

        //Text indicating at what % each level is
        for (var j = 0; j < cfg.levels; j++) {
            var levelFactor = cfg.factor * radius * ((j + 1) / cfg.levels);
            g.selectAll(".levels")
             .data([1]) //dummy data
             .enter()
             .append("svg:text")
             .attr("x", function (d) { return levelFactor * (1 - cfg.factor * Math.sin(0)); })
             .attr("y", function (d) { return levelFactor * (1 - cfg.factor * Math.cos(0)); })
             .attr("class", "legend")
             .style("font-family", "sans-serif")
             .style("font-size", "10px")
             .attr("transform", "translate(" + (cfg.w / 2 - levelFactor + cfg.ToRight) + ", " + (cfg.h / 2 - levelFactor) + ")")
             .attr("fill", "#737373")
             .text(Format((j + 1) * cfg.maxValue / cfg.levels));
        }

        series = 0;

        var axis = g.selectAll(".axis")
                .data(allAxis)
                .enter()
                .append("g")
                .attr("class", "axis");

        axis.append("line")
            .attr("x1", cfg.w / 2)
            .attr("y1", cfg.h / 2)
            .attr("x2", function (d, i) { return cfg.w / 2 * (1 - cfg.factor * Math.sin(i * cfg.radians / total)); })
            .attr("y2", function (d, i) { return cfg.h / 2 * (1 - cfg.factor * Math.cos(i * cfg.radians / total)); })
            .attr("class", "line")
            .style("stroke", "grey")
            .style("stroke-width", "1px");

        axis.append("text")
            .attr("class", "legend")
            .text(function (d) { return d })
            .style("font-family", "sans-serif")
            .style("font-size", "11px")
            .attr("text-anchor", "middle")
            .attr("dy", "1.5em")
            .attr("transform", function (d, i) { return "translate(0, -10)" })
            .attr("x", function (d, i) { return cfg.w / 2 * (1 - cfg.factorLegend * Math.sin(i * cfg.radians / total)) - 60 * Math.sin(i * cfg.radians / total); })
            .attr("y", function (d, i) { return cfg.h / 2 * (1 - Math.cos(i * cfg.radians / total)) - 20 * Math.cos(i * cfg.radians / total); });


        data.forEach(function (y, x) {
            dataValues = [];
            g.selectAll(".nodes")
              .data(y, function (j, i) {
                  dataValues.push([
                    cfg.w / 2 * (1 - (parseFloat(Math.max(j.value, 0)) / cfg.maxValue) * cfg.factor * Math.sin(i * cfg.radians / total)),
                    cfg.h / 2 * (1 - (parseFloat(Math.max(j.value, 0)) / cfg.maxValue) * cfg.factor * Math.cos(i * cfg.radians / total))
                  ]);
              });
            dataValues.push(dataValues[0]);
            g.selectAll(".area")
                           .data([dataValues])
                           .enter()
                           .append("polygon")
                           .attr("class", "radar-chart-serie" + series)
                           .style("stroke-width", "2px")
                           .style("stroke", cfg.color(series))
                           .attr("points", function (d) {
                               var str = "";
                               for (var pti = 0; pti < d.length; pti++) {
                                   str = str + d[pti][0] + "," + d[pti][1] + " ";
                               }
                               return str;
                           })
                           .style("fill", function (j, i) { return cfg.color(series) })
                           .style("fill-opacity", cfg.opacityArea)
                           .on('mouseover', function (d) {
                               z = "polygon." + d3.select(this).attr("class");
                               g.selectAll("polygon")
                                .transition(200)
                                .style("fill-opacity", 0.1);
                               g.selectAll(z)
                                .transition(200)
                                .style("fill-opacity", .7);
                           })
                           .on('mouseout', function () {
                               g.selectAll("polygon")
                                .transition(200)
                                .style("fill-opacity", cfg.opacityArea);
                           });
            series++;
        });
        series = 0;


        data.forEach(function (y, x) {
            g.selectAll(".nodes")
              .data(y).enter()
              .append("svg:circle")
              .attr("class", "radar-chart-serie" + series)
              .attr('r', cfg.radius)
              .attr("alt", function (j) { return Math.max(j.value, 0) })
              .attr("cx", function (j, i) {
                  dataValues.push([
                    cfg.w / 2 * (1 - (parseFloat(Math.max(j.value, 0)) / cfg.maxValue) * cfg.factor * Math.sin(i * cfg.radians / total)),
                    cfg.h / 2 * (1 - (parseFloat(Math.max(j.value, 0)) / cfg.maxValue) * cfg.factor * Math.cos(i * cfg.radians / total))
                  ]);
                  return cfg.w / 2 * (1 - (Math.max(j.value, 0) / cfg.maxValue) * cfg.factor * Math.sin(i * cfg.radians / total));
              })
              .attr("cy", function (j, i) {
                  return cfg.h / 2 * (1 - (Math.max(j.value, 0) / cfg.maxValue) * cfg.factor * Math.cos(i * cfg.radians / total));
              })
              .attr("data-id", function (j) { return j.axis })
              .style("fill", cfg.color(series)).style("fill-opacity", .9)
              .on('mouseover', function (d) {
                  newX = parseFloat(d3.select(this).attr('cx')) - 10;
                  newY = parseFloat(d3.select(this).attr('cy')) - 5;

                  tooltip
                      .attr('x', newX)
                      .attr('y', newY)
                      .text(Format(d.value))
                      .transition(200)
                      .style('opacity', 1);

                  z = "polygon." + d3.select(this).attr("class");
                  g.selectAll("polygon")
                      .transition(200)
                      .style("fill-opacity", 0.1);
                  g.selectAll(z)
                      .transition(200)
                      .style("fill-opacity", .7);
              })
              .on('mouseout', function () {
                  tooltip
                      .transition(200)
                      .style('opacity', 0);
                  g.selectAll("polygon")
                      .transition(200)
                      .style("fill-opacity", cfg.opacityArea);
              })
              .append("svg:title")
              .text(function (j) { return Math.max(j.value, 0) });

            series++;
        });
        //Tooltip
        tooltip = g.append('text')
                   .style('opacity', 0)
                   .style('font-family', 'sans-serif')
                   .style('font-size', '13px');
    }
};


var WordCloudChart = {
    draw: function (id, chart_data, colIndexes, options) {
        var cfg = {
            w: 600,
            h: 600,
        }
        var color = d3.scale.linear()
            .domain([0, 1, 2, 3, 4, 5, 6, 10, 15, 20, 100])
            .range(["#ddd", "#ccc", "#bbb", "#aaa", "#999", "#888", "#777", "#666", "#555", "#444", "#333", "#222"]);
        if ('undefined' !== typeof options) {
            for (var i in options) {
                cfg[i] = options[i];
            }
        }

        function draw(words) {
            d3.select(id).select("svg").remove();
            d3.select(id).append("svg")
                .attr("width", 850)
                .attr("height", 350)
                //.attr("width", cfg.w)
                //.attr("height", cfg.h)
                .attr("class", "wordcloud")
                .append("g")
                // without the transform, words words would get cutoff to the left and top, they would
                // appear outside of the SVG area
                .attr("transform", "translate(320,200)")
                .selectAll("text")
                .data(words)
                .enter().append("text")
                .style("font-size", function (d) { return d.size + "px"; })
                .style("fill", function (d, i) { return color(i); })
                .attr("transform", function (d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .text(function (d) { return d.text; });
        }

        var data = [];
        var LegendOptions = [];
        for (var rownr = 1; rownr < chart_data.length; rownr++) {
            var word = chart_data[rownr][0];
            var frequency = 0
            for (var colnr = 1; colnr < chart_data[0].length; colnr++) {
                if (colIndexes.indexOf(colnr) >= 0) {
                    frequency = frequency + chart_data[rownr][colnr];
                    data.push({ 'text': word, 'size': frequency });
                }
            }
        }

        d3.layout.cloud().size([800, 300])
        //d3.layout.cloud().size([cfg.w, cfg.h])
            .timeInterval(200)
            .words(data)
            .rotate(0)
            .fontSize(function (d) { return d.size; })
            .on("end", draw)
            .start();
    }
}