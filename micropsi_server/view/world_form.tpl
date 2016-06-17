
<div class="dialogform modal">

    <form class="form-horizontal" action="/world/edit" method="POST">

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
                    <label class="control-label" for="world_name">Name</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge" maxlength="256" id="world_name" name="world_name"
                        %if defined('world'):
                        value="{{world.name}}"
                        %end
                        />
                        %if defined("name_error"):
                        <span class="help-inline">{{name_error}}</span>
                        %end
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="world_type">Type</label>
                    <div class="controls">
                        <select class="input-xlarge" id="world_type" name="world_type">
                            <option value="">None</option>
                            % for type in worldtypes:
                                %if defined("world") and type == world.type:
                                    <option value="{{type}}" selected="selected">{{type}}</option>
                                %else:
                                    <option value="{{type}}">{{type}}</option>
                                %end
                            %end
                        </select>
                        % for type in worldtypes:
                            <div class="hint small world_docstring world_docstring_{{type}}" style="display:none; white-space: pre-wrap;">{{(worldtypes[type].__doc__ or '').strip()}}</div>
                        %end
                    </div>
                </div>

                %for type in worldtypes:
                    % for param in worldtypes[type].get_config_options():
                    <div class="control-group world_config world_config_{{type}}" style="display:none">
                        <label class="control-label" for="world_config_{{type}}_{{param['name']}}">{{param['name']}}</label>
                        <div class="controls">
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
                            %if param.get('description'):
                                <div class="hint small">{{param['description']}}</div>

                            %end
                        </div>
                    </div>
                    %end
                %end


            %if defined("world"):
                <input type="hidden" name="world_uid" value="{{world.uid}}" />
            %end

            </fieldset>
    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Save</button>
        <a class="btn" data-dismiss="modal">Cancel</a>
    </div>

    </form>

</div>

<script type="text/javascript">
$('#world_type').on('change', function(event){
    var val = $(event.target).val();
    $('.world_config').hide();
    $('.world_config_'+val).show();
    $('.world_docstring').hide();
    $('.world_docstring_'+val).show();
})
</script>