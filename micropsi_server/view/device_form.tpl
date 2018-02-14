
<div class="dialogform modal">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>Edit devices</h3>
    </div>

    <div class="modal-body">

        <div class="list_component" style="float:left; width: 33%">
            <form id="device_list">

                <div class="controls">
                    <select class="input-medium" id="input_device_list" size="10">
                    </select>
                </div>
                <div class="modal-buttons">
                    <button id="button_add_device" type="button"> + </button>
                </div>
            </form>
        </div>
        <div id="detail_component" style="float:right; width: 66%; overflow: auto;">
            <form id="device_detail" class="">
                <div class="offline">
                    <button type="button" id="button_delete_offline_device">Delete</button>
                </div>
                <div class="online">
                    <div>
                        <label class="control-label" for="input_device_type">Type</label>
                        <div class="controls">
                            <select class="input-medium" id="input_device_type" name="input_device_type">
                                % for type in sorted(device_types.keys()):
                                    <option value="{{type}}">{{type}}</option>
                                %end
                            </select>
                        </div>
                    </div>


                    %for type, config in device_types.items():
                        % for param in config:
                        <div class="control-group device_config device_config_{{type}}" style="display:none">
                            <label class="control-label" for="device_config_{{type}}_{{param['name']}}">{{param['name']}}</label>
                            <div class="controls">
                                %if param.get('description'):
                                    <span class="hint xsmall">{{param['description']}}</span>
                                %end
                                % if param.get('options'):
                                <select class="input-xlarge" id="device_config_{{type}}_{{param['name']}}" name="{{type}}_{{param['name']}}">
                                    % for val in param['options']:
                                        <option value="{{val}}"
                                            %if param.get('default') and param['default'] == val:
                                                selected="selected"
                                            %end
                                        >{{val}}</option>
                                    %end
                                </select>
                                %else:
                                <input class="input-xlarge" id="device_config_{{type}}_{{param['name']}}" name="{{type}}_{{param['name']}}"
                                    type="text" value="{{param.get('default', '')}}" />
                                %end
                            </div>
                        </div>
                        %end
                    %end

                    <div class="modal-buttons">
                        <button type="button" id="button_delete_device">Delete</button>
                        <button type="submit" id="button_save_device">Save</button>
                    </div>
                </div>
            </form>

        </div>
    </div>
    <div class="modal-footer">
        <a class="btn" data-dismiss="modal">Close</a>
    </div>
</div>

<script type="text/javascript">

var device_data = {};
var device_types = {};
var list = $('#input_device_list');
var detail = $('#detail_component');
var selected_device_uid = null;
api.call('get_device_types', {}, function(data){
    device_types = data;
    update_all();
});

function sort_devices(a, b){
    if(a.config.name.toLowerCase() < b.config.name.toLowerCase()) return -1;
    if(b.config.name.toLowerCase() < a.config.name.toLowerCase()) return 1;
    return 0;
}

function update_all(selected_uid){
    api.call('get_devices', {}, function(result){
        device_data = result;
        refresh_device_list();
        select_device(selected_uid);
    });
}

function refresh_device_list(){
    var html = [];
    var items = [];
    for (var key in device_data){
        device_data[key]['uid'] = key;
    }
    data = Object.values(device_data).sort(sort_devices);
    for(var i in data){
        if(data[i].online){
            html.push('<option value="'+data[i].uid+'">'+data[i].config.name+'</option>');
        } else {
            html.push('<option value="'+data[i].uid+'">'+data[i].config.name+' (offline)</option>');
        }
    }
    list.html(html.join(''));
    detail.hide();
}

function show_device_params(devicetype){
    $('.device_config').hide();
    $('.device_config_'+devicetype).show();
    $('.device_docstring').hide();
    $('.device_docstring_'+devicetype).show();
}

function fill_detail_values(deviceuid){
    var data = device_data[deviceuid];
    if(data.online){
        $('#device_detail .online').show();
        $('#device_detail .offline').hide();
        $('#input_device_name').val(data.config.name);
        $('#input_device_type').val(data.type);
        if(deviceuid == 'new'){
            $('#input_device_type').removeAttr('disabled');
        } else {
            $('#input_device_type').attr('disabled', 'disabled');
        }
        show_device_params($('#input_device_type').val());
        for (var key in data.config){
            if(key){
                $('#device_config_'+data.type+'_'+key).val(data.config[key]);
            }
        }
    } else {
        $('#device_detail .offline').show();
        $('#device_detail .online').hide();
    }
}

function select_device(selected_uid){
    selected_device_uid = selected_uid;
    list.val(selected_uid);
    if(selected_uid){
        selected_device_uid = selected_uid;
        fill_detail_values(selected_uid);
        detail.show();
    } else {
        detail.hide();
    }
}

function delete_device(event){
    event.preventDefault();
    if(selected_device_uid == 'new'){
        delete device_data['new'];
        refresh_device_list();
    } else {
        if(confirm("Really delete this device?")){
            api.call('remove_device', {'device_uid': selected_device_uid}, function(result){
                var name = device_data[selected_device_uid].config.name;
                update_all();
                dialogs.notification("Device "+name+" deleted");
            })
        }
    }
}

$('#button_add_device').on('click', function(event){
    event.preventDefault();
    device_data['new'] = {
        'config': {'name': 'new device'},
        'online': true
    };
    refresh_device_list();
    select_device('new')
    $('#input_device_name').focus();
});

list.on('change', function(event){
    var val = $(event.target).val();
    select_device(val);
});

$('#input_device_type').on('change', function(event){
    var val = $(event.target).val();
    show_device_params(val);
});

$('#button_delete_device').on('click', delete_device);
$('#button_delete_offline_device').on('click', delete_device);


$('#button_save_device').on('click', function(event){
    event.preventDefault();
    data = {config: {}};
    dtype = $('#input_device_type').val();
    for(var i in device_types[dtype]){
        var item = device_types[dtype][i];
        data.config[item.name] = $('#device_config_'+dtype+'_'+item.name).val();
    }
    if(selected_device_uid == 'new'){
        data.device_type = dtype;
        api.call('add_device', data, function(result){
            dialogs.notification("Device "+data.config.name+" added");
            selected_device_uid = result;
            update_all(result);
        });
    } else {
        data.device_uid = selected_device_uid;
        api.call('set_device_properties', data, function(result){
            dialogs.notification("Device "+data.config.name+" saved");
            update_all(selected_device_uid);
        });
    }
});

</script>