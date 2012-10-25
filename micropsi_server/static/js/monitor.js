
var viewProperties = {
    height: 300,
    padding: 20
};

var container = $('#graph');
var currentMonitor = null;
var svg = null;

var monitor = {
  showMonitorGraph: function (event){
    event.preventDefault();
    var link = $(event.target);
    currentMonitor = monitors[link.attr('data')];
    monitor.drawGraph(currentMonitor);
  },

  updateMonitorGraph: function (){
    if(currentMonitor){
      api.call('export_monitor_data', {
        nodenet_uid: currentNodenet,
        monitor_uid: currentMonitor.uid
      }, function(data){
          monitors[monitor.uid] = data;
          currentMonitor = monitors[monitor.uid];
          monitor.drawGraph(currentMonitor);
      });
    }
  },

  drawGraph: function(selectedMonitor){

    container.html(''); // TODO: come up with a way to redraw

    var margin = {top: 20, right: 20, bottom: 30, left: 50},
        width = container.width() - margin.left - margin.right - viewProperties.padding,
        height = viewProperties.height - margin.top - margin.bottom - viewProperties.padding;

    data = [];
    for(var xvalue in selectedMonitor.values){
        data.push([parseInt(xvalue, 10), parseFloat(selectedMonitor.values[xvalue])]);
    }
    var x = d3.scale.linear()
        .domain([0, d3.max(data, function(d) { return d[0]; })])
        .range([0, width]);

    var y = d3.scale.linear().range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    var line = d3.svg.line()
        .x(function(d) { return x(d[0]); })
        .y(function(d) { return y(d[1]); });

    svg = d3.select("#graph").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
    .append("text")
      .attr("dx", width - 100)
      .attr("dy", -5)
      .style("text-anchor", "start")
      .text("Nodenet step");
    svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Activation");

    svg.append("path")
      .datum(data)
      .attr("class", "line")
      .attr("d", line);

  }
};