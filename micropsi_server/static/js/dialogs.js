
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
        form.ajaxSubmit({
            success: function(data){
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

    call: function(functionname, params, success_cb, error_cb, method){
        var url = '/rpc/'+functionname;
        if(method != "post"){
            args = '';
            for(var key in params){
                args += key+'='+encodeURIComponent(JSON.stringify(params[key]))+',';
            }
            url += '('+args.substr(0, args.length-1) + ')';
        }
        $.ajax({
            url: url,
            data: ((method == "post") ? JSON.stringify(params) : null),
            type: method || "get",
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
        dialogs.notification("Changes saved", 'success');
    },
    defaultErrorCallback: function (data, outcome, type){
        var msg = '';
        if(data.status == 0){
            msg = "Server not reachable.";
        } else {
            try{
                error = JSON.parse(data.responseText);
                var errtext = $('<div/>').text(error.data).html();
                msg += '<strong>' + errtext + '</strong>';
                if(error.traceback){
                    msg += '<p><pre class="exception">'+error.traceback+'</pre></p>';
                }
            } catch (err){}
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

    $('a.remote_form_dialog').on('click', remote_form);

    $('.navbar a.nodenet_new').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(data){
            // refreshNodenetList();  -- TODO: does not work yet (due to paperscript missing proper js integration)
            dialogs.notification('Nodenet created. ID: ' + data.nodenet_uid, 'success');
            $.cookie('selected_nodenet', data.nodenet_uid, { expires: 7, path: '/' });
            window.location.reload();
        });
    });

    $('.navbar a.nodenet_delete').on('click', function(){
        if(typeof currentNodenet == 'undefined'){
            return dialogs.notification("there is no current nodenet selected");
        }
        dialogs.confirm("Do you really want to delete this nodenet?", function(){
            api.call('delete_nodenet', {nodenet_uid: currentNodenet}, function(data){
                currentNodenet=null;
                // refreshNodenetList();  -- TODO: does not work yet (due to paperscript missing proper js integration)
                $.cookie('selected_nodenet', currentNodenet, { expires: 7, path: '/' });
                dialogs.notification('Nodenet deleted');
                window.location.reload();
            });
        });
    });

    $('.navbar a.nodenet_edit').on('click', function(event){
        event.preventDefault();
        if(typeof currentNodenet == 'undefined'){
            return dialogs.notification("there is no current nodenet selected");
        }
        api.call('edit_nodenet', {nodenet_uid: currentNodenet});
    });

    $('.navbar a.nodenet_save').on('click', function(event){
        event.preventDefault();
        if(typeof currentNodenet == 'undefined'){
            return dialogs.notification("there is no current nodenet selected");
        }
        api.call('save_nodenet', {nodenet_uid: currentNodenet});
    });

    $('.navbar a.nodenet_revert').on('click', function(event){
        event.preventDefault();
        if(typeof currentNodenet == 'undefined'){
            return dialogs.notification("there is no current nodenet selected");
        }
        api.call('revert_nodenet', {nodenet_uid: currentNodenet}, function(data){
            dialogs.notification("nodenet reverted");
            //setCurrentNodenet(nodenet_uid);  -- TODO: does not work yet (due to paperscript missing proper js integration)
            window.location.reload();
        });
    });

    $('.navbar a.reload_native_modules').on('click', function(event){
        event.preventDefault();
        if(typeof currentNodenet == 'undefined'){
            return dialogs.notification("there is no current nodenet selected");
        }
        api.call('reload_native_modules', {nodenet_uid: currentNodenet}, function(){
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
        if(typeof currentNodenet == 'undefined'){
            return dialogs.notification("there is no current nodenet selected");
        }
        dialogs.remote_form_dialog(event.target.href + '/' + currentNodenet, function(){
            window.location.reload();
        });
    });

    // WORLD
    $('.navbar a.world_new').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(data){
            dialogs.notification('World created. ID: ' + data.world_uid, 'success');
            var url = '/world_list/' + ($.cookie('selected_world') || '');
            $.get(url, {}, function(data){
                $('#world_list').html(data);
            });
        });
    });
    $('.navbar a.world_edit').on('click', remote_form);

    $('.navbar a.world_delete').on('click', function(event){
        event.preventDefault();
        if(typeof currentWorld == 'undefined'){
            return dialogs.notification("there is no current world selected");
        }
        dialogs.confirm("Do you really want to delete this world?", function(){
            api.call('delete_world',
                {world_uid: currentWorld},
                function(){
                    $.cookie('selected_world', '', {expires: -1, path: '/'});
                    dialogs.notification("World deleted");
                    window.location.reload();
                }
            );
        });
    });

    $('.navbar a.world_save').on('click', function(event){
        event.preventDefault();
        if(typeof currentWorld == 'undefined'){
            return dialogs.notification("there is no current world selected");
        }
        api.call('save_world', {world_uid: currentWorld});
    });

    $('.navbar a.world_revert').on('click', function(event){
        event.preventDefault();
        if(typeof currentWorld == 'undefined'){
            return dialogs.notification("there is no current world selected");
        }
        api.call('revert_world', {world_uid: currentWorld},
            function(){
                dialogs.notification("World state reverted");
                window.location.reload();
            }, function(){
                dialogs.notification('Error reverting world', 'error');
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
        dialogs.remote_form_dialog($(event.target).attr('href'), function(){window.location.reload();});
    });

    $('.nodenet_export').on('click', function(event){
        event.preventDefault();
        if(typeof currentNodenet == 'undefined'){
            return dialogs.notification("there is no current nodenet selected");
        }
        window.location.replace(event.target.href + '/' + currentNodenet);
    });

    $('.world_export').on('click', function(event){
        event.preventDefault();
        if(typeof currentWorld == 'undefined'){
            return dialogs.notification("there is no current world selected");
        }
        window.location.replace(event.target.href + '/' + currentWorld);
    });

    $('.add_custom_monitor').on('click', function(event){
        event.preventDefault();
        $('#monitor_name_input').val('');
        $('#monitor_code_input').val('');
        $('#monitor_modal .custom_monitor').show();
        $('#monitor_modal').modal('show');
        $('#monitor_modal .btn-primary').on('click', function(event){
            api.call('add_custom_monitor', {
                'nodenet_uid': currentNodenet,
                'function': $('#monitor_code_input').val(),
                'name': $('#monitor_name_input').val()
            }, function(data){
                dialogs.notification("monitor saved");
                $(document).trigger('monitorsChanged', data);
                $('#monitor_modal .btn-primary').off();
                $('#monitor_modal').modal('hide');
            }, function(data){
                api.defaultErrorCallback(data);
                $('#monitor_modal .btn-primary').off();
                $('#monitor_modal').modal('hide');
            },
            method="post");
        });
    });


    var recipes = {};
    var recipe_name_input = $('#recipe_name_input');

    var update_parameters_for_recipe = function(){
        var name = recipe_name_input.val();
        if(name in recipes){
            var html = '';
            for(var i in recipes[name].parameters){
                var param = recipes[name].parameters[i];
                html += '' +
                '<div class="control-group">'+
                    '<label class="control-label" for="params_'+param.name+'_input">'+param.name+'</label>'+
                    '<div class="controls">'+
                        '<input type="text" name="'+param.name+'" class="input-xlarge" id="params_'+param.name+'_input" value="'+(param.default || '')+'"/>'+
                    '</div>'+
                '</div>';
            }
            $('.recipe_param_container').html(html);
        }
    };

    var run_recipe = function(){
        var form = $('#recipe_modal form');
        data = form.serializeArray();
        parameters = {};
        for(var i=0; i < data.length; i++){
            if(data[i].name != 'recipe_name_input'){
                parameters[data[i].name] = data[i].value
            }
        }
        api.call('run_recipe', {
            'nodenet_uid': currentNodenet,
            'name': recipe_name_input.val(),
            'parameters': parameters,
        }, function(data){
            window.location.reload();
        });
    };

    recipe_name_input.on('change', update_parameters_for_recipe);
    $('#recipe_modal .btn-primary').on('click', run_recipe);
    $('#recipe_modal form').on('submit', run_recipe);

    $('.run_recipe').on('click', function(event){
        $('#recipe_modal').modal('show');
        api.call('get_available_recipes', {}, function(data){
            recipes = data;
            var options = '';
            for(var key in data){
                options += '<option>' + data[key].name + '</option>';
            }
            recipe_name_input.html(options);
            update_parameters_for_recipe();
        });
    });

});


updateWorldAdapterSelector = function() {
    var option = $("#nn_world option:selected");
    if (option) {
        $("#nn_worldadapter").load("/create_worldadapter_selector/"+option.val());
    }
};


var listeners = {}
var simulationRunning = false;
var currentNodenet;
var runner_properties = {};


$(function(){
    setButtonStates(false);
    currentNodenet = $.cookie('selected_nodenet') || '';
    if(currentNodenet){
        fetch_stepping_info();
    }
});

register_stepping_function = function(type, input, callback){
    listeners[type] = {'input': input, 'callback': callback};
}

fetch_stepping_info = function(){
    params = {
        nodenet_uid: currentNodenet
    };
    for (key in listeners){
        params[key] = listeners[key].input()
    }
    api.call('get_current_state', params, success=function(data){
        var start = new Date().getTime();
        for(key in listeners){
            if(data[key]){
                listeners[key].callback(data[key]);
            }
        }
        $('.nodenet_step').text(data.current_nodenet_step);
        $('.world_step').text(data.current_world_step);
        var end = new Date().getTime();
        if(data.simulation_running){
            if(runner_properties.timestep - (end - start) > 0){
                window.setTimeout(fetch_stepping_info, runner_properties.timestep - (end - start));
            } else {
                $(document).trigger('runner_stepped');
            }
        }
        setButtonStates(data.simulation_running);
    });
}

$(document).on('runner_started', fetch_stepping_info);
$(document).on('runner_stepped', fetch_stepping_info);
$(document).on('nodenet_changed', function(event, new_uid){
    currentNodenet = new_uid;
})
$(document).on('form_submit', function(event, data){
    if(data.url == '/config/runner'){
        for(var i=0; i < data.values.length; i++){
            switch(data.values[i].name){
                case 'timestep': runner_properties.timestep = parseInt(data.values[i].value); break;
                case 'factor': runner_properties.timestep = parseInt(data.values[i].value); break;
            }
        }
    }
});

api.call('get_runner_properties', {}, function(data){
    runner_properties = data;
});

function setButtonStates(running){
    if(running){
        $('#nodenet_start').addClass('active');
        $('#nodenet_stop').removeClass('active');
    } else {
        $('#nodenet_start').removeClass('active');
        $('#nodenet_stop').addClass('active');
    }
}

function stepNodenet(event){
    event.preventDefault();
    if(simulationRunning){
        stopNodenetrunner(event);
    }
    if(currentNodenet){
        api.call("step_simulation",
            {nodenet_uid: currentNodenet},
            success=function(data){
                $(document).trigger('runner_stepped');
            });
    } else {
        dialogs.notification('No nodenet selected', 'error');
    }
}

function startNodenetrunner(event){
    event.preventDefault();
    nodenetRunning = true;
    if(currentNodenet){
        api.call('start_simulation', {nodenet_uid: currentNodenet}, function(){
            $(document).trigger('runner_started');
        });
    } else {
        dialogs.notification('No nodenet selected', 'error');
    }
}
function stopNodenetrunner(event){
    event.preventDefault();
    api.call('stop_simulation', {nodenet_uid: currentNodenet}, function(){
        $(document).trigger('runner_stopped');
        nodenetRunning = false;
    });
}

function resetNodenet(event){
    event.preventDefault();
    nodenetRunning = false;
    if(currentNodenet){
        api.call(
            'revert_nodenet',
            {nodenet_uid: currentNodenet},
            function(){
                window.location.reload();
                // $(document).trigger('load_nodenet', currentNodenet);
            }
        );
    } else {
        dialogs.notification('No nodenet selected', 'error');
    }
}
$(function() {
    $('#nodenet_start').on('click', startNodenetrunner);
    $('#nodenet_stop').on('click', stopNodenetrunner);
    $('#nodenet_reset').on('click', resetNodenet);
    $('#nodenet_step_forward').on('click', stepNodenet);
});

// data tables

$.extend( $.fn.dataTableExt.oStdClasses, {
    "sWrapper": "dataTables_wrapper form-inline"
} );

$(document).ready(function() {
    $('#nodenet_mgr').dataTable( {
        "sDom": "<'row'<'span6'l><'span6'f>r>t<'row'<'span6'i><'span6'p>>",
        "sPaginationType": "bootstrap"
    } );
    $('textarea.loc').autogrow();
} );


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

var sections = ['nodenet_editor', 'monitor', 'world_editor'];

$(document).ready(function() {
    if($('.frontend_section').length == 1){
        $('.frontend_section').addClass('in');
    } else {
        $.each(sections, cookiebindings);
    }
});
