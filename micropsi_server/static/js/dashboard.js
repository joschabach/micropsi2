

$(function(){

    var container = $('#dashboard_container');

    var nodes = $('<div id="dashboard_nodes" class="dashboard-item right"></div>');
    var datatable = $('<div id="dashboard_datatable" class="dashboard-item right"></div>');
    var urges = $('<div id="dashboard_urges" class="dashboard-item left"></div>');
    var modulators = $('<div id="dashboard_modulators" class="dashboard-item left"></div>');
    var face = $('<div id="dashboard_face" class="dashboard-item right"></div>');

    container.append(datatable, nodes,  face, urges, modulators, $('<p style="break:both"></p>'));

    var d3graphs = {};

    function getPollParams(){
        return 1
    }

    function setData(data){
        draw_urges(data);
        draw_modulators(data);
        draw_nodes(data);
        draw_datatable(data);
        draw_face(data);
    }

    register_stepping_function('dashboard', getPollParams, setData);

    $(document).trigger('runner_stepped');

    function draw_modulators(dashboard){
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
        for(var key in dashboard.modulators){
            if(key in colors){
                data.push({'name': key.substr(4).replace('_', ' '), 'value': dashboard.modulators[key], 'color': colors[key]});
            }
        }
        if(data.length) drawBarChart(data, '#dashboard_modulators');
    }

    function draw_nodes(dashboard){
        var total = parseInt(dashboard['count_nodes'])
        var data = [
            {'value': dashboard['count_negative_nodes'], 'name': 'failing', 'color': 'red'},
            {'value': dashboard['count_positive_nodes'], 'name': 'success', 'color': 'green'},
            {'value': total - dashboard['count_negative_nodes'] - dashboard['count_negative_nodes'], name: 'off', color: 'lightgrey'}
        ];
        var label = total + " Nodes"
        draw_circle_chart(data, '#dashboard_nodes', label);
    }

    function draw_urges(dashboard){
        var colors = {
            'Fool': 'purple',
            'eat': 'brown',
            'sleep': 'grey',
            'warmth': 'red',
            'coldness': 'blue',
            'heal': 'green'
        }
        var data = [];
        for(var key in dashboard.urges){
            data.push({'name': key, 'value': dashboard.urges[key], 'color': colors[key]});
        }
        if(data.length) drawBarChart(data, '#dashboard_urges')
    }

    function draw_datatable(dashboard){
        var html = '<table class="table-condensed table-striped dashboard-table">';

        if(dashboard.motive){
            html += "<tr><th><strong>Motive:</strong></th><th>"+dashboard.motive.motive+"</th></tr>"
            html += "<tr><td>Weight:</td><td>"+parseFloat(dashboard.motive.weight).toFixed(3)+"</td></tr>"
            html += "<tr><td>Gain:</td><td>"+parseFloat(dashboard.motive.gain).toFixed(3)+"</td></tr>"
        }
        if('action' in dashboard){
            html += "<tr><th><strong>Action:</strong></th><th>"+dashboard.action+"</th></tr>"
        }
        if('situation' in dashboard){
            html += "<tr><th><strong>Situation:</strong></th><th>"+dashboard.situation+"</th></tr>"
        }

        html += "<tr><th><strong>sec/step:</strong></th><th>"+parseFloat(dashboard.stepping_rate).toFixed(3)+"</th></tr>"

        if(dashboard.concepts){
            var data = [
                {'value': dashboard.concepts.failed.length, 'name': 'failing', 'color': 'red'},
                {'value': dashboard.concepts.verified.length, 'name': 'success', 'color': 'green'},
                {'value': dashboard.concepts.checking.length, 'name': 'checking', 'color': 'lightgrey'},
                {'value': dashboard.concepts.off, 'name': 'off', 'color': 'darkgrey'}
            ];
            html += "<tr><th>Concepts:</th><th><div id=\"concept_graph\"></div></th></tr>";
            html += "<tr><td>Verified:</td><td>" + (dashboard.concepts.verified.sort().join('<br />') || '--') + "</td></tr>";
            html += "<tr><td>Checking:</td><td>" + (dashboard.concepts.checking.sort().join('<br />') || '--') + "</td></tr>";
            html += "<tr><td>Failed:</td><td>" + (dashboard.concepts.failed.sort().join('<br />') || '--') + "</td></tr>";
        }

        if(dashboard.automatisms){
            html += "<tr><th>Automatisms:</th><td>"
            for(var i = 0; i < dashboard.automatisms.length; i++){
                var auto = dashboard.automatisms[i]
                html += auto.name + "(c:"+auto.complexity+", w:"+auto.competence+") <br />"
            }
            html += "</td><tr>"
        }

        html += "</table>"
        datatable.html(html);
        if(dashboard.concepts && dashboard.concepts.total){
            draw_circle_chart(data, '#concept_graph', dashboard.concepts.total, 80, 5);
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

    function drawBarChart(data, selector){

            d3graphs[selector] = {};
            var margin = {top: 20, right: 20, bottom: 70, left: 40},
                width = 500 - margin.left - margin.right,
                height = 250 - margin.top - margin.bottom;

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

            }

            var ymin = 0;
            var ymax = 1;
            for(var i=0; i < data.length; i++){
                data[i].value = Math.max(0, data[i].value);
                if(data[i].value < ymin) ymin = data[i].value;
                else if(data[i].value > ymax) ymax = data[i].value;
            }
            x.domain(data.map(function(d) { return d.name; }));
            y.domain([ymin, ymax]);

            svg.select(".y.axis")
                .call(yAxis)
                .selectAll("text")
                .style("font-size", "80%")

            svg.select(".x.axis")
                .call(xAxis)
                .selectAll("text")
                .style("font-size", "80%");


            var bars = svg.selectAll('.bar')
                .data(data)
            //update
            bars
                .attr("fill", "#009")

            //enter
            bars.enter()
                .append("svg:rect")
                .attr("class", "bar")
                .attr("fill", "#900")


            //exit
            bars.exit()
            .transition()
            .duration(300)
            .ease("exp")
                .attr("height", 0)
                .remove()

            bars
            .transition()
            .duration(300)
            .ease("quad")
               .style("fill", function(d) { return d.color})
               .attr("x", function(d) { return x(d.name); })
               .attr("width", x.rangeBand())
               .attr("y", function(d) { return y(d.value); })
               .attr("height", function(d) { return height - y(d.value); });

           svg.selectAll('g.x.axis g text').each(insertLinebreaks);
    }

    var piecharts = {}



    function draw_circle_chart(data, selector, label, height, margin){

        var values = [];
        for(var i = 0; i < data.length; i++){
            values.push(data[i].value);
        }
        //Width and height
        var margin = margin || 20;
        var h = height || 180;
        var w = h - margin;

        var outerRadius = w / 2;
        var innerRadius = w / 3;
        var arc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(outerRadius);


        function arcTween(a) {
          var i = d3.interpolate(this._current, a);
          this._current = i(0);
          return function(t) {
            return arc(i(t));
          };
        }

        var svg = d3.select(selector).select("svg");
        if(!svg.empty() && piecharts[selector]){

            var text = svg.select("text");
            var pie = piecharts[selector]['pie']
            text.text(label)
            pie.value(function(d, i){return values[i]})
            path = piecharts[selector]['path'].data(pie); // compute the new angles
            path.transition().duration(750).attrTween("d", arcTween); // redraw the arcs
            return
        }

        piecharts[selector] = {}

        var pie = d3.layout.pie()
                    .value(function(d, i){return values[i]});

        piecharts[selector]['pie'] = pie;

        //Create SVG element
        var svg = d3.select(selector)
                    .append("svg")
                    .attr("width", w + margin)
                    .attr("height", h + margin);

        piecharts[selector]['path'] = svg.datum(values).selectAll("path")
                      .data(pie)
                      .enter()
                      .append("path")
                      .attr("class", "arc")
                      .attr("d", arc)
                      .attr("fill", function(d, i) {
                        return data[i].color;
                      })
                      .each(function(d) { this._current = d; })
                      .attr("transform", "translate(" + (outerRadius + margin) +"," + (outerRadius + margin) + ")")

        svg.append("text")
            .text(label)
            .style("text-anchor", "left")
            .attr("dx", w/2 - margin/1.5)
            .attr("dy", h/2 + margin/1.5)
    }

    function draw_face(data, selector){
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
                .attr("xlink:href", "/static/face/stevehead.png")
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

        lip_presser = lip_presser
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