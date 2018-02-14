<div class="dialogform modal">

    <form id="nodenet_form" class="form-horizontal" action="/agent/edit" method="POST">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>{{title}}</h3>
    </div>

    <div class="modal-body">

            %if defined('error') and error:
            <div class="alert alert-info">
                <b>Error:</b> {{error}}.
            </div>
            %end

            <fieldset class="well">

                %if not defined("name_error"):
                <div class="control-group">
                %else:
                <div class="control-group error">
                %end
                    <label class="control-label" for="nn_name">Name</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge focused" maxlength="256" id="nn_name" name="nn_name"
                        %if nodenet:
                        value="{{nodenet['name']}}"
                        %end
                        />
                        %if defined("name_error"):
                        <span class="help-inline">{{name_error}}</span>
                        %end
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="nn_engine">Engine</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nn_engine" name="nn_engine"
                        %if nodenet:
                            disabled="disabled"
                        %end
                        >
                            %if numpy_available:
                            <option value="numpy_engine"
                            %if nodenet and nodenet['engine']=="numpy_engine":
                                selected="selected"
                            %end
                            >numpy_engine</option>
                            %end
                            %if theano_available:
                            <option value="theano_engine"
                            %if nodenet and nodenet['engine']=="theano_engine":
                            selected="selected"
                            %end
                            >theano_engine</option>
                            %end
                            <option value="dict_engine"
                            %if nodenet and nodenet['engine']=="dict_engine":
                            selected="selected"
                            %end
                            >dict_engine</option>
                        </select>
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="nn_modulators">Emotional Modulators</label>
                    <div class="controls">
                        <input class="input-xlarge" id="nn_modulators" name="nn_modulators" type="checkbox" 
                        %if nodenet:
                            disabled="disabled"
                            %if nodenet['use_modulators']:
                                checked="checked"
                            %end
                        %end
                        />
                        <!-- <span class="help-inline">Deselect if this agent does not use the emotional model of the PSI Theory</span> -->
                    </div>
                </div>

                %if not nodenet:
                    <div class="control-group">
                        <label class="control-label" for="nn_template">Template</label>
                        <div class="controls">
                            <select class="input-xlarge" id="nn_template" name="nn_template">
                                <option value="">None</option>
                                %for uid in nodenets:
                                    %if nodenets[uid].owner == user_id:
                                            <option value="{{uid}}">{{nodenets[uid].name}}</option>
                                    %end
                                %end
                                % for uid in nodenets:
                                    %if nodenets[uid].owner != user_id:
                                        % if defined("template") and template == uid:
                            <option value="{{uid}}" selected="selected">{{nodenets[uid].name}}({{nodenets[uid].owner}})</option>
                                        %else:
                            <option value="{{uid}}">{{nodenets[uid].name}}({{nodenets[uid].owner}})</option>
                                        %end
                                    %end
                                %end
                            </select>
                        </div>
                    </div>
                %end

                <div class="control-group">
                    <label class="control-label" for="nn_world">Environment</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nn_world" name="nn_world" onchange="updateWorldAdapterSelector();">
                            <option value="">None</option>
                            % for uid in worlds:
                                % if worlds[uid].owner == user_id:
                                    % if nodenet and nodenet['world'] == uid:
                            <option value="{{uid}}" selected="selected">{{worlds[uid].name}}</option>
                                    %else:
                            <option value="{{uid}}">{{worlds[uid].name}}</option>
                                    %end
                                %end
                            %end
                            % for uid in worlds:
                                % if worlds[uid].owner != user_id:
                                   % if nodenet and nodenet['world'] == uid:
                            <option value="{{uid}}" selected="selected">{{worlds[uid].name}}</option>
                                    %else:
                            <option value="{{uid}}">{{worlds[uid].name}}</option>
                                    %end
                                %end
                            %end
                        </select>
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="nn_worldadapter">Worldadapter</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nn_worldadapter" name="nn_worldadapter">

                        </select>
                    </div>
                </div>

                %for type, data in worldtypes.items():
                    % for name, adapter in data['class'].get_supported_worldadapters().items():
                        % for param in adapter.get_config_options():
                            <div class="control-group worldadapter-config worldadapter-{{name}}" style="display:none">
                                <label class="control-label" for="worldadapter_config_{{name}}_{{param['name']}}">{{param['name']}}</label>
                                <div class="controls">
                                    % if param.get('options'):
                                    <select class="input-xlarge" id="worldadapter_config_{{name}}_{{param['name']}}" name="worldadapter_{{name}}_{{param['name']}}">
                                        % for val in param['options']:
                                            <option value="{{val}}"
                                            %if nodenet and nodenet['worldadapter_config'].get(param['name']) == val:
                                                selected="selected"
                                            %elif param.get('default') and param['default'] == val:
                                                selected="selected"
                                            %end
                                            >{{val}}</option>
                                        %end
                                    </select>
                                    %else:
                                    <input class="input-xlarge" id="world_config_{{name}}_{{param['name']}}" name="worldadapter_{{name}}_{{param['name']}}"
                                        type="text" value="{{nodenet['worldadapter_config'].get(param['name']) or param.get('default', '') if nodenet else param.get('default', '')}}" />
                                    %end
                                    %if param.get('description'):
                                        <div class="hint small">{{param['description']}}</div>

                                    %end
                                </div>
                            </div>
                        % end
                    %end
                %end
                <div class="control-group worldadapter-device-config" style="display:none;">
                    <label class="control-label">Devices</label>
                    % for uid in devices:
                        %if devices[uid]['online']:
                            <div class="controls">
                                <label class="inline" style="width: 150px">
                                    <input type="checkbox" name="device-map-{{uid}}" value="{{uid}}"
                                    % if nodenet and uid in nodenet['device_map']:
                                        checked="checked"
                                    % end
                                    /> {{devices[uid]['config']['name']}}
                                </label>
                                <input type="text" readonly="readonly" id="device-name-{{uid}}" name="device-name-{{uid}}" data-prefix="{{devices[uid]['prefix']}}" class="input-small device-name-input"
                                % if nodenet and uid in nodenet['device_map']:
                                    value="{{nodenet['device_map'][uid]}}"
                                %end
                                />
                            </div>
                        %end
                    % end
                </div>
            </fieldset>
    </div>

    <div class="modal-footer">
        <input type="hidden" name="nodenet_uid" value="{{nodenet['uid'] if nodenet else ''}}" />
        <button type="submit" class="btn btn-primary">Save</button>
        <a class="btn" data-dismiss="modal" href="/">Cancel</a>
    </div>

    </form>

</div>

<script type="text/javascript">

updateWorldAdapterSelector();
var device_section = $('.worldadapter-device-config');
var engine_field = $('#nn_engine');

function wa_changed(evt){
    var $el = $(event.target);
    var option_supports_devices = true;
    for(var i = 0; i < $el.children().length; i++){
        if($el.children()[i].selected){
            option_supports_devices = ($($el.children()[i]).data()['devices_supported'] == 'True');
            break;
        }
    }
    if($el.val() && engine_field.val() != "dict_engine" && option_supports_devices){
        device_section.show();
    } else {
        device_section.hide();
    }
}
$('#nn_world').on('world_form_refreshed', function(evt){
    $('#nn_worldadapter').on('change', wa_changed);
    if($(evt.target).val()){
        device_section.show();
    }
});

var assigned_prefixes = {};

var checkboxes = $('.worldadapter-device-config input[type="checkbox"]');
checkboxes.each(function(idx, el){
    var $el = $(el);
    $el.on('change', update_label);
    if(el.checked){
        var textfield = $('#device-name-'+$el.val());
        var prefix = textfield.data().prefix;
        if(!assigned_prefixes[prefix]){
            assigned_prefixes[prefix] = [];
        }
        assigned_prefixes[prefix].push(parseInt(textfield.val().substr(prefix.length + 1)));
    }
});


function update_label(event){
    var cb = $(event.target);
    var uid = cb.val();
    var textfield = $('#device-name-'+uid);
    var prefix = textfield.data().prefix;
    if(assigned_prefixes[prefix] && assigned_prefixes[prefix].length){
        assigned_prefixes[prefix].sort();
        if(cb[0].checked){
            // added:
            var maxidx = assigned_prefixes[prefix][assigned_prefixes[prefix].length -1];
            assigned_prefixes[prefix].push(maxidx + 1);
            textfield.val(prefix + "_" + (maxidx + 1).toString());
        } else {
            var key = textfield.val().substr(prefix.length + 1);
            var idx = assigned_prefixes[prefix].indexOf(parseInt(key));
            assigned_prefixes[prefix].splice(idx, 1);
            var reference;
            if(idx >= 0){
                for(var i = 0; i < assigned_prefixes[prefix].length; i++){
                    if(i >= idx - 1){
                        var newname = prefix + "_" + (i + 1);
                        $('.device-name-input').each(function(idx, el){
                            if($(el).val() == prefix + "_" + assigned_prefixes[prefix][i]){
                                $(el).val(newname);
                            }
                        });
                        assigned_prefixes[prefix][i] = i + 1;
                    }
                }
            }
            textfield.val('');
        }
    } else {
        if(cb[0].checked){
            assigned_prefixes[prefix] = [1];
            textfield.val(prefix + "_1");
        }
    }
}



</script>