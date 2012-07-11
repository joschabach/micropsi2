%include menu.tpl version = version, permissions = permissions, user = userid

<div class="row-fluid">
    <p>
    <h1>{{title}}</h1>
    </p>

    <div class="row-fluid">
        <form class="form-horizontal well" action="agent/edit" method="POST">
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
                    <label class="control-label" for="agent_name">Name</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge" maxlength="256" id="agent_name" name="agent_name"
                        %if defined('agent'):
                        value="{{agent.get('name', '')}}"
                        %end
                        />
                        %if defined("name_error"):
                        <span class="help-inline">{{name_error}}</span>
                        %end
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="agent_template">Template</label>
                    <div class="controls">
                        <select class="input-xlarge" id="agent_template" name="agent_template">
                            <option value="">None</option>
                            % for template in templates:
                                %if template == agent.get('template'):
                                    <option value="{{template}}" selected="selected">{{template}}</option>
                                %else:
                                    <option value="{{template}}">{{template}}</option>
                                %end
                            %end
                        </select>
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="agent_world">World</label>
                    <div class="controls">
                        <select class="input-xlarge" id="agent_world" name="agent_world">
                            <option value="">None</option>
                            % for world in worlds:
                                %if world == agent.get('world'):
                                    <option value="{{world}}" selected="selected">{{world}}</option>
                                %else:
                                    <option value="{{world}}">{{world}}</option>
                                %end
                            %end
                        </select>
                    </div>
                </div>

                <div class="control-group">
                    <label class="control-label" for="agent_worldadapter">World adapter</label>
                    <div class="controls">
                        <select class="input-xlarge" id="agent_worldadapter" name="agent_worldadapter">
                            <option value="">None</option>
                            % for adapter in worldadapters:
                                %if adapter == agent.get('worldadapter'):
                                    <option value="{{adapter}}" selected="selected">{{adapter}}</option>
                                %else:
                                    <option value="{{adapter}}">{{adapter}}</option>
                                %end
                            %end
                        </select>
                    </div>
                </div>
            </fieldset>

            %if agent.get('id'):
                <input type="hidden" name="agent_id" value="{{agent.get('id')}}" />
            %end

            <button type="submit" class="btn btn-primary">Save</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>


%rebase boilerplate title = title
