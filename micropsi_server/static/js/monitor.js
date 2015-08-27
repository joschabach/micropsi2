
$(function(){

    var viewProperties = {
        height: 420,
        padding: 20,
        xvalues: 100,
        max_log_entries: 2000
    };

    var container = $('#graph');
    var svg = null;

    var nodenetMonitors = {};
    var currentMonitors = [];

    var currentSimulationStep = 0;
    var currentNodenet = $.cookie('selected_nodenet');

    var capturedLoggers = {
        'system': false,
        'world': false,
        'agent': false
    };

    var logs = [];

    if($.cookie('capturedLoggers')){
        capturedLoggers = JSON.parse($.cookie('capturedLoggers'));
    }
    if($.cookie('currentMonitors')){
        currentMonitors = JSON.parse($.cookie('currentMonitors'));
    }

    var last_logger_call = 0;

    var log_container = $('#logs');

    var fixed_position = null;

    init();

    $('.layoutbtn').on('click', function(event){
        event.preventDefault();
        var target = $(event.target);
        if(!target.hasClass('active')){
            var layout = target.attr('data');
            if(layout == 'vertical'){
                $('.layout_field').addClass('span6');
            } else if(layout == 'horizontal'){
                $('.layout_field').removeClass('span6');
            }
            refreshMonitors();
            $('.layoutbtn').removeClass('active');
            target.addClass('active');
        }
    })

    $('#monitor_x_axis').on('change', function(){
        viewProperties.xvalues = parseInt($('#monitor_x_axis').val());
        refreshMonitors();
    });

    var filter_timeout=null;
    $('#monitor_filter_logs').on('keydown', function(event){
        if(event.keyCode == 13){
            event.preventDefault();
        }
        clearTimeout(filter_timeout);
        filter_timeout = setTimeout(refreshLoggerView, 400);
    })

    $(document).on('monitorsChanged', function(evt, new_monitor){
        currentMonitors.push(new_monitor)
        refreshMonitors();
    });
    $(document).on('nodenet_changed', function(data, newNodenet){
        currentNodenet = newNodenet;
        init();
    });

    log_container.on('click', '.logentry', function(event){
        var el = $(this)
        var step = el.attr('data-step');
        if(el.hasClass('highlight')){
            el.removeClass('highlight');
            fixed_position = null;
            drawGraph(nodenetMonitors);
        } else {
            $('.logentry').removeClass('highlight');
            if(step && parseInt(step)){
                fixed_position = parseInt(step);
                drawGraph(nodenetMonitors);
                $(this).addClass('highlight');
            }
        }
    });


    function init() {
        bindEvents();
        if (currentNodenet = $.cookie('selected_nodenet')) {
            $('#loading').show();
            api.call('load_nodenet', {
                nodenet_uid: currentNodenet,
                include_links: false
            }, function(data) {
                $('#loading').hide();
                refreshMonitors();
            },
            function(data) {
                $('#loading').hide();
                if(data.status == 500){
                    api.defaultErrorCallback(data);
                } else {
                    currentNodenet = null;
                    $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
                    dialogs.notification(data.data, "Info");
                }
            });
        }
    }

    function getPollParams(){
        var poll = [];
        for(var logger in capturedLoggers){
            if(capturedLoggers[logger]){
                var name = logger;
                if(logger == 'agent') name = "agent." + currentNodenet;
                poll.push(name);
            }
        }
        return {
            logger: poll,
            after: last_logger_call
        }
    }

    function setData(data){
        currentSimulationStep = data.current_step;
        setMonitorData(data);
        setLoggingData(data);
    }

    register_stepping_function('monitors', getPollParams, setData);

    function refreshMonitors(newNodenet){
        params = getPollParams();
        if(newNodenet || currentNodenet){
            params.nodenet_uid = newNodenet || currentNodenet;
            api.call('get_monitoring_info', params, setData);
        }
    }

    function setMonitorData(data){
        updateMonitorList(data.monitors);
        nodenetMonitors = data.monitors;
        drawGraph(nodenetMonitors);
    }

    function setLoggingData(data){
        last_logger_call = data.logs.servertime;
        for(var idx in data.logs.logs){
            if(data.logs.logs[idx].logger.indexOf("agent.") > -1){
                data.logs.logs[idx].logger = "agent";
            }
            logs.push(data.logs.logs[idx]);
        }
        if(logs.length > viewProperties.max_log_entries){
            logs.splice(0, logs.length - viewProperties.max_log_entries);
        }
        if(!fixed_position){
            refreshLoggerView();
        }
    }

    function refreshLoggerView(){
        var height = log_container.height();
        var scrollHeight = log_container[0].scrollHeight;
        var st = log_container.scrollTop();
        var doscroll = (st >= (scrollHeight - height));
        var html = '';
        var filter = $('#monitor_filter_logs').val().toLowerCase();
        for(var idx in logs){
            item = logs[idx];
            if(filter){
                var check = (item.logger + item.msg + item.module+ item.function + item.level).toLowerCase();
                if(check.indexOf(filter) > -1){
                    html += '<span class="logentry log_'+item.level+'" data-step="'+(item.step||'')+'">'+("          " + item.logger).slice(-10)+' | ' + item.msg +'</span>';
                }
            } else {
                html += '<span class="logentry log_'+item.level+'" data-step="'+(item.step||'')+'">'+("          " + item.logger).slice(-10)+' | ' + item.msg +'</span>';
            }
        }
        log_container.html(html);
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
            var data = {'logging_levels': {}}
            data['logging_levels'][el.attr('data')] = el.val();
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
        var sorted = Object.values(monitors);
        sorted.sort(sortByName);
        for(var i = 0; i < sorted.length; i++){
            var mon = sorted[i];
            html += '<li><input type="checkbox" class="monitor_checkbox" value="'+mon.uid+'" id="'+mon.uid+'"';
            if(currentMonitors.indexOf(mon.uid) > -1){
                html += ' checked="checked"';
            }
            html += ' /> <label for="'+mon.uid+'" style="display:inline;color:'+mon.color+'"><strong>' + mon.name + '</strong></label> <a href="#" class="delete_monitor" title="delete monitor" data="'+mon.uid+'"><i class="icon-trash"></i></a></li>';
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
                    refreshMonitors();
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
        $.cookie('currentMonitors', JSON.stringify(currentMonitors), {path:'/', expires:7})
        refreshMonitors();
    }

    function drawGraph(monitors) {

        var position = fixed_position;
        var customMonitors = false;
        container.html(''); // TODO: come up with a way to redraw
        var margin = {
                top: 20,
                right: 50,
                bottom: 30,
                left: 50
            };
        var width = container.width() - margin.left - margin.right - viewProperties.padding;
        var height = viewProperties.height - margin.top - margin.bottom - viewProperties.padding;

        var xmax = Math.max(viewProperties.xvalues, currentSimulationStep);
        if(position && xmax > viewProperties.xvalues){
            xmax = Math.min(position + (viewProperties.xvalues/2), xmax);
            if(xmax - viewProperties.xvalues < 0) {
                xmax -= (xmax - viewProperties.xvalues)
            }
        }

        var xvalues = viewProperties.xvalues;
        if(viewProperties.xvalues < 0){
            xvalues = xmax;
        }
        var x = d3.scale.linear()
            .domain([xmax - xvalues, xmax])
            .range([0, width]);
        var xstart = xmax - xvalues;

        var y1values = [];
        var y2values = [];
        var y1max = 1.0;
        var y1min = 0;
        var y2max = 1.0;
        var y2min = 0;
        for (var idx in currentMonitors) {
            var uid = currentMonitors[idx];
            for (var step in monitors[uid].values) {
                if(monitors[uid].classname == 'CustomMonitor'){
                    customMonitors = true;
                    y2values.push(monitors[uid].values[step]);
                    if (step >= xstart && step <= xmax) {
                        y2max = Math.max(y2max, monitors[uid].values[step]);
                        y2min = Math.min(y2min, monitors[uid].values[step]);
                    }
                } else {
                    y1values.push(monitors[uid].values[step]);
                    if (step >= xstart && step <= xmax) {
                        y1max = Math.max(y1max, monitors[uid].values[step]);
                        y1min = Math.min(y1min, monitors[uid].values[step]);
                    }
                }
            }
        }

        var y1 = d3.scale.linear().domain([y1min, y1max]).range([height, 0]);
        var y2 = d3.scale.linear().domain([y2min, y2max]).range([height, 0]);

        var x_axis_pos = (y1max / (y1max - y1min)) * height;

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var y1Axis = d3.svg.axis()
            .scale(y1)
            .orient("left");
        var y2Axis = d3.svg.axis()
            .scale(y2)
            .orient("right");

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
            .call(y1Axis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Activation");
        if(position){
            svg.append('line')
                .attr('x1', x(position))
                .attr('y1', 0)
                .attr('x2', x(position))
                .attr('y2', x_axis_pos)
                .attr('stroke-width', 0.5)
                .attr('stroke', '#999');
            svg.append('text')
                .attr('x', x(position))
                .attr('y', 0)
                .text(position)
                .attr('font-size', '10px')
                .attr('font-family', 'monospace')
                .attr('fill', 'black')
        }
        if(customMonitors){
            svg.append("g")
                .attr("class", "y axis")
                .call(y2Axis)
                .attr("transform", "translate(" + width + " ,0)")
                .append("text")
                .attr("transform", "rotate(-90)")
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "end")
                .text("Value");
        }

        for (var idx in currentMonitors) {
            var uid = currentMonitors[idx];
            var data = [];
            if(monitors[uid].classname == 'CustomMonitor'){
                var line = d3.svg.line()
                    .x(function(d) {
                        return x(d[0]);
                    })
                    .y(function(d) {
                        return y2(d[1]);
                    })
                    .defined(function(d){ return d[1] == 0 || Boolean(d[1])});
                for (var step in monitors[uid].values) {
                    step = parseInt(step, 10);
                    if(step >= xstart && step <= xmax){
                        data.push([step, parseFloat(monitors[uid].values[step])]);
                    }
                }
                var points = svg.selectAll(".point")
                    .data(data)
                    .enter().append("svg:circle")
                     .attr("stroke", "black")
                     .attr("fill", function(d, i) { return  monitors[uid].color })
                     .attr("cx", function(d, i) { return x(d[0]); })
                     .attr("cy", function(d, i) { return y2(d[1]); })
                     .attr("r", function(d) {
                        return ((position && d[0] == position) ? 4 : 2);
                      });

            } else {
                var line = d3.svg.line()
                    .x(function(d) {
                        return x(d[0]);
                    })
                    .y(function(d) {
                        return y1(d[1]);
                    })
                    .defined(function(d){
                        return d[1] == 0 || Boolean(d[1])
                    });
                for (var step in monitors[uid].values) {
                    step = parseInt(step, 10);
                    if(step >= xstart && step <= xmax){
                        data.push([step, parseFloat(monitors[uid].values[step])]);
                    }
                }
                var points = svg.selectAll(".point")
                    .data(data)
                    .enter().append("svg:circle")
                     .attr("fill", function(d, i) { return monitors[uid].color })
                     .attr("cx", function(d, i) { return x(d[0]); })
                     .attr("cy", function(d, i) { return y1(d[1]); })
                     .attr("r", function(d) {
                        return ((position && d[0] == position) ? 4 : 2);
                      });
            }

            var color =  monitors[uid].color;
            svg.append("path")
                .datum(data)
                .attr("class", "line")
                .attr("stroke", color)
                .attr("transform", "translate(0,0)")
                .attr("d", line);
        }
    }

});
