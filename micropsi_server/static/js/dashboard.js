

$(function(){

    var container = $('#dashboard_container');

    var urges = $('<div id="dashboard_urges" class="dashboard-item"></div>');
    var modulators = $('<div id="dashboard_modulators" class="dashboard-item"></div>');
    var nodes = $('<div id="dashboard_nodes" class="dashboard-item"></div>');
    var datatable = $('<div id="dashboard_datatable" class="dashboard-item"></div>');
    var sensors = $('<div id="dashboard_sensors" class="dashboard-item"></div>');

    container.append(urges, modulators, nodes, datatable, sensors, $('<p style="break:both"></p>'));


    function getPollParams(){
        return 1
    }

    function setData(data){
        draw_urges(data);
        draw_modulators(data);
        draw_nodes(data);
        draw_datatable(data);
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
        modulators.html('');
        var data = [];
        for(var key in dashboard.modulators){
            if(key in colors){
                data.push({'name': key.substr(4).replace('_', ' '), 'value': dashboard.modulators[key], 'color': colors[key]});
            }
        }
        drawBarChart(data, '#dashboard_modulators');
    }

    function draw_nodes(dashboard){
        var total = parseInt(dashboard['count_nodes'])
        var data = [
            {'value': dashboard['count_negative_nodes'], 'name': 'failing', 'color': 'red'},
            {'value': dashboard['count_positive_nodes'], 'name': 'success', 'color': 'green'},
            {'value': total - dashboard['count_negative_nodes'] - dashboard['count_negative_nodes'], name: 'off', color: 'grey'}
        ];
        var label = total + " Nodes"
        nodes.html('');
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
        urges.html('');
        var data = [];
        for(var key in dashboard.urges){
            data.push({'name': key, 'value': dashboard.urges[key], 'color': colors[key]});
        }
        drawBarChart(data, '#dashboard_urges')
    }

    function draw_datatable(dashboard){
        var html = '<table class="table-condensed table-striped dashboard-table">';

        if(dashboard.motive){
            html += "<tr><th><strong>Motive:</strong></th><th>"+dashboard.motive.motive+"</th></tr>"
            html += "<tr><td>Weight:</td><td>"+dashboard.motive.weight+"</td></tr>"
            html += "<tr><td>Gain:</td><td>"+dashboard.motive.gain+"</td></tr>"
        }
        html += "<tr><th><strong>Action:</strong></th><th>"+dashboard.action+"</th></tr>"

        html += "<tr><th><strong>sec/step:</strong></th><th>"+dashboard.stepping_rate+"</th></tr>"

        html += "</table>"
        datatable.html(html);
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

        var svg = d3.select(selector).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform",
                  "translate(" + margin.left + "," + margin.top + ")");

        x.domain(data.map(function(d) { return d.name; }));
        var ymin = 0;
        var ymax = 1;
        for(var i=0; i < data.length; i++){
            if(data[i].value < ymin) ymin = data[i].value;
            else if(data[i].value > ymax) ymax = data[i].value;
        }
        y.domain([ymin, ymax]);

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

        svg.selectAll("bar")
            .data(data)
          .enter().append("rect")
            .style("fill", function(d) { return d.color})
            .attr("x", function(d) { return x(d.name); })
            .attr("width", x.rangeBand())
            .attr("y", function(d) { return y(d.value); })
            .attr("height", function(d) { return height - y(d.value); });
        svg.selectAll('g.x.axis g text').each(insertLinebreaks);
    }

    function draw_circle_chart(data, selector, label){
        //Width and height
        var margin = 20;

        var w = 160;
        var h = 180;

        var outerRadius = w / 2;
        var innerRadius = w / 3;
        var arc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(outerRadius);

        var pie = d3.layout.pie();

        //Create SVG element
        var svg = d3.select(selector)
                    .append("svg")
                    .attr("width", w + 20)
                    .attr("height", h + 20);

        //Set up groups
        var values = [];
        for(var i = 0; i < data.length; i++){
            values.push(data[i].value);
        }
        var arcs = svg.selectAll("g.arc")
                      .data(pie(values))
                      .enter()
                      .append("g")
                      .attr("class", "arc")
                      .attr("transform", "translate(" + (outerRadius + margin) +"," + (outerRadius + margin) + ")")

        //Draw arc paths
        arcs.append("path")
            .attr("fill", function(d, i) {
                return data[i].color;
            })
            .attr("d", arc);
        arcs.append("text")
            .text(label)
            .style("text-anchor", "middle")
    }

});