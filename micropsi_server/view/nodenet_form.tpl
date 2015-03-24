<div class="dialogform modal">

    <form class="form-horizontal" action="/nodenet/edit" method="POST">

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
                            <option value="dict_engine">dict_engine</option>
                            %if theano_available:
                            <option value="theano_engine">theano_engine (experimental)</option>
                            %end
                        </select>
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
                    <label class="control-label" for="nn_world">World</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nn_world" name="nn_world" onchange="updateWorldAdapterSelector();">
                            <option value="">None</option>
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
                    <label class="control-label" for="nn_worldadapter">World adapter</label>
                    <div class="controls">
                        <select class="input-xlarge" id="nn_worldadapter" name="nn_worldadapter">
                            % if not defined("nodenet") or not defined ("nodenet.world.uid") or not nodenet.world.uid in worlds:
                            <option value="">None</option>
                            % else:
                                %for worldadapter in worlds[nodenet.world.uid].worldadapters:
                                    <!-- TODO -->
                                    <option>{{worldadapter}}</option>
                                %end
                            % end
                        </select>
                    </div>
                </div>

            </fieldset>
    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Save</button>
        <a class="btn" data-dismiss="modal" href="/">Cancel</a>
    </div>

    </form>

</div>

