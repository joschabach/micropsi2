<div class="dialogform modal">

    <form class="form-horizontal" action="/agent/edit" method="POST">

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
                        %if defined('nodenet_uid'):
                        value="{{nodenets[nodenet_uid].name}}"
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
                        <select class="input-xlarge" id="nn_engine" name="nn_engine">
                            %if theano_available:
                            <option value="theano_engine">theano_engine</option>
                            %end
                            <option value="dict_engine">dict_engine</option>
                        </select>
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="nn_modulators">Emotional Modulators</label>
                    <div class="controls">
                        <input class="input-xlarge" id="nn_modulators" name="nn_modulators" type="checkbox" />
                        <!-- <span class="help-inline">Deselect if this agent does not use the emotional model of the PSI Theory</span> -->
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="nn_template">Template</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nn_template" name="nn_template">
                            <option value="">None</option>
                            %if defined("nodenets"):
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
                            %end
                        </select>
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="nn_world">Environment</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nn_world" name="nn_world" onchange="updateWorldAdapterSelector();">
                            <option value="">None</option>
                            % for uid in worlds:
                                % if worlds[uid].owner == user_id:
                                    % if defined("nodenet") and uid == nodenet.world:
                            <option value="{{uid}}" selected="selected">{{worlds[uid].name}}</option>
                                    %else:
                            <option value="{{uid}}">{{worlds[uid].name}}</option>
                                    %end
                                %end
                            %end
                            % for uid in worlds:
                                % if worlds[uid].owner != user_id:
                                    % if defined ("nodenet") and defined ("nodenet.world") and uid == nodenet.world:
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
                            % if not defined("nodenet") or not defined ("nodenet.world") or not nodenet.world in worlds:
                            <option value="">None</option>
                            % else:
                                %for worldadapter in worlds[nodenet.world].worldadapters:
                                    <!-- TODO -->
                                    <option>{{worldadapter}}</option>
                                %end
                            % end
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
                                            %if param.get('default') and param['default'] == val:
                                                selected="selected"
                                            %end
                                            >{{val}}</option>
                                        %end
                                    </select>
                                    %else:
                                    <input class="input-xlarge" id="world_config_{{name}}_{{param['name']}}" name="worldadapter_{{name}}_{{param['name']}}"
                                        type="text" value="{{param.get('default', '')}}" />
                                    %end
                                    %if param.get('description'):
                                        <div class="hint small">{{param['description']}}</div>

                                    %end
                                </div>
                            </div>
                        % end
                    %end
                %end


            </fieldset>
    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Save</button>
        <a class="btn" data-dismiss="modal" href="/">Cancel</a>
    </div>

    </form>

</div>
