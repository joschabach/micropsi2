
var viewProperties = {
    height: 300,
    padding: 20,
    xvalues: 100
};

var container = $('#graph');
var svg = null;
var currentMonitors = [];

function updateMonitorGraphs(){
    if(currentMonitors.length){
      api.call('export_monitor_data', {
        nodenet_uid: currentNodenet
      }, function(data){
          var m = {};
          for(var uid in data){
            if(currentMonitors.indexOf(uid) >= 0){
              m[uid] = data[uid];
            }
          }
          drawGraph(m);
      });
    } else {
      container.html('');
    }
}

function updateMonitorSelection(){
    currentMonitors = [];
    $.each($('.monitor_checkbox'), function(idx, el){
      if(el.checked){
        currentMonitors.push(el.value);
      }
    });
    updateMonitorGraphs();
}

function drawGraph(currentMonitors){

    container.html(''); // TODO: come up with a way to redraw
    var margin = {top: 20, right: 20, bottom: 30, left: 50},
        width = container.width() - margin.left - margin.right - viewProperties.padding,
        height = viewProperties.height - margin.top - margin.bottom - viewProperties.padding;

    var xmax = Math.max(viewProperties.xvalues, currentSimulationStep);
    var x = d3.scale.linear()
        .domain([xmax-viewProperties.xvalues, xmax])
        .range([0, width]);

    var values = [];
    var xstart = xmax-viewProperties.xvalues;
    var ymax = 1.0;
    for(var uid in currentMonitors){
      for(var step in currentMonitors[uid].values){
        values.push(currentMonitors[uid].values[step]);
        if(step >= xstart && currentMonitors[uid].values[step] > ymax){
          ymax = currentMonitors[uid].values[step];
        }
      }
    }

    var y = d3.scale.linear().domain([0, ymax]).range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

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

    for(var uid in currentMonitors){
      var line = d3.svg.line()
          .x(function(d) { return x(d[0]); })
          .y(function(d) { return y(d[1]); });
      var data = [];
      for(var step in currentMonitors[uid].values){
        data.push([parseInt(step, 10), parseFloat(currentMonitors[uid].values[step])]);
      }
      var len = data.length;
      data.splice(0, len-viewProperties.xvalues-1);
      var color = '#' + uid.substr(2,6);
      svg.append("path")
        .datum(data)
        .attr("class", "line")
        .attr("stroke", color)
        .attr("d", line);
    }
  }
