
$(function(){

    var viewProperties = {
        height: 420,
        padding: 20,
        xvalues: 100
    };

    var container = $('#graph');
    var svg = null;

    var nodenetMonitors = {};
    var currentMonitors = [];

    var currentNodenet = null;

    var nodenet_running = false;

    var capturedLoggers = {
        'system': false,
        'world': false,
        'nodenet': false
    };

    if($.cookie('capturedLoggers')){
        capturedLoggers = JSON.parse($.cookie('capturedLoggers'));
    }

    var last_logger_call = 0;

    var log_container = $('#logs');

    init();

    $(document).on('monitorsChanged', function(){
        if(!nodenet_running){
            pollMonitoringData();
        }
    });
    $(document).on('nodenetStepped', function(){
        if(!nodenet_running){
            pollMonitoringData();
        }
    });
    $(document).on('nodenetChanged', function(data, newNodenet){
        currentNodenet = newNodenet;
        pollMonitoringData();
    });


    function init() {
        bindEvents();
        if (currentNodenet = $.cookie('selected_nodenet')) {
            api.call('load_nodenet', {
                nodenet_uid: currentNodenet,
                x1: 0,
                x2: 0,
                y1: 0,
                y2: 0
            }, function(data) {
                nodenetMonitors = data.monitors;
                currentMonitors = Object.keys(nodenetMonitors);
                currentSimulationStep = data.step;
                nodenet_running = data.is_active;
                pollMonitoringData();
            },
            function(data) {
                if(data.status == 500){
                    api.defaultErrorCallback(data);
                } else {
                    currentNodenet = null;
                    $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
                    dialogs.notification(data.Error, "Info");
                }
            });
        }
    }

    function pollMonitoringData(){
        var poll = [];
        for(var logger in capturedLoggers){
            if(capturedLoggers[logger]){
                poll.push(logger);
            }
        }
        api.call('get_monitoring_info', {
            nodenet_uid: currentNodenet,
            logger: poll,
            after: last_logger_call
        }, function(data){
            setMonitorData(data);
            setLoggingData(data);
            nodenet_running = data.nodenet_running;
            currentSimulationStep = data.current_step;
            if(nodenet_running){
                window.setTimeout(pollMonitoringData, 500);
            } else {
                pollActive();
            }

        })
    }

    function pollActive(){
        api.call('get_is_nodenet_running', {nodenet_uid: currentNodenet}, function(data){
            nodenet_running = data.nodenet_running;
            if(nodenet_running){
                pollMonitoringData();
            }
            if(!nodenet_running){
                window.setTimeout(pollActive, 4000);
            }
        }, function(){
            console.warn('server offline. can not determine nodenet state');
        });
    }

    function setMonitorData(data){
        updateMonitorList(data.monitors);
        nodenetMonitors = data.monitors;
        var m = {};
        for (var uid in nodenetMonitors) {
            if (currentMonitors.indexOf(uid) >= 0) {
                m[uid] = nodenetMonitors[uid];
            }
        }
        drawGraph(m);
    }

    function setLoggingData(data){
        var height = log_container.height();
        var scrollHeight = log_container[0].scrollHeight;
        var st = log_container.scrollTop();
        var doscroll = (st >= (scrollHeight - height));
        last_logger_call = data.logs.servertime;
        for(var idx in data.logs.logs){
            log_container.append($('<span class="logentry log_'+data.logs.logs[idx].level+'">'+data.logs.logs[idx].logger+' | ' + data.logs.logs[idx].msg +'</span>'));
        }
        if(doscroll){
            log_container.scrollTop(log_container[0].scrollHeight);
        }
    }

    function bindEvents(){
        $('.log_switch').on('change', function(event){
            var el = $(event.target);
            capturedLoggers[el.attr('data')] = el.attr('checked')
            $.cookie('capturedLoggers', JSON.stringify(capturedLoggers), {path:'/', expires:7})
        });
        $('.log_level_switch').on('change', function(event){
            var el = $(event.target);
            var data = {}
            data[el.attr('data')] = el.val();
            api.call('set_logging_levels', data);
        });
        $('.log_switch').each(function(idx, el){
            if(capturedLoggers[$(el).attr('data')]){
                el.checked=true;
            }
        });
    }

    function updateMonitorList(monitors){
        var list = $('#monitor_selector');
        var html = '';
        for(var uid in monitors){
            html += '<li><input type="checkbox" class="monitor_checkbox" value="'+uid+'" id="'+uid+'"';
            if(currentMonitors.indexOf(uid) > -1){
                html += ' checked="checked"';
            }
            html += ' /> <label for="'+uid+'" style="display:inline;color:#'+uid.substr(2,6)+'"><strong>' + monitors[uid].type + ' ' + monitors[uid].target + '</strong> @ Node ' + (monitors[uid].node_name || monitors[uid].node_uid) + '</label> <a href="#" class="delete_monitor" title="delete monitor" data="'+uid+'"><i class="icon-trash"></i></a></li>';
        }
        list.html(html);
        $('.monitor_checkbox', list).on('change', updateMonitorSelection);
        $('.delete_monitor', list).on('click', function(event){
            event.preventDefault();
            api.call(
                'remove_monitor',
                {nodenet_uid: currentNodenet, monitor_uid: $(event.delegateTarget).attr('data')},
                function(){
                    delete monitors[uid];
                    updateMonitorList();
                }
            );
        });
    }

    function updateMonitorSelection() {
        currentMonitors = [];
        $.each($('.monitor_checkbox'), function(idx, el) {
            if (el.checked) {
                currentMonitors.push(el.value);
            }
        });
    }

    function drawGraph(currentMonitors) {

        container.html(''); // TODO: come up with a way to redraw
        var margin = {
                top: 20,
                right: 20,
                bottom: 30,
                left: 50
            },
            width = container.width() - margin.left - margin.right - viewProperties.padding,
            height = viewProperties.height - margin.top - margin.bottom - viewProperties.padding;

        var xmax = Math.max(viewProperties.xvalues, currentSimulationStep);
        var x = d3.scale.linear()
            .domain([xmax - viewProperties.xvalues, xmax])
            .range([0, width]);

        var values = [];
        var xstart = xmax - viewProperties.xvalues;
        var ymax = 1.0;
        var ymin = 0;
        for (var uid in currentMonitors) {
            for (var step in currentMonitors[uid].values) {
                values.push(currentMonitors[uid].values[step]);
                if (step >= xstart) {
                    ymax = Math.max(ymax, currentMonitors[uid].values[step]);
                    ymin = Math.min(ymin, currentMonitors[uid].values[step]);
                }
            }
        }

        var y = d3.scale.linear().domain([ymin, ymax]).range([height, 0]);

        var x_axis_pos = (ymax / (ymax - ymin)) * height;

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
            .attr("transform", "translate(0," + x_axis_pos + ")")
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

        for (var uid in currentMonitors) {
            var line = d3.svg.line()
                .x(function(d) {
                    return x(d[0]);
                })
                .y(function(d) {
                    return y(d[1]);
                });
            var data = [];
            for (var step in currentMonitors[uid].values) {
                data.push([parseInt(step, 10), parseFloat(currentMonitors[uid].values[step])]);
            }
            var len = data.length;
            data.splice(0, len - viewProperties.xvalues - 1);
            var color = '#' + uid.substr(2, 6);
            svg.append("path")
                .datum(data)
                .attr("class", "line")
                .attr("stroke", color)
                .attr("d", line);
        }
    }

});
