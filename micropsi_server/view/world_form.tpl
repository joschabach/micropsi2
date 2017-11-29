
<div class="dialogform modal">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>Edit environments</h3>
    </div>

    <div class="modal-body">

        <div class="list_component" style="float:left; width: 33%">
            <form id="world_list">

                <div class="controls">
                    <select class="input-medium" id="input_world_list" size="10">
                    </select>
                </div>
                <div class="modal-buttons">
                    <button id="button_add_world" type="button"> + </button>
                </div>
            </form>
        </div>
        <div id="detail_component" style="float:right; width: 66%;">
            <form id="world_detail" class="">
                <div>
                    <label class="control-label" for="input_world_name">Name</label>
                    <div class="controls">
                        <input type="text" class="input-medium" maxlength="256" id="input_world_name" name="input_world_name" />
                    </div>
                </div>

                <div>
                    <label class="control-label" for="input_world_type">Type</label>
                    <div class="controls">
                        <select class="input-medium" id="input_world_type" name="input_world_type">
                            % for type in sorted(worldtypes.keys()):
                                <option value="{{type}}">{{type}}</option>
                            %end
                        </select>
                        % for type, data in worldtypes.items():
                            <p class="hint xsmall world_docstring world_docstring_{{type}}" style="display:none; white-space: pre-wrap;">{{(data['class'].__doc__ or '').strip()}}</p>
                        %end
                    </div>
                </div>


                %for type, data in worldtypes.items():
                    % for param in data['class'].get_config_options():
                    <div class="control-group world_config world_config_{{type}}" style="display:none">
                        <label class="control-label" for="world_config_{{type}}_{{param['name']}}">{{param['name']}}</label>
                        <div class="controls">
                            %if param.get('description'):
                                <span class="hint xsmall">{{param['description']}}</span>
                            %end
                            % if param.get('options'):
                            <select class="input-xlarge" id="world_config_{{type}}_{{param['name']}}" name="{{type}}_{{param['name']}}">
                                % for val in param['options']:
                                    <option value="{{val}}"
                                    %if param.get('default') and param['default'] == val:
                                        selected="selected"
                                    %end
                                    >{{val}}</option>
                                %end
                            </select>
                            %else:
                            <input class="input-xlarge" id="world_config_{{type}}_{{param['name']}}" name="{{type}}_{{param['name']}}"
                                type="text" value="{{param.get('default', '')}}" />
                            %end
                        </div>
                    </div>
                    %end
                %end

                <div class="modal-buttons">
                    <button type="button" id="button_delete_world">Delete</button>
                    <button type="submit" id="button_save_world">Save</button>
                </div>

            </form>

        </div>
    </div>
    <div class="modal-footer">
        <a class="btn" data-dismiss="modal">Close</a>
    </div>
</div>

<script type="text/javascript">

var world_data = {};
var world_types = {};
var list = $('#input_world_list');
var detail = $('#detail_component');
var selected_world_uid = null;
api.call('get_available_world_types', {}, function(data){
    world_types = data;
    update_all();
});

function update_all(selected_uid){
    api.call('get_available_worlds', {}, function(result){
        world_data = result;
        refresh_world_list();
        select_world(selected_uid);
    });
}

function refresh_world_list(){
    var html = [];
    data = Object.values(world_data).sort(sortByName);
    for(var i in data){
        html.push('<option value="'+data[i].uid+'">'+data[i].name+'</option>');
    }
    list.html(html.join(''));
}

function show_world_params(worldtype){
    $('.world_config').hide();
    $('.world_config_'+worldtype).show();
    $('.world_docstring').hide();
    $('.world_docstring_'+worldtype).show();
}

function fill_detail_values(worlduid){
    var data = world_data[worlduid];
    $('#input_world_name').val(data.name);
    $('#input_world_type').val(data.world_type);
    if(worlduid == 'new'){
        $('#input_world_type').attr('disabled');
    } else {
        $('#input_world_type').removeAttr('disabled', 'disabled');
    }
    show_world_params(data.world_type);
    for (var key in data.config){
        if(key){
            $('#world_config_'+data.world_type+'_'+key).val(data.config[key]);
        }
    }
}

function select_world(selected_uid){
    selected_world_uid = selected_uid;
    list.val(selected_uid);
    if(selected_uid){
        selected_world_uid = selected_uid;
        fill_detail_values(selected_uid);
        detail.show();
    } else {
        detail.hide();
    }
}

$('#button_add_world').on('click', function(event){
    event.preventDefault();
    world_data['new'] = {
        'name': '',
        'world_type': 'DefaultWorld',
        'config': {}
    };
    refresh_world_list();
    select_world('new')
    $('#input_world_name').focus();
});

list.on('change', function(event){
    var val = $(event.target).val();
    select_world(val);
});

$('#input_world_type').on('change', function(event){
    var val = $(event.target).val();
    show_world_params(val);
});

$('#button_delete_world').on('click', function(event){
    event.preventDefault();
    if(confirm("Really delete this world?")){
        api.call('delete_world', {'world_uid': selected_world_uid}, function(result){
            var name = world_data[selected_world_uid].name
            update_all();
            dialogs.notification("World "+name+" deleted");
        })
    }
});

$('#button_save_world').on('click', function(event){
    event.preventDefault();
    data = {'world_name': $('#input_world_name').val()};
    wtype = $('#input_world_type').val();
    for(var i in world_types[wtype].config){
        if(!data.config){
            data.config = {}
        }
        var item = world_types[wtype].config[i];
        data.config[item.name] = $('#world_config_'+wtype+'_'+item.name).val();
    }
    if(selected_world_uid == 'new'){
        data.world_type = wtype;
        api.call('new_world', data, function(result){
            dialogs.notification("World "+data.world_name+" added");
            selected_world_uid = result;
            update_all(result);
        });
    } else {
        data.world_uid = selected_world_uid;
        api.call('set_world_properties', data, function(result){
            dialogs.notification("World "+data.world_name+" saved");
            update_all(selected_world_uid);
        });
    }
});

</script>