%include menu.tpl version = version, permissions = permissions, user_id = user_id

<div class="row-fluid">
    % print nodenets
    <p>
    <h1>{{title}}</h1>
    </p>

    <div class="row-fluid">
        <form class="form-horizontal well" action="/edit_nodenet/" method="POST">
            %if defined('error') and error:
            <div class="alert alert-info">
                <b>Error:</b> {{error}}.
            </div>
            %end
            <fieldset>

                %if not defined("name_error"):
                <div class="control-group">
                %else:
                <div class="control-group error">
                %end
                    <label class="control-label" for="nodenet_name">Name</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge focused" maxlength="256" id="nodenet_name" name="nodenet_name"
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
                    <label class="control-label" for="nodenet_template">Template</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nodenet_template" name="nodenet_template">
                            <option value="None">None</option>
                            % if defined("nodenets"):
                                % for uid in nodenets:
                                    %if nodenets[uid].owner == user_id:
                                        % if defined("template") and template == uid:
                            <option value="{{uid}}" selected="selected">{{nodenets[uid].name}</option>
                                        %else:
                            <option value="{{uid}}">{{nodenets[uid].name}}</option>
                                        %end
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
                    <label class="control-label" for="nodenet_world">World</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nodenet_world" name="nodenet_world" onchange="updateWorldAdapterSelector();">
                            <option value="None">None</option>
                            % for uid in worlds:
                                % if worlds[uid].owner == user_id:
                                    % if defined("nodenet") and uid == nodenet.world.uid:
                            <option value="{{uid}}" selected="selected">{{worlds[uid].name}}</option>
                                    %else:
                            <option value="{{uid}}">{{worlds[uid].name}}</option>
                                    %end
                                %end
                            %end
                            % for uid in worlds:
                                % if worlds[uid].owner != user_id:
                                    % if defined ("nodenet") and defined ("nodenet.world.uid") and uid == nodenet.world.uid:
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
                    <label class="control-label" for="nodenet_worldadapter">World adapter</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nodenet_worldadapter" name="nodenet_worldadapter">
                            % if not defined("nodenet") or not defined ("nodenet.world.uid") or not nodenet.world.uid in worlds:
                            <option value="None">None</option>
                            % else:
                                %for worldadapter in worlds[nodenet.world.uid].worldadapters:
                        </select>
                    </div>
                </div>
            </fieldset>

            %if defined("nodenet"):
                <input type="hidden" name="nodenet_uid" value="{{nodenet.uid}}" />
            %end

            <button type="submit" class="btn btn-primary">Save</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>

%rebase boilerplate title = title
