
Object.values = function(obj){
    ret = [];
    for(var key in obj){
        ret.push(obj[key]);
    }
    return ret;
}

window.sortByName = function(a, b){
    if(a.name.toLowerCase() < b.name.toLowerCase()) return -1;
    if(b.name.toLowerCase() < a.name.toLowerCase()) return 1;
    return 0;
}

var dialogs = {

    /**
        renders a simple confirmation modal, containing the given message
        the callback is executed, if the user confirms the dialog.
    */
    confirm: function(message, callback){
        $('#confirm_dialog p.message').html(message);
        var el = $('#confirm_dialog');
        var submit = $('#confirm_dialog .btn-confirm');
        el.modal();
        submit.off();
        submit.on('click', function(){
            el.modal('hide');
            callback();
        });
    },


    /**
        renders a modal, with the html obtained from the url.
    */
    remote_form_dialog: function(url, callback){
        $('#remote_form_dialog').html('').modal();
        $.ajax(url, {
            success: function(data){
                dialogs.setModalForm(data, callback);
            }
        });
    },

    /**
        Set the content of the modal and bind form-submit events

        If you want a second dialog, or want to display another dialog,
        use links with the class "modal_followup". The JS will then fetch the html
        from the href attribute, and set it as the dialog's content.

    */
    setModalForm: function(data, callback){
        var el = $('#remote_form_dialog');
        if (data.msg){
            el.modal('hide');
            return dialogs.notification(data.msg, data.status);
        }
        el.html(data);
        var links = $('.modal_followup', el);
        if(links){
            links.on('click', function(event){
                event.preventDefault();
                dialogs.remote_form_dialog($(event.target).attr('href'), callback);
            });
        }
        var submit = $('#remote_form_dialog .btn-primary');
        submit.bind('click', {callback: callback}, dialogs.async_form_submit);
        $('form', el).bind('submit', {callback: callback}, dialogs.async_form_submit);
    },

    /**
        callback after submission of the form.
        The backend can deliver the following responses:

            * A dict, with a 'status' and a 'msg'. The modal will close,
              and the message will be displayed as a notification. the status
              can be one of ['info', 'error', 'success'] to correspond with the
              bootstrap notification themes

            * A dict, with a 'redirect' parameter. The JS will then trigger
              a reload to the given url

            * HTML. The modal will persist, and set the delivered html as its content

    */
    async_form_submit: function(event, callback){
        event.preventDefault();
        var el = $('#remote_form_dialog');
        form = $('form', el);
        $('#loading').show();
        form.ajaxSubmit({
            success: function(data){
                $('#loading').hide();
                $(document).trigger('form_submit', form.attr('action'), form.serializeArray());
                if(data.redirect){
                    window.location.replace(data.redirect);
                } else if (data.msg){
                    el.modal('hide');
                    if(data.status == 'success' && event.data.callback){
                        event.data.callback(data);
                    }
                    dialogs.notification(data.msg, data.status);
                } else {
                    dialogs.setModalForm(data, callback);
                }
            },
            error: function(data, param1){
                if(data.status == 500){
                    $('body').html(data.responseText);
                } else {
                    dialogs.notification(data.statusText, "error");
                }
            }
        });
    },

    /**
        render a simple and temporary twitter bootstrap notification.
        Parameters:
            message - the message to display
            status - one of ['error', 'info', 'success', 'exception']
    */
    notification: function(message, status){
        if(status == 'exception'){
            var fadeOut = { enabled: false}
            var content = { html: message }
            status = 'error';
        } else {
            var fadeOut = { enabled: true, delay: 1000 };
            var content = { text: message }
        }
        $('#notification').notify({
            message: content,
            fadeOut: fadeOut,
            type: status || "info"
        }).show();
    }

};

var api = {

    base_url: '/rpc/',

    call: function(functionname, params, success_cb, error_cb, method){
        var url = api.base_url+functionname;
        $.ajax({
            url: url,
            data: ((method != "get") ? JSON.stringify(params) : params),
            type: method || "post",
            processData: (method == "get"),
            contentType: "application/json",
            success: function(response){
                if(response.status == 'success'){
                    if(success_cb) success_cb(response.data);
                    else api.defaultSuccessCallback(response.data);
                } else{
                    if(error_cb) error_cb(response);
                    else api.defaultErrorCallback(response);
                }
            },
            error: error_cb || api.defaultErrorCallback
        });
    },
    defaultSuccessCallback: function (data){
        $('#loading').hide();
        dialogs.notification("Changes saved", 'success');
    },
    defaultErrorCallback: function (data, outcome, type){
        $('#loading').hide();
        var msg = '';
        if(data.status == 0){
            msg = "Server not reachable.";
        } else {
            if(data.responseText){
                try{
                    error = JSON.parse(data.responseText);
                    var errtext = $('<div/>').text(error.data).html();
                    msg += '<strong>' + errtext + '</strong>';
                    if(error.traceback){
                        msg += '<p><pre class="exception">'+error.traceback+'</pre></p>';
                    }
                } catch (err){}
            } else if(data.data) {
                if(typeof data.data == 'object'){
                    msg = '<ul>';
                    for(var i in data.data){
                        msg += '<li>'+data.data[i]+'</li>';
                    }
                    msg += '</ul>';
                } else {
                    msg = data.data
                }
            }
            if(!msg){
                msg = type || "serverside exception";
            }
        }
        dialogs.notification("Error: " + msg, 'exception');
    },
    EmptyCallback: function (){}
};


$(function() {

    // Bind Menubar links

    // NODENET
    function remote_form(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    }

    $('.navbar .nav .dropdown').find('a').on('click', function(event){
        if($(event.target).parent().hasClass("disabled")){
            event.stopImmediatePropagation();
            event.preventDefault();
        }
    });
    $('a.dropdown-toggle[href=#menu_nodenet]').on('click', function(event){
        if(currentNodenet){
            $('#menu_nodenet').find('[data=nodenet-needed]').removeClass("disabled")
        } else {
            $('#menu_nodenet').find('[data=nodenet-needed]').addClass("disabled")
        }
    });
    $('a.dropdown-toggle[href=#menu_world]').on('click', function(event){
        if(currentWorld){
            $('#menu_world').find('[data=world-needed]').removeClass("disabled")
        } else {
            $('#menu_world').find('[data=world-needed]').addClass("disabled")
        }
    });

    $('a.remote_form_dialog').on('click', remote_form);

    $('.navbar a.nodenet_new').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(data){
            // refreshNodenetList();  -- TODO: does not work yet (due to paperscript missing proper js integration)
            dialogs.notification('Agent created. ID: ' + data.nodenet_uid, 'success');
            $.cookie('selected_nodenet', data.nodenet_uid+"/", { expires: 7, path: '/' });
            window.location.reload();
        });
    });
    $('.navbar a.nodenet_edit').on('click', function(event){
        event.preventDefault();
        console.log($(event.target).attr('href') + currentNodenet);
        dialogs.remote_form_dialog($(event.target).attr('href') + currentNodenet, function(data){
            dialogs.notification('Changes saved', 'success');
            window.location.reload();
            // $(document).trigger("runner_stepped");
        });
    });
    $('.navbar a.nodenet_delete').on('click', function(){
        dialogs.confirm("Do you really want to delete this agent?", function(){
            api.call('delete_nodenet', {nodenet_uid: currentNodenet}, function(data){
                currentNodenet=null;
                // refreshNodenetList();  -- TODO: does not work yet (due to paperscript missing proper js integration)
                $.cookie('selected_nodenet', "", { expires: 7, path: '/' });
                dialogs.notification('Agent deleted');
                window.location.reload();
            });
        });
    });

    $('.navbar a.nodenet_save').on('click', function(event){
        event.preventDefault();
        $('#loading').show();
        api.call('save_nodenet', {nodenet_uid: currentNodenet});
    });

    $('.navbar a.nodenet_revert').on('click', function(event){
        event.preventDefault();
        $('#loading').show();
        api.call('revert_nodenet', {nodenet_uid: currentNodenet}, function(data){
            dialogs.notification("agent reverted");
            //setCurrentNodenet(nodenet_uid);  -- TODO: does not work yet (due to paperscript missing proper js integration)
            window.location.reload();
        });
    });

    $('.navbar a.reload_code').on('click', function(event){
        event.preventDefault();
        if($(event.target).hasClass("reload_revert")){
            api.call('reload_and_revert', {nodenet_uid: currentNodenet}, function(){
                window.location.reload();
            });
            return
        }
        $('#loading').show();
        api.call('reload_code', {}, function(){
            dialogs.notification("reload successful");
            window.location.reload();
        });
    });

    $('.navbar a.nodenet_import').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog(event.target.href, function(){
            window.location.reload();
        });
    });
    $('.navbar a.nodenet_merge').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog(event.target.href + '/' + currentNodenet, function(){
            window.location.reload();
        });
    });

    // WORLD
    $('.navbar a.world_manage').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    });

    $('.navbar a.device_manage').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    });

    $('.navbar a.world_delete').on('click', function(event){
        event.preventDefault();
        dialogs.confirm("Do you really want to delete this environment?", function(){
            api.call('delete_world',
                {world_uid: currentWorld},
                function(){
                    $.cookie('selected_world', '', {expires: -1, path: '/'});
                    dialogs.notification("Environment deleted");
                    window.location.reload();
                }
            );
        });
    });

    $('.navbar a.world_save').on('click', function(event){
        event.preventDefault();
        api.call('save_world', {world_uid: currentWorld});
    });

    $('.navbar a.world_revert').on('click', function(event){
        event.preventDefault();
        api.call('revert_world', {world_uid: currentWorld},
            function(){
                dialogs.notification("Environment state reverted");
                window.location.reload();
            }, function(){
                dialogs.notification('Error reverting environment', 'error');
                window.location.reload();
            }
        );
    });

    $('.navbar a.world_import').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(){window.location.reload();});
    });

    // USER

    $('a.set_new_password').on('click', remote_form);

    $('a.create_user').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(){window.location.reload();});
    });

    $('a.login').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($('a.login').attr('href'), function(){window.location.reload();});
    });

    $('.nodenet_export').on('click', function(event){
        event.preventDefault();
        window.location.replace(event.target.href + '/' + currentNodenet);
    });

    $('.world_export').on('click', function(event){
        event.preventDefault();
        window.location.replace(event.target.href + '/' + currentWorld);
    });

    var colorpicker = $('.color-chooser').colorpicker({
        color: "#990000"
    });

    $('.add_custom_monitor').on('click', function(event){
        event.preventDefault();
        addMonitor('custom');
    });

    $('#monitor_modal input[name="monitor_node_type"]').on('change', function(event){
        if(event.target.id == 'monitor_node_type_slot'){
            $('.control-group.gate_monitor').hide();
            $('.control-group.slot_monitor').show();
            $('#monitor_type').val('slot')
        } else {
            $('.control-group.slot_monitor').hide();
            $('.control-group.gate_monitor').show();
            $('#monitor_type').val('gate')
        }
    });

    function submitMonitorModal(event){
        event.preventDefault();
        var type = $('#monitor_type').val();
        var func;
        var params = {
            nodenet_uid: currentNodenet,
            name: $('#monitor_name_input').val(),
            color: $('#monitor_color_input').val()
        };
        switch(type){
            case 'gate':
            case 'slot':
                func = 'add_'+type+'_monitor';
                params['node_uid'] = $('#monitor_node_uid_input').val();
                params[type] = $('#monitor_'+type+'_input').val()
                break;
            case 'link':
                func = 'add_link_monitor';
                params['source_node_uid'] = $('#monitor_link_sourcenode_uid_input').val();
                params['gate_type'] = $('#monitor_link_sourcegate_type_input').val();
                params['target_node_uid'] = $('#monitor_link_targetnode_uid_input').val();
                params['slot_type'] = $('#monitor_link_targetslot_type_input').val();
                break;
            case 'modulator':
                func = 'add_modulator_monitor';
                params['modulator'] = $('#monitor_modulator_input').val();
                break;
            case 'custom':
                func = "add_custom_monitor";
                params['function'] = $('#monitor_code_input').val();
                break;
        }
        api.call(func, params, function(data){
            dialogs.notification("monitor saved");
            if($.cookie('currentMonitors')){
                currentMonitors = JSON.parse($.cookie('currentMonitors'));
            } else {
                currentMonitors = [];
            }
            currentMonitors.push(data)
            $.cookie('currentMonitors', JSON.stringify(currentMonitors), {path:'/', expires:7})
            $(document).trigger('monitorsChanged', data);
            $('#monitor_modal').modal('hide');
        }, function(data){
            api.defaultErrorCallback(data);
            $('#monitor_modal').modal('hide');
        });
    }
    $('#monitor_modal .btn-primary').on('click', submitMonitorModal);
    $('#monitor_modal form').on('submit', submitMonitorModal);

    var remove_condition = $('#remove_runner_condition');
    var set_condition = $('#set_runner_condition');
    remove_condition.on('click', function(event){
        api.call('remove_runner_condition', {nodenet_uid: currentNodenet}, function(event){
            fetch_stepping_info();
        });
    });
    set_condition.on('click', function(event){
        event.preventDefault();
        api.call('get_monitoring_info', {nodenet_uid: currentNodenet}, function(data){
            var html = '';
            var sorted = Object.values(data.monitors);
            sorted.sort(sortByName);
            for(var i in sorted){
                html += '<option value="'+sorted[i].uid+'">'+sorted[i].name+'</option>';
            }
            $('#run_condition_monitor_selector').html(html);
            $('#run_nodenet_dialog').modal('show');
            $('#run_condition_steps').focus();
        });
    });

    function set_runner_condition(event){
        event.preventDefault();
        var text = '';
        var params = {nodenet_uid: currentNodenet};
        params.steps = $('#run_condition_steps').val() || null;
        var monitor_val = $('#run_condition_monitor_value').val();
        if (monitor_val){
            params.monitor = {
                'uid': $('#run_condition_monitor_selector').val(),
                'value': monitor_val
            }
        }
        api.call('set_runner_condition', params, function(data){
            fetch_stepping_info();
        });
        $('#run_nodenet_dialog').modal('hide');
    }

    $('#run_nodenet_dialog button.btn-primary').on('click', set_runner_condition);
    $('#run_nodenet_dialog form').on('submit', set_runner_condition);

    var recipes = {};
    var recipe_name_input = $('#recipe_name_input');

    var update_parameters_for_recipe = function(){
        var name = recipe_name_input.val();
        if(Object.keys(recipes).length && name in recipes){
            $('#recipe_modal .default_explanation').hide();
            $('#recipe_modal .docstring').show();
            $('#recipe_modal .docstring').html(recipes[name].docstring);
            $('#recipe_modal .btn-primary').show();
        } else {
            $('#recipe_modal .default_explanation').show();
            $('#recipe_modal .docstring').hide();
            $('#recipe_modal .btn-primary').hide();
        }
        var html = '';
        if(name in recipes){
            for(var i in recipes[name].parameters){
                var param = recipes[name].parameters[i];
                html += '' +
                '<div class="control-group">'+
                    '<label class="control-label" for="params_'+param.name+'_input">'+param.name+'</label>'+
                    '<div class="controls">'+
                        '<input type="text" name="'+param.name+'" class="input-xlarge" id="params_'+param.name+'_input" value="'+((param.default == null) ? '' : param.default)+'"/>'+
                    '</div>'+
                '</div>';
            }
        }
        $('.recipe_param_container').html(html);
    };

    var run_recipe = function(event){
        event.preventDefault();
        var form = $('#recipe_modal form');
        data = form.serializeArray();
        parameters = {};
        for(var i=0; i < data.length; i++){
            if(data[i].name != 'recipe_name_input'){
                parameters[data[i].name] = data[i].value
            }
        }
        $('#recipe_modal button').prop('disabled', true);
        $('#loading').show();
        api.call('run_recipe', {
            'nodenet_uid': currentNodenet,
            'name': recipe_name_input.val(),
            'parameters': parameters,
        }, function(data){
            $('#recipe_modal').modal('hide');
            $('#loading').hide();
            var reload = data.reload;
            if(!reload) {
                $(document).trigger('runner_stepped');
            }
            delete data.reload;
            if(data){
                html = '';
                if(data.content_type && data.content_type.indexOf("image") > -1){
                    html += '<p><img src="'+data.content_type+','+data.data+'" /></p>';
                    delete data.content_type
                    delete data.data
                }
                if(Object.keys(data).length){
                    html += '<dl>';
                    for(var key in data){
                        html += '<dt>'+key+':</dt>';
                        if(typeof data[key] == 'string'){
                            html += '<dd>'+data[key]+'</dd>';
                        } else {
                            html += '<dd>'+JSON.stringify(data[key])+'</dd>';
                        }
                    }
                    html += '</dl>';
                }
                if(html){
                    $('#recipe_result .modal-body').html(html);
                    $('#recipe_result').modal('show');
                    $('#recipe_result button').off();
                    if(reload){
                        $('#recipe_result button').on('click', function(){
                            window.location.reload();
                        });
                    }
                } else {
                    if(reload){
                        window.location.reload();
                    } else {
                        dialogs.notification("Recipe ran successful", 'success');
                    }
                }
            }
        }, function(data){
            $('#recipe_modal button').removeAttr('disabled');
            api.defaultErrorCallback(data);
        });
    };

    recipe_name_input.on('change', update_parameters_for_recipe);
    $('#recipe_modal .btn-primary').on('click', run_recipe);
    $('#recipe_modal form').on('submit', run_recipe);
    $('.run_recipe').on('click', function(event){
        $('#recipe_modal').modal('show');
        $('#recipe_modal button').prop('disabled', false);
        api.call('get_available_recipes', {}, function(data){
            recipes = data;
            var categories = {};
            for(var key in recipes){
                if(!categories[recipes[key].category]){
                    categories[recipes[key].category] = [];
                }
                categories[recipes[key].category].push(recipes[key]);
            }
            var sorted = Object.keys(categories);
            sorted.sort();
            recipe_name_input.chosen('destroy');
            var html = '<option></option>';
            var cat;
            for(var i in sorted){
                cat = sorted[i]
                html += '<optgroup label="'+cat+'">';
                categories[cat].sort(sortByName);
                for(var i in categories[cat]){
                    html += '<option>' + categories[cat][i].name + '</option>';
                }
                html += '</optgroup>'
            }
            recipe_name_input.html(html);
            recipe_name_input.val('');
            recipe_name_input.chosen({'search_contains': true});
            recipe_name_input.focus();
            recipe_name_input.trigger('chosen:open');
            update_parameters_for_recipe();
        });
    });

});


updateWorldAdapterSelector = function() {
    var option = $("#nn_world option:selected");
    uid = (option)? option.val() : "";
    $("#nn_worldadapter").parent().load("/create_worldadapter_selector/"+option.val(), null, function(evt){
        $('#nn_world').trigger("world_form_refreshed");
    });
};


var listeners = {}
var calculationRunning = false;
var currentNodenet;
var runner_properties = {};
var sections = ['nodenet_editor', 'netapi_console', 'monitor', 'world_editor'];


register_stepping_function = function(type, input, callback){
    listeners[type] = {'input': input, 'callback': callback};
}
unregister_stepping_function = function(type){
    delete listeners[type];
}

busy = false;
fetch_stepping_info = function(){
    if(!currentNodenet){
        return false;
    }
    params = {
        nodenet_uid: currentNodenet
    };
    for (key in listeners){
        params[key] = listeners[key].input()
    }
    busy = true;
    api.call('get_calculation_state', params, success=function(data){
        busy = false;
        var start = new Date().getTime();
        window.currentSimulationStep = data.current_nodenet_step;
        window.nodenetRunning = data.is_active;
        for(key in listeners){
            if(data[key]){
                listeners[key].callback(data[key]);
            }
        }
        $('.nodenet_step').text(data.current_nodenet_step);
        $('.world_step').text(data.current_world_step);
        var text = [];
        if(data.calculation_condition){
            if(data.calculation_condition.step_amount){
                text.push("run " + data.calculation_condition.step_amount + " steps");
                $('#run_condition_steps').val(data.calculation_condition.step_amount);
            }
            if(data.calculation_condition.monitor){
                text.push('<span style="color: '+data.calculation_condition.monitor.color+';">monitor = ' + data.calculation_condition.monitor.value + '</span>');
                $('#run_condition_monitor_selector').val(data.calculation_condition.monitor.uid);
                $('#run_condition_monitor_value').val(data.calculation_condition.monitor.value);
            }
        }
        if(text.length){
            $('#calculation_controls .runner_condition').html(text.join(" or "));
            $('#calculation_controls .running_conditional').show();
            $('#remove_runner_condition').show();
        } else {
            $('#calculation_controls .running_conditional').hide();
            $('#remove_runner_condition').hide();
            $('#set_runner_condition').show();
        }

        var end = new Date().getTime();
        calculationRunning = data.calculation_running;
        if(data.calculation_running && !busy){
            if(runner_properties.timestep - (end - start) > 0){
                window.setTimeout(fetch_stepping_info, runner_properties.timestep - (end - start));
            } else {
                $(document).trigger('runner_stepped');
            }
        }
        setButtonStates(data.calculation_running);
        if(data.user_prompt){
            promptUser(data.user_prompt);
        }
    }, error=function(data, outcome, type){
        $(document).trigger('runner_stopped');
        setButtonStates(false);
        if(data.data == 'No such nodenet'){
            currentNodenet = null;
            $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
        } else {
            api.defaultErrorCallback(data, outcome, type);
        }
    });

    $('#nodenet_user_prompt .btn-primary').on('click', function(event){
        event.preventDefault();
        var form = $('#nodenet_user_prompt form');
        parameters = {};
        var startnet = false;
        var fields = form.serializeArray();
        for(var idx in fields){
            if(fields[idx].name == 'run_nodenet'){
                startnet = true;
            } else {
                parameters[fields[idx].name] = fields[idx].value;
            }
        }
        api.call('user_prompt_response', {
            nodenet_uid: currentNodenet,
            node_uid: $('#user_prompt_node_uid').val(),
            key: $('#user_prompt_key').val(),
            parameters: parameters,
            resume_nodenet: startnet
        }, function(data){
            $(document).trigger("runner_started");
        });
        $('#nodenet_user_prompt').modal('hide');
    });
}

$(document).on('runner_started', fetch_stepping_info);
$(document).on('runner_stepped', fetch_stepping_info);
$(document).on('nodenet_changed', function(event, new_uid){
    currentNodenet = new_uid;
    $.cookie('selected_nodenet', currentNodenet+"/", { expires: 7, path: '/' });
    refreshNodenetList();
})
$(document).on('form_submit', function(event, data){
    if(data.url == '/config/runner'){
        for(var i=0; i < data.values.length; i++){
            if (data.values[i].name == 'timestep'){
                runner_properties.timestep = parseInt(data.values[i].value);
                break;
            }
        }
    }
});

api.call('get_runner_properties', {}, function(data){
    runner_properties = data;
});

function refreshNodenetList(){
    $.get("/agent_list/"+(currentNodenet || ''), function(html){
        $.each($('.nodenet_list'), function(idx, item){
            $(item).html(html);
            $('.nodenet_select', item).on('click', function(event){
                event.preventDefault();
                var el = $(event.target);
                var uid = el.attr('data');
                $(document).trigger('nodenet_changed', uid);
            });
        });
    });
}

$(document).on('refreshNodenetList', refreshNodenetList);

var default_title = $(document).prop('title');
function setButtonStates(running){
    if(running){
        $(document).prop('title', "▶ " + default_title);
        $('#nodenet_start').addClass('active');
        $('#nodenet_stop').removeClass('active');
        $('#calculation_controls .runner_running').show();
        $('#calculation_controls .runner_paused').hide();
    } else {
        $(document).prop('title', default_title);
        $('#nodenet_start').removeClass('active');
        $('#nodenet_stop').addClass('active');
        $('#calculation_controls .runner_running').hide();
        $('#calculation_controls .runner_paused').show();
    }
}

function stepNodenet(event){
    event.preventDefault();
    if(calculationRunning){
        stopNodenetrunner(event);
    }
    if(currentNodenet){
        api.call("step_calculation",
            {nodenet_uid: currentNodenet},
            success=function(data){
                $(document).trigger('runner_stepped');
            });
    } else {
        dialogs.notification('No agent selected', 'error');
    }
}

function startNodenetrunner(event){
    event.preventDefault();
    nodenetRunning = true;
    if(currentNodenet){
        api.call('start_calculation', {nodenet_uid: currentNodenet}, function(){
            $(document).trigger('runner_started');
        });
    } else {
        dialogs.notification('No agent selected', 'error');
    }
}
function stopNodenetrunner(event){
    event.preventDefault();
    api.call('stop_calculation', {nodenet_uid: currentNodenet}, function(){
        $(document).trigger('runner_stopped');
        nodenetRunning = false;
    });
}

function revertAll(event){
    event.preventDefault();
    nodenetRunning = false;
    if(currentNodenet){
        $('#loading').show();
        api.call(
            'revert_calculation',
            {nodenet_uid: currentNodenet},
            function(){
                window.location.reload();
                // $(document).trigger('load_nodenet', currentNodenet);
            }
        );
    } else {
        dialogs.notification('No agent selected', 'error');
    }
}
$(function() {
    $('#nodenet_start').on('click', startNodenetrunner);
    $('#nodenet_stop').on('click', stopNodenetrunner);
    $('#revert_all').on('click', revertAll);
    $('#nodenet_step_forward').on('click', stepNodenet);
});

// data tables

$.extend( $.fn.dataTableExt.oStdClasses, {
    "sWrapper": "dataTables_wrapper form-inline"
} );

$(document).ready(function() {
    var nodenetcookie = $.cookie('selected_nodenet') || '';
    if (nodenetcookie && nodenetcookie.indexOf('/') > 0){
        nodenetcookie = nodenetcookie.split("/");
        currentNodenet = nodenetcookie[0];
        currentNodeSpace = nodenetcookie[1] || null;
    } else {
        currentNodenet = '';
        currentNodeSpace = '';
    }
    currentWorld = $.cookie('selected_world') || '';
    $('#nodenet_mgr').dataTable( {
        "sDom": "<'row'<'span6'l><'span6'f>r>t<'row'<'span6'i><'span6'p>>",
        "sPaginationType": "bootstrap"
    });
    $('textarea.loc').autogrow();
    if($('.frontend_section').length == 1){
        $('.frontend_section').addClass('in');
    } else {
        $.each(sections, cookiebindings);
    }
    refreshNodenetList();
    setButtonStates(false);
    if(currentNodenet){
        $(document).trigger('nodenet_changed', currentNodenet);
    }
});


// section collapse bindings
function cookiebindings(index, name){
    var last = $.cookie('section_state_'+name);
    var el = $('#' + name);
    if (last === "false" && el) {
        el.removeClass('in');
    } else {
        el.addClass('in');
    }
    if(el){
        el.bind('shown', function() {
            $.cookie('section_state_'+name, true);
        });
        el.bind('hidden', function() {
            $.cookie('section_state_'+name, false);
        });
    }
}


window.addMonitor = function(type, param, val){
    $('#monitor_modal .control-group').hide();
    $('#monitor_modal .control-group.all_monitors').show();
    $('#monitor_modal .control-group.'+type+'_monitor').show();
    $('#monitor_name_input').val('');
    $('#monitor_type').val(type);
    switch(type){
        case 'node':
            var html = '';
            for(var key in param['gates']){
                html += '<option>'+key+'</option>';
            }
            var has_gates = Boolean(html);
            $('#monitor_gate_input').html(html);
            var html = '';
            for(var key in param['slots']){
                html += '<option>'+key+'</option>';
            }
            $('#monitor_slot_input').html(html);
            var has_slots = Boolean(html);
            $('#monitor_node_type_gate').prop('checked', has_gates);
            $('#monitor_node_type_slot').prop('checked', !has_gates);
            $('#monitor_node_type_gate').prop('disabled', !has_gates);
            $('#monitor_node_type_slot').prop('disabled', !has_slots);
            $('#monitor_node_type_gate').trigger('change');
        case 'slot':
        case 'gate':
            if(type == 'slot' || type == 'gate'){
                var html = '';
                for(var key in param[type+'s']){
                    html += '<option>'+key+'</option>';
                }
                $('#monitor_'+type+'_input').html(html);
                if(val){
                    $('#monitor_'+type+'_input').val(val);
                }
            }
            $('#monitor_node_input').val(param.name || param.uid);
            $('#monitor_node_uid_input').val(param.uid);
            if(param.name){
                $('#monitor_name_input').val(param.name);
            }
            break;
        case 'link':
            $('#monitor_link_input').val(param.uid);
            $('#monitor_link_sourcenode_uid_input').val(param.sourceNodeUid);
            $('#monitor_link_sourcegate_type_input').val(param.gateName);
            $('#monitor_link_targetnode_uid_input').val(param.targetNodeUid);
            $('#monitor_link_targetslot_type_input').val(param.slotName);
            break;
        case 'modulator':
            $('#monitor_modulator_input').val(param);
            $('#monitor_name_input').val(param);
            break;
        case 'custom':
            $('#monitor_code_input').val('');
            break;
    }
    $('#monitor_modal').modal('show');
    $('#monitor_name_input').focus();
}

function promptUser(data){
    var html = '';
    html += '<p>Agent interrupted by Node ' + (data.node.name || data.node.uid) +' with message:</p>';
    html += "<p>" + data.msg +"</p>";
    html += '<form class="well form-horizontal">';
    if (data.parameters){
        for(var idx in data.parameters){
            var item = data.parameters[idx];
            html += '<div class="control-group"><label class="control-label">' + item.name + '</label>';
            if(item.options && typeof item.options == 'object'){
                html += '<div class="controls"><select name="'+item.name+'">';
                for(var val in item.options){
                    html += '<option';
                    if (item.default && item.default == item.options[val]){
                        html += ' selected="selected"'
                    }
                    html += '>'+item.options[val]+'</option>';
                }
                html += '</select></div>';
            } else {
                html += '<div class="controls"><input name="'+item.name+'" value="'+(item.default || '')+'" /></div>';
            }
            if (item.description){
                html += '<div class="hint small">'+item.description+'</div>'
            }
            html += '</div>';
        }
    }
    if (nodenetRunning){
        html += '<div class="control-group"><label class="control-label">Continue running agent?</label>';
        html += '<div class="controls"><input type="checkbox" name="run_nodenet"/></div></div>';
    }
    html += '<input class="hidden" id="user_prompt_node_uid" value="'+data.node.uid+'" />';
    html += '<input class="hidden" id="user_prompt_key" value="'+data.key+'" />';
    html += '</form>';
    $('#nodenet_user_prompt .modal-body').html(html);
    $('#nodenet_user_prompt').modal("show");
}


