
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
    var currentNodenet = '';
    var cookieval = $.cookie('selected_nodenet');
    if (cookieval && cookieval.indexOf('/')){
        currentNodenet = cookieval.split('/')[0];
    }

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
    var showStepInLog = true;
    var logs_to_add = [];

    init();

    if(!$('#nodenet_editor').length && currentNodenet){
        refreshMonitors();
    }

    var splitviewclass = 'span4';

    var count_sections = $('.layout_field').length;
    $('.layoutbtn').on('click', function(event){
        event.preventDefault();
        var target = $(event.target);
        if(!target.hasClass('active')){
            var layout = target.attr('data');
            if(layout == 'vertical'){
                $('.layout_field').addClass(splitviewclass);
            } else if(layout == 'horizontal'){
                $('.layout_field').removeClass(splitviewclass);
            }
            refreshMonitors();
            $('.layoutbtn').removeClass('active');
            target.addClass('active');
        }
    })
    $('.layoutbtn[data="vertical"]').trigger('click');

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
        refreshMonitors();
    });
    $(document).on('nodenet_loaded', function(data, newNodenet){
        currentNodenet = newNodenet;
        refreshMonitors();
    });

    log_container.on('click', '.logentry', function(event){
        var el = $(this)
        var step = el.attr('data-step');
        if(el.hasClass('highlight')){
            el.removeClass('highlight');
            fixed_position = null;
            refreshMonitors();
        } else {
            $('.logentry').removeClass('highlight');
            if(step && parseInt(step)){
                fixed_position = parseInt(step);
                refreshMonitors();
                $(this).addClass('highlight');
            }
        }
    });

    var monitor_list_items = [];

    function init() {
        bindEvents();
    }

    function getPollParams(){
        var poll = [];
        for(var logger in capturedLoggers){
            if(capturedLoggers[logger]){
                var name = logger;
                if(logger == 'agent') {
                    name = "agent." + currentNodenet;
                }
                poll.push(name);
            }
        }
        var params = {
            logger: poll,
            after: last_logger_call,
            monitor_count: viewProperties.xvalues
        }
        if(fixed_position){
            params['monitor_from'] = Math.max(fixed_position - (viewProperties.xvalues / 2), 1);
        }
        return params;
    }

    function setData(data){
        currentSimulationStep = data.current_step;
        setMonitorData(data);
        setLoggingData(data);
        setStatusData(data);
    }

    if($('#monitor').height() > 0){
        register_stepping_function('monitors', getPollParams, setData);
    }
    $('#monitor').on('shown', function(){
        register_stepping_function('monitors', getPollParams, setData);
        if(!calculationRunning){
            $(document).trigger('runner_stepped');
        }
    });
    $('#monitor').on('hidden', function(){
        unregister_stepping_function('monitors');
    });


    function refreshMonitors(newNodenet){
        params = getPollParams();
        if(newNodenet || currentNodenet){
            params.nodenet_uid = newNodenet || currentNodenet;
            api.call('get_monitoring_info', params, setData);
        }
    }

    function setMonitorData(data){
        if(data.monitors){
            updateMonitorList(data.monitors);
            nodenetMonitors = data.monitors;
            drawGraph(nodenetMonitors);
        }
    }

    function setLoggingData(data){
        last_logger_call = data.logs.servertime;
        for(var idx in data.logs.logs){
            if(data.logs.logs[idx].logger.indexOf("agent.") > -1){
                data.logs.logs[idx].logger = "agent";
            }
            logs.push(data.logs.logs[idx]);
            logs_to_add.push(data.logs.logs[idx]);
        }
        if(!fixed_position){
            addLoggerMessages(logs_to_add);
            logs_to_add = [];
        }
        if(logs.length > viewProperties.max_log_entries){
            logs.splice(0, logs.length - viewProperties.max_log_entries);
        }
    }

    function sortfunc(a, b){
        if(a < b) return -1;
        if(a > b) return 1;
        return 0;
    };

    function setStatusData(data){
        var table = $('#status_table');
        table.html();
        var html = [];

        function fill_html(data, level){
            var sorted_keys = Object.keys(data);
            sorted_keys.sort(sortfunc);
            for(var i = 0; i < sorted_keys.length; i++){
                entry = data[sorted_keys[i]];
                html.push(
                    '<tr><td>',
                    "&nbsp;".repeat(level * 3),
                    sorted_keys[i],
                    '</td><td>')
                if(entry.state){
                    html.push('<i class="status_indicator ',
                        entry.state.replace(' ', ''),
                        '" title="', entry.state, '" ',', />')
                } else {
                    html.push("&nbsp;");
                }
                html.push(
                    '</td><td>',
                    entry.msg || "&nbsp;",
                    '</td><td>');
                if(entry.progress){
                    html.push(
                        entry.progress[0] || "?",
                        ' / ',
                        entry.progress[1] || "?",
                    );
                }
                else {
                    html.push("&nbsp;");
                }
                html.push('</td></tr>');
                if(Object.keys(entry.children).length){
                    fill_html(entry.children, level+1);
                }
            }
        }
        fill_html(data.status, 0)
        table.html(html.join(''));
    }

    function refreshLoggerView(){
        log_container.html('');
        addLoggerMessages(logs);
    }

    function addLoggerMessages(data_to_add){
        var height = log_container.height();
        var scrollHeight = log_container[0].scrollHeight;
        var st = log_container.scrollTop();
        var doscroll = (st >= (scrollHeight - height));
        var html = '';
        var filter = $('#monitor_filter_logs').val().toLowerCase();
        var pad = String(currentSimulationStep).length;
        var space = "               ";  // spaces for padding.
        for(var idx in data_to_add){
            item = data_to_add[idx];
            if(filter){
                var check = (item.logger + item.msg + item.module+ item.function + item.level).toLowerCase();
                if(check.indexOf(filter) > -1){
                    html += '<span class="logentry log_'+item.level+'" data-step="'+(item.step||'')+'">'+
                    ((showStepInLog && !isNaN(parseInt(item.step))) ? (space+item.step).slice(-pad) : (space).slice(-pad)) +
                    (space + item.logger).slice(-8) +' | ' + item.msg + '</span>';
                }
            } else {
                html += '<span class="logentry log_'+item.level+'" data-step="'+(item.step||'')+'">'+
                ((showStepInLog && !isNaN(parseInt(item.step))) ? (space+item.step).slice(-pad) : (space).slice(-pad)) +
                (space + item.logger).slice(-8) +' | ' + item.msg + '</span>';
            }
        }

        log_container.append(html);
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
            if(el.attr('data') == "agent" && currentNodenet){
                data['logging_levels']['agent.' + currentNodenet] = el.val();
            } else {
                data['logging_levels'][el.attr('data')] = el.val();
            }
            api.call('set_logging_levels', data);
        });
        $('.log_switch').each(function(idx, el){
            if(capturedLoggers[$(el).attr('data')]){
                el.checked=true;
            }
        });
        $('#clear_logs').on('click', function(event){
            event.preventDefault();
            logs = [];
            refreshLoggerView();
        });
    }

    function updateMonitorList(monitors){
        var list = $('#monitor_selector');
        var html = '';
        var sorted = Object.values(monitors);
        sorted.sort(sortByName);
        var keys = Object.keys(monitors);
        var changed = $(keys).not(monitor_list_items).length != 0 || $(monitor_list_items).not(keys).length != 0;
        if(!changed){
            return;
        }
        monitor_list_items = [];
        var els = $('.monitor');
        for(var i = 0; i < sorted.length; i++){
            var mon = sorted[i];
            html += '<li><input type="checkbox" class="monitor_checkbox" value="'+mon.uid+'" id="'+mon.uid+'"';
            if(currentMonitors.indexOf(mon.uid) > -1){
                html += ' checked="checked"';
            }
            html += ' /> <label for="'+mon.uid+'" style="display:inline;color:'+mon.color+'"><strong>' + mon.name + '</strong></label>';
            html += ' <a href="#" class="delete_monitor monitor_action" title="delete monitor" data="'+mon.uid+'"><i class="icon-trash"></i></a></li>';
            monitor_list_items.push(mon.uid);
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
            if(!monitors[uid]) continue;
            for (var step in monitors[uid].values) {
                if(monitors[uid].classname == 'CustomMonitor'){
                    customMonitors = true;
                    y2values.push(monitors[uid].values[step]);
                    if (step >= xstart && step <= xmax) {
                        y2max = Math.max(y2max, monitors[uid].values[step]);
                        y2min = Math.min(y2min, monitors[uid].values[step]);
                    }
                } else if(monitors[uid].classname == 'GroupMonitor'){
                    y1values.concat(monitors[uid].values[step]);
                    if (step >= xstart && step <= xmax) {
                        y1max = Math.max(y1max, Math.max.apply(Math, monitors[uid].values[step]));
                        y1min = Math.min(y1min, Math.min.apply(Math, monitors[uid].values[step]));
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
            if(!monitors[uid]) continue;
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
                    .filter(function(d, i){ return d[1] == 0 || Boolean(d[1]) })
                     .attr("stroke", "black")
                     .attr("fill", function(d, i) { return  monitors[uid].color })
                     .attr("cx", function(d, i) { return x(d[0]); })
                     .attr("cy", function(d, i) { return y2(d[1]); })
                     .attr("r", function(d) {
                        return ((position && d[0] == position) ? 4 : 2);
                      });

            } else if(monitors[uid].classname == 'GroupMonitor'){
                for(var i = 0; i < monitors[uid].values[step].length; i++){
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
                            if(monitors[uid].values[step]){
                                data.push([step, parseFloat(monitors[uid].values[step][i])]);
                            } else {
                                data.push([step, null]);
                            }
                        }
                    }
                    var points = svg.selectAll(".point")
                        .data(data)
                        .enter().append("svg:circle")
                        .filter(function(d, i){ return d[1] == 0 || Boolean(d[1]) })
                         .attr("fill", function(d, i) { return monitors[uid].color })
                         .attr("cx", function(d, i) { return x(d[0]); })
                         .attr("cy", function(d, i) { return y1(d[1]); })
                         .attr("r", function(d) {
                            return ((position && d[0] == position) ? 4 : 2);
                          });
                }
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
                    .filter(function(d, i){ return d[1] == 0 || Boolean(d[1]) })
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
