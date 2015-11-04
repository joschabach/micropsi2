

$(function(){

    var container = $('#dashboard_container');

    var nodes = $('#dashboard_nodes');
    var datatable_motivation = $('#dashboard_datatable_motivation');
    var datatable_concepts = $('#dashboard_datatable_concepts');
    var urges = $('#dashboard_urges');
    var modulators = $('#dashboard_modulators');
    var face = $('#dashboard_face');
    var valence = $('#dashboard_valence');
    var protocols = $('#dashboard_protocols');

    var perspective = $('#perspective');
    var hypo = $('#hypo');

    var old_values = {}

    function getPollParams(){
        return 1
    }

    // three states:
    //   'action': Wait for action selection or outcome
    //   'motivation': Action finished, show influence on urges
    //   'modulators': Show influence of urge changes on modulators
    var current_state = null;

    var action_outcome = 0;

    function setData(data){
        if(!current_state || current_state == 'action'){
            drawNodes(data);
            drawDatatable(data);
            $('.arrow').removeClass("green");
            $('.arrow').removeClass("red");
        }
        if(!current_state || current_state == 'motivation'){
            drawUrges(data);
            drawValence(data);
            if(action_outcome > 0) $('#arrow_motivation').addClass("green");
            else if(action_outcome < 0) $('#arrow_motivation').addClass("red");
        }
        if(!current_state || current_state == 'modulators'){
            drawUrges(data);
            drawModulators(data);
            drawFace(data);
            if(action_outcome > 0) $('#arrow_modulators').addClass("green");
            else if(action_outcome < 0) $('#arrow_modulators').addClass("red");
        }
        drawProtocols(data);
        drawPerspective(data);

        if(!current_state && data.urges) current_state = 'action'
        else if(current_state == 'motivation') current_state = 'modulators'
        else if(current_state == 'modulators') current_state = 'action'

    }

    register_stepping_function('dashboard', getPollParams, setData);

    $(document).trigger('runner_stepped');

    function drawModulators(dashboard){
        if(dashboard.modulators){
            $('[data=modulators]').show();
            var colors = {
                // base_number_of_active_motives: 0
                // base_number_of_expected_events: 0
                // base_number_of_unexpected_events: 0
                // base_sum_importance_of_intentions: 0
                // base_sum_urgency_of_intentions: 0
                // base_unexpectedness: 1
                // base_urge_change: 0
                emo_activation: 'orange',
                emo_competence: 'blue',
                emo_pleasure: 'red',
                emo_resolution: 'purple',
                emo_securing_rate: 'brown',
                emo_selection_threshold: 'gray',
                emo_sustaining_joy: 'green'
            }
            var data = [];
            var sorted = Object.keys(dashboard.modulators);
            sorted.sort();
            for(var i = 0; i < sorted.length; i++){
                if(sorted[i] in colors){
                    data.push({'name': sorted[i].substr(4).replace('_', ' '), 'value': dashboard.modulators[sorted[i]], 'color': colors[sorted[i]]});
                }
            }
            if(data.length) drawBarChart(data, [], '#dashboard_modulators', true);
            old_values.modulators = dashboard.modulators
        } else {
            $('[data=modulators]').hide();
        }
    }

    function drawNodes(dashboard){
        if('nodetypes' in dashboard){
            var total = 0;
            var keys = Object.keys(dashboard.nodetypes)
            keys.sort();
            var data = [];
            for(var i = 0; i < keys.length; i++){
                total += dashboard.nodetypes[keys[i]]
                data.push({'value': dashboard.nodetypes[keys[i]], 'name': keys[i]});
            }
            if(total == 0){
                data = [{'value': 1, 'name':'', 'color': 'lightgrey'}]
            }
            var label = total + " Nodes"
            drawPieChart(data, '#dashboard_nodes', label, null, null, true);
        }
    }

    function drawValence(dashboard){
        var data = [];
        var old_data = [];
        if('emo_valence' in dashboard.modulators){
            dashboard.modulators.emo_valence = Math.max(-1, Math.min(1, dashboard.modulators.emo_valence))
            data.push({'name': 'valence', 'value': dashboard.modulators.emo_valence, 'color': 'purple'});
        }
        if(data.length)
            drawBarChart(data, old_data, '#dashboard_valence', true, 100)
    }

    function drawUrges(dashboard){
        if (dashboard.urges){
            $('[data=urges]').show();
            var colors = {
                'Fool': 'purple',
                'eat': 'brown',
                'sleep': 'grey',
                'warmth': 'red',
                'coldness': 'blue',
                'heal': 'green'
            }
            var sorted = ["heal", "eat", "warmth", "coldness", "sleep", "Fool"];
            var data = [];
            var old_data = [];
            for(var i = 0; i < sorted.length; i++){
                var key = sorted[i];
                if(dashboard.urges && key in dashboard.urges){
                    data.push({'name': key, 'value': dashboard.urges[key], 'color': colors[key]});
                    if(old_values.urges){
                        old_data.push({'name': key, 'value': old_values.urges[key], 'color': colors[key], 'delta': Math.round((old_values.urges[key] - dashboard.urges[key]) * 100) /100})
                    }
                }
            }
            if(data.length) drawBarChart(data, old_data, '#dashboard_urges')
            old_values.urges = dashboard.urges
        } else {
            $('[data=modulators]').show();
        }
    }

    function drawDatatable(dashboard){
        var html = '<table class="table-condensed table-striped dashboard-table">';

        if(dashboard.motive){
            $('[data=motivation]').show();
            html += "<tr><th><strong>Motive:</strong></th><th>"+dashboard.motive.motive+"</th></tr>"
            html += "<tr><td>Weight:</td><td>"+parseFloat(dashboard.motive.weight).toFixed(3)+"</td></tr>"
            html += "<tr><td>Gain:</td><td>"+parseFloat(dashboard.motive.gain).toFixed(3)+"</td></tr>"
            if('action' in dashboard){
                action_outcome = dashboard.action_outcome;
                if('action_outcome' in dashboard && dashboard.action_outcome > 0){
                    html += "<tr class=\"mark_green\"><th><strong>Action:</strong></th><th>"+dashboard.action+"</th></tr>"
                    current_state = 'motivation'
                } else if('action_outcome' in dashboard && dashboard.action_outcome < 0){
                    html += "<tr class=\"mark_red\"><th><strong>Action:</strong></th><th>"+dashboard.action+"</th></tr>"
                    current_state = 'motivation'
                } else {
                    html += "<tr><th><strong>Action:</strong></th><th>"+dashboard.action+"</th></tr>"
                }
            }
        } else {
            $('[data=motivation]').hide();
        }

        datatable_motivation.html(html);
        html = '<table class="table-condensed table-striped dashboard-table wide">';

        if('situation' in dashboard){
            html += "<tr><th><strong>Situation:</strong></th><th>"+dashboard.situation+"</th></tr>"
        }

        html += "<tr><th><strong>sec/step:</strong></th><th>"+parseFloat(dashboard.stepping_rate).toFixed(3)+"</th></tr>"

        if(dashboard.concepts){
            var data = [
                {'value': dashboard.concepts.failed, 'name': 'failing', 'color': 'red'},
                {'value': dashboard.concepts.verified, 'name': 'success', 'color': 'green'},
                {'value': dashboard.concepts.checking, 'name': 'checking', 'color': 'lightgrey'},
                {'value': dashboard.concepts.off, 'name': 'off', 'color': 'darkgrey'}
            ];
            html += "<tr><th>Concepts:</th><th><div id=\"concept_graph\"></div></th></tr>";
        }
        if(dashboard.schemas){
            html += "<tr><td>Verified:</td><td>" + (dashboard.schemas.verified || '0') + "</td></tr>";
            html += "<tr><td>Checking:</td><td>" + (dashboard.schemas.checking || '0') + "</td></tr>";
            html += "<tr><td>Failed:</td><td>" + (dashboard.schemas.failed || '0') + "</td></tr>";
        }

        if(dashboard.automatisms){
            html += "<tr><th colspan=\"2\">Automatisms:</th></tr>"
            for(var i = 0; i < dashboard.automatisms.length; i++){
                var auto = dashboard.automatisms[i]
                html += "<tr><td class=\""+auto.name.replace(">","")+"\">" + auto.name + "</td><td><span class=\"mini\">complexity:"+auto.complexity+"</span><span class=\"mini\">competence:"+parseFloat(auto.competence).toFixed(3)+"</span></td></tr>"
            }
        }
        if(dashboard.hypotheses){
            html += "<tr><th>Hypotheses:</th><td>"+dashboard.hypotheses.join("<br />")+"</td></tr>";
        }

        html += "</table>"
        datatable_concepts.html(html);
        if(dashboard.reinforcement){
            var classname = (dashboard.reinforcement.result > 0) ? 'mark_green' : 'mark_red';
            $('.' + dashboard.reinforcement.name.replace(">","")).addClass(classname);
        }
        if(dashboard.concepts && dashboard.concepts.total){
            drawPieChart(data, '#concept_graph', dashboard.concepts.total, 80, 5);
        }
    }

    function drawProtocols(data){
        if(data.learning && data.learning.protocols){
            $('[data=protocols]').show();
            html = "<p class=\"linkweight-container\">";
            for(var i = 0; i < data.learning.protocols.length; i++){
                html += '<span class="linkweight-tick" style="opacity:'+data.learning.protocols[i]+'"></span>'
            }
            html += "</p>";
            protocols.html(html);
        } else {
            $('[data=protocols]').hide();
        }
    }

    function drawPerspective(data){
        if(data.agent_view || data.hypo_view){
            $('[data=perspective]').show();
            var agent_view = '';
            var hypo_view = '';
            if(data.agent_view){
                agent_view = '<p>Perspective:</p><img src="'+data.agent_view.content_type+','+data.agent_view.data+'" />';
            }
            if(data.hypo_view){
                hypo_view = '<p>Hypothesis:</p><img src="'+data.hypo_view.content_type+','+data.hypo_view.data+'" />';
            }
            perspective.html(agent_view);
            hypo.html(hypo_view);
        } else {
            $('[data=perspective]').hide();
        }
    }

    function insertLinebreaks(d) {
        var el = d3.select(this);
        var words = d.split(' ');
        el.text('');

        for (var i = 0; i < words.length; i++) {
            var tspan = el.append('tspan').text(words[i]);
            if (i > 0)
                tspan.attr('x', 0).attr('dy', '15');
        }
    }

    function drawBarChart(data, old_data, selector, negative_values, width, height){
            var margin = {top: 20, right: 20, bottom: 40, left: 30},
            width = width || 400
            height = height || 200
            width = width - margin.left - margin.right,
            height = height - margin.top - margin.bottom;

            var x = d3.scale.ordinal().rangeRoundBands([0, width], .05);
            var y = d3.scale.linear().range([height, 0]);

            var xAxis = d3.svg.axis()
                .scale(x)
                .orient("bottom")

            var yAxis = d3.svg.axis()
                .scale(y)
                .orient("left")
                .ticks(10);

            var svg = d3.select(selector).select("svg");

            if (svg.empty()){
                svg = d3.select(selector).append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                  .append("g")
                    .attr("transform",
                          "translate(" + margin.left + "," + margin.top + ")");

                svg.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(0," + height + ")")
                    .call(xAxis)
                  .selectAll("text")
                    .style("text-anchor", "middle")
                    .style("font-size", "80%")

                svg.append("g")
                    .attr("class", "y axis")
                    .call(yAxis)
                  .selectAll("text")
                    .style("font-size", "80%")

                if(negative_values){
                    svg.select(".x.axis").attr("class", "x axis noborder")
                    svg.append("g")
                        .attr("class", "zero axis")
                        .attr("transform", "translate(0," + height/2 + ")")
                        .call(xAxis)
                }
                svg.append("svg:defs")
                for(var i =0; i < data.length; i++){
                    var color = d3.rgb(data[i].color);
                    var gradient = svg.select("defs")
                        .append("svg:linearGradient")
                        .attr("id", "gradient_"+data[i].color)
                        .attr("x1", "100%")
                        .attr("y1", "0%")
                        .attr("x2", "0%")
                        .attr("y2", "20%")
                        .attr("spreadMethod", "pad");

                        gradient.append("svg:stop")
                        .attr("offset", "0%")
                        .attr("stop-color", color.brighter(2))
                        .attr("stop-opacity", 1);

                        gradient.append("svg:stop")
                        .attr("offset", "100%")
                        .attr("stop-color",  color.darker(2))
                        .attr("stop-opacity", 1);
                }
                var color = d3.rgb('#333');
                var gradient = svg.select("defs")
                        .append("svg:linearGradient")
                        .attr("id", "gradient_background")
                        .attr("x1", "0%")
                        .attr("y1", "0%")
                        .attr("x2", "100%")
                        .attr("y2", "0%")
                        .attr("spreadMethod", "pad");

                        gradient.append("svg:stop")
                        .attr("offset", "0%")
                        .attr("stop-color", color.brighter(2))
                        .attr("stop-opacity", 1);

                        gradient.append("svg:stop")
                        .attr("offset", "100%")
                        .attr("stop-color",  color.darker(1))
                        .attr("stop-opacity", 1);

            } else {
                svg = svg.select("g")
            }

            x.domain(data.map(function(d) { return d.name; }));

            if(negative_values)
                y.domain([-1, 1]);
            else
                y.domain([0, 1]);

            svg.select(".y.axis")
                .call(yAxis)
                .selectAll("text")
                .style("font-size", "80%")

            svg.select(".x.axis")
                .call(xAxis)
                .selectAll("text")
                .style("font-size", "80%");

            if(negative_values){
                svg.select(".zero.axis")
                    .call(xAxis)
                    .selectAll("text")
                    .style("display", "none")
                    .selectAll(".ticks")
                    .attr("dy", -5)
            }

            var background_bars = svg.selectAll(".background_bar").data(data)

            var bars = svg.selectAll('.bar')
                .data(data)

            background_bars.enter()
                .append("svg:rect")
                .attr("class", "background_bar")
                .style("fill", "url(\#gradient_background)")
                .attr("width", x.rangeBand())
                .attr("opacity", (negative_values) ? 0 : 0.8)
                .attr("y", y(1))
                .attr("height", height)
            //enter
            bars.enter()
                .append("svg:rect")
                .attr("class", "bar")
                .attr("fill", "#900")

            //exit
            bars.exit().remove()
            background_bars.exit().remove()

            background_bars.transition().duration(0).attr("x", function(d) { return x(d.name); })
            bars
            .transition()
            .duration(500)
            .ease("quad")
               .style("fill", function(d){ return "url(\#gradient_"+d.color})
               .attr("x", function(d) { return x(d.name); })
               .attr("width", x.rangeBand())
               .attr("y", function(d) {
                    if(negative_values) {
                        return (d.value < 0) ? y(0) : y(d.value)
                    } else {
                        return y(d.value);
                    }
                })
               .attr("height", function(d) { 
                    if(negative_values){
                        return height/2 - y(Math.abs(d.value))
                    } else {
                        return height - y(d.value);
                    }
                });

           svg.selectAll('g.x.axis g text').each(insertLinebreaks);

           if(old_data){
                var oldbars = svg.selectAll('.old-bar')
                    .data(old_data)
                var lines = svg.selectAll('.arrowline')
                    .data(old_data)
                var arrowheads = svg.select("defs")
                    .selectAll('.arrowhead')
                    .data(old_data)

                //enter
                oldbars.enter()
                    .append("svg:rect")
                    .attr("class", "old-bar")
                    .attr("fill", "#000")
                    .attr("opacity", 0.4)
                lines.enter()
                    .append("line")
                    .attr("class", "arrowline")
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 3)
                    .attr("opacity", 0.7)
                arrowheads.enter()
                    .append("svg:marker")
                    .attr("viewBox", "0 0 10 10")
                    .attr("markerUnits", "strokeWidth")
                    .attr("markerWidth", 5)
                    .attr("markerHeight", 3)
                    .attr("class", "arrowhead")
                    .attr("opacity", 0.7)
                    .attr("fill", "white")
                    .append("svg:path")
                    .attr("d", "M 0 0 L 10 5 L 0 10 z")

                //exit
                oldbars.exit()
                    .transition()
                    .duration(500)
                    .ease("exp")
                        .attr("height", 0)
                        .remove()
                lines.exit()
                        .remove()

                oldbars.transition()
                    .duration(500)
                    .ease("quad")
                       .attr("x", function(d) { return x(d.name); })
                       .attr("width", x.rangeBand())
                       .attr("y", function(d) {
                            if(d.delta > 0) return y(d.value);
                            else if (d.delta < 0) return y(d.value - d.delta)
                            else return y(d.value - d.delta)
                        })
                       .attr("height", function(d) {
                            if (d.delta == 0) return 0
                            return height - y(Math.abs(d.delta))
                        })

                arrowheads.transition()
                    .duration(function(d){ return Math.abs(d.delta) * 50})
                    .ease("quad")
                        .attr("id", function(d){ return "arrow_" + d.name })
                        .attr("opacity", function(d){
                            return (d.delta != 0) ? 0.7 : 0;
                        })
                        .attr("refX", 0)
                        .attr("refY", 5)
                        .attr("orient", "auto")
                        .attr("fill", function(d){
                            if (d.delta != 0) return "white"
                            else return "transparent"
                        })

                lines.transition()
                    .duration(function(d){ return Math.abs(d.delta) * 50})
                    .ease("quad")
                        .attr("opacity", function(d){
                            return (d.delta != 0) ? 0.7 : 0;
                        })
                        .attr("x1", function(d){ return x(d.name) + (x.rangeBand()/2) })
                        .attr("y1", function(d) {
                            if(d.delta != 0) return y(d.value);
                            else return y(d.value - d.delta)
                        })
                        .attr("x2", function(d){ return x(d.name) + (x.rangeBand()/2)  })
                        .attr("y2", function(d){
                            var level = Math.min(10, Math.abs(y(d.value - d.delta) - y(d.value))) - 1
                            if(d.delta > 0) return y(d.value - d.delta) - level;
                            else if(d.delta < 0) return y(d.value - d.delta) + level ;
                            else return y(0)
                        })
                        .attr( "marker-end", function(d){ return "url(\#arrow_"+d.name+")" })
           }
    }

    function drawPieChart(data, selector, label, height, margin, legend){

        var values = [];
        for(var i = 0; i < data.length; i++){
            values.push(data[i].value);
        }

        // Store the currently-displayed angles in this._current.
        // Then, interpolate from this._current to the new angles.
        function arcTween(a) {
            var i = d3.interpolate(this._current, a);
            this._current = i(0);
            return function(t) {
                return arc(i(t));
            };
        }

        //Width and height
        margin = margin || 20;
        height = height || 200;
        width = height || 200;

        var outerRadius = width / 2;
        var innerRadius = width / 3;
        var duration = 500
        var color = d3.scale.category10()

        var arc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(outerRadius);

        var donut = d3.layout.pie().sort(null)

        var svg = d3.select(selector).select("svg");

        if(!svg.empty()){
            var arcs = svg.selectAll(".arc")
            arcs.data(donut(values)); // recompute angles, rebind data
            arcs.transition().ease("quad").duration(duration).attrTween("d", arcTween);
            svg.select("text.chartLabel").text(label);

        } else {
            // init
            var svg = d3.select(selector).append("svg:svg")
                .attr("width", width + 2*margin).attr("height", height+2*margin);

            var arc_grp = svg.append("svg:g")
                .attr("class", "arcGrp")
                .attr("transform", "translate(" + ((width / 2) + margin) + "," + ((height / 2) + margin) + ")");

            // group for center text
            var center_group = svg.append("svg:g")
                .attr("class", "ctrGroup")
                .attr("transform", "translate(" + ((width / 2) + margin) + "," + ((height / 2) + margin) + ")");

            // center label
            var pieLabel = center_group.append("svg:text")
                .attr("dy", ".35em").attr("class", "chartLabel")
                .attr("text-anchor", "middle")
                .text(label);

            // draw arc paths
            var arcs = arc_grp.selectAll("path")
                .data(donut(values));
            arcs.enter().append("svg:path")
                .attr("fill", function(d, i) {return data[i].color || color(i);})
                .attr("class", "arc")
                .attr("d", arc)
                .each(function(d) {this._current = d});

            // draw slice labels
            if(legend){
                var legend_size = 10;
                var legend = svg.selectAll('.legend')
                  .data(color.domain())
                  .enter()
                  .append('g')
                  .attr('class', 'legend')
                  .attr('transform', function(d, i) {
                    var horz = width + 2*margin;
                    var vert = i * legend_size;
                    return 'translate(' + horz + ',' + vert + ')';
                  });
                legend.append('text')
                  .attr('x', -legend_size -2)
                  .attr('y', legend_size -2)
                  .style('font-size', '10px')
                  .text(function(d, i) { return data[i].name; })
                  .attr('text-anchor', 'end')
                legend.append('rect')
                  .attr('x', -legend_size)
                  .attr('y', 0)
                  .attr('width', legend_size)
                  .attr('height', legend_size)
                  .style('fill', color)
                  .style('stroke', color);

            }
        }
    }

    function drawFace(data, selector){
        var margin = 30;
        var width = 100;
        var height = 100;

        var raster = width / 8; // face has 8x8 pixels
        var eye_color = '#fff'
        var pup_color = '#523D89'
        var nose_color = '#694032'
        var mouth_color = '#764237'

        var emoexpression = data.face;

        var shapes = {
            'eye_l': {
                width: 2*raster,
                height: raster,
                x: margin + raster,
                y: margin + 4*raster,
                color: eye_color
            },
            'eye_r': {
                width: 2*raster,
                height: raster,
                x: margin + 5*raster,
                y: margin + 4*raster,
                color: eye_color
            },
            'pup_l': {
                width: raster,
                height: raster,
                x: margin + 2*raster,
                y: margin + 4*raster,
                color: pup_color
            },
            'pup_r': {
                width: raster,
                height: raster,
                x: margin + 5*raster,
                y: margin + 4*raster,
                color: pup_color
            },
            'nose': {
                width: 2*raster,
                height: 0.9 * raster,
                x: margin + 3*raster,
                y: margin + 5*raster,
                color: nose_color
            },
            'upper_lip': {
                width: 4 * raster,
                height: 0.5 * raster,
                x: margin + 2*raster,
                y: margin + 6*raster,
                color: mouth_color
            },
            'lower_lip': {
                width: 4*raster,
                height: 0.5 * raster,
                x: margin + 2*raster,
                y: margin + 6.5*raster,
                color: mouth_color
            },
            'corner_l': {
                width: 0.5 * raster,
                height: 0.9 * raster,
                x: margin + 2*raster,
                y: margin + 6*raster,
                color: mouth_color
            },
            'corner_r': {
                width: 0.5 * raster,
                height: 0.9 * raster,
                x: margin + 5.5*raster,
                y: margin + 6*raster,
                color: mouth_color
            }
        }

        var svg = d3.select('#dashboard_face').select('svg');

        if (svg.empty()){
            svg = d3.select('#dashboard_face')
                    .append("svg")
                    .attr("width", width + 2*margin)
                    .attr("height", height + 2*margin);

            // add image
            var imgs = svg.selectAll("image").data([0]);
            imgs.enter()
                .append("svg:image")
                .attr("xlink:href", "/static/img/stevehead.png")
                .attr("x", margin)
                .attr("y", margin)
                .attr("width", width)
                .attr("height", height);

            var coloroverlay = svg.append("rect")
                .attr("x", margin)
                .attr("y", margin)
                .attr("width", width)
                .attr("height", height)
                .attr("class", "coloroverlay")
                .attr("opacity", "0")

            for(var key in shapes){
                svg.append("rect")
                    .attr("x", shapes[key].x)
                    .attr("y", shapes[key].y)
                    .attr("width", shapes[key].width)
                    .attr("height", shapes[key].height)
                    .attr("fill", shapes[key].color)
                    .attr("class", key);
            }
        }

        face_r = 100;
        face_g = 100;
        face_b = 100;

        // activation slightly reddens the face
        face_r += 255 * emoexpression["exp_activation"] / 5;

        // anger strongly reddens the face
        face_r += 255 * emoexpression["exp_anger"] / 3;
        face_g -= 255 * emoexpression["exp_anger"] / 10;
        face_b -= 255 * emoexpression["exp_anger"] / 10;

        // fear pales the face
        face_r -= 255 * emoexpression["exp_fear"] / 5;
        face_g -= 255 * emoexpression["exp_fear"] / 5;
        face_b -= 255 * emoexpression["exp_fear"] / 5;

        // pain greens the face
        face_r -= 255 * emoexpression["exp_pain"] / 20;
        face_g += 255 * emoexpression["exp_pain"] / 20;
        face_b -= 255 * emoexpression["exp_pain"] / 20;

        // face_background_m.uniforms["color"]["value"] = new THREE.Color(face_r, face_g, face_b );
        svg.selectAll(".coloroverlay")
            .attr("opacity", "0")
            .attr("fill", d3.rgb(face_r, face_g, face_b).toString())

        // -- pupil position
        pup_depressor = 0
        pup_depressor += emoexpression["exp_sadness"];
        svg.selectAll('.pup_l')
            .attr('y', shapes.pup_l.y + pup_depressor * 6)
            .attr('height', shapes.pup_l.height * (1 - pup_depressor/2))
        svg.selectAll('.pup_r')
            .attr('y', shapes.pup_r.y + pup_depressor * 6)
            .attr('height', shapes.pup_r.height * (1 - pup_depressor/2))

        // -- eye height
        eye_l_h = 1;
        eye_r_h = 1;

        // pain lowers eye height left and increases right
        eye_l_h -= emoexpression["exp_pain"] / 2;
        eye_r_h += emoexpression["exp_pain"] / 2;

        // surprise increaes eye height
        eye_l_h += emoexpression["exp_surprise"] * 1.8;
        eye_r_h += emoexpression["exp_surprise"] * 1.8;

        // anger decreases eye height
        eye_l_h -= emoexpression["exp_anger"] / 2;
        eye_r_h -= emoexpression["exp_anger"] / 2;

        // fear increases eye height
        eye_l_h += emoexpression["exp_fear"];
        eye_r_h += emoexpression["exp_fear"];

        eye_l_newheight = shapes.eye_l.height * eye_l_h
        diff_eye_l_h = eye_l_newheight - shapes.eye_l.height
        eye_r_newheight = shapes.eye_r.height * eye_r_h
        diff_eye_r_h = eye_r_newheight - shapes.eye_r.height

        // -- eye width
        eye_l_w = 1;
        eye_r_w = 1;

        // surprise decreases eye width, slightly
        eye_l_w -= emoexpression["exp_surprise"] / 5;
        eye_r_w -= emoexpression["exp_surprise"] / 5;

        // anger increases eye width
        eye_l_w += emoexpression["exp_anger"] / 2;
        eye_r_w += emoexpression["exp_anger"] / 2;

        // fear increases eye width
        eye_l_w += emoexpression["exp_fear"] / 2;
        eye_r_w += emoexpression["exp_fear"] / 2;

        eye_l_newwidth = shapes.eye_l.width * eye_l_w
        diff_eye_l_w = eye_l_newwidth - shapes.eye_l.width
        eye_r_newwidth = shapes.eye_r.width * eye_r_w
        diff_eye_r_w = eye_r_newwidth - shapes.eye_r.width

        // -- eye position
        eye_raiser = 0

        // surprise increaes eye position
        eye_raiser += emoexpression["exp_surprise"] * 8;

        svg.selectAll('.eye_l')
            .attr("y", shapes.eye_l.y - (diff_eye_l_h/2) - eye_raiser)
            .attr("x", shapes.eye_l.x - (diff_eye_l_w/2) + eye_raiser/10)
            .attr("width", eye_l_newwidth)
            .attr("height", eye_l_newheight)
        svg.selectAll('.eye_r')
            .attr("y", shapes.eye_r.y - (diff_eye_r_h/2) - eye_raiser)
            .attr("x", shapes.eye_r.x - (diff_eye_r_w/2) + eye_raiser/10)
            .attr("width", eye_r_newwidth)
            .attr("height", eye_l_newheight)

        // -- lip corners
        lip_corner_depressor = 0

        // sadness depresses lip corners
        lip_corner_depressor -= emoexpression["exp_sadness"] * 40;

        // joy raises 'em
        lip_corner_depressor += emoexpression["exp_joy"] * 20;

        // -- lip presser
        lip_presser = 0;

        lip_presser += emoexpression["exp_pain"] * 0.5;
        lip_presser += emoexpression["exp_anger"] * 0.5;
        lip_presser += emoexpression["exp_fear"] * 0.5;
        lip_presser += emoexpression["exp_joy"] * 0.2;

        lip_presser = Math.min(lip_presser, 1)
        lip_corner_depressor = lip_corner_depressor

        svg.selectAll('.corner_l')
            .attr("width", shapes.corner_l.width * (1 - lip_presser))
            .attr("height", shapes.corner_l.height * (1 - lip_presser))
            .attr("y", shapes.corner_l.y + (lip_presser * 50 - lip_corner_depressor)/5)
        svg.selectAll('.corner_r')
            .attr("width", shapes.corner_l.width * (1 - lip_presser))
            .attr("height", shapes.corner_r.height * (1 - lip_presser))
            .attr("y", shapes.corner_r.y + (lip_presser * 50 - lip_corner_depressor)/5)

        // -- lower lip depressor
        lower_lip_depressor = 0;
        lower_lip_depressor += emoexpression["exp_surprise"] * 50;
        if(lower_lip_depressor > 50) {
            lower_lip_depressor = 50;
        }
        lower_lip_depressor = lower_lip_depressor / 10

        diff_upper_lip_h = shapes.upper_lip.height - (shapes.upper_lip.height * (1 - lip_presser))

        svg.selectAll('.upper_lip')
            .attr("height", shapes.upper_lip.height * (1 - lip_presser))
            .attr("width", shapes.upper_lip.width * (1 - (lip_presser / 4)))
            .attr("y", shapes.upper_lip.y + diff_upper_lip_h + lip_presser * 8)

        svg.selectAll('.lower_lip')
            .attr("height", shapes.lower_lip.height * (1 - lip_presser))
            .attr("width", shapes.lower_lip.width * (1 - (lip_presser / 4)))
            .attr("y", shapes.lower_lip.y + lip_presser*8 + lower_lip_depressor)

    }

});