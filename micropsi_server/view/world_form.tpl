%include menu.tpl version = version, permissions = permissions, user_id = user_id

<div class="row-fluid">
    <p>
    <h1>{{title}}</h1>
    </p>

    <div class="row-fluid">
        <form class="form-horizontal well" action="world/edit" method="POST">
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
                    </div>
                </div>

            %if defined("world"):
                <input type="hidden" name="world_uid" value="{{world.uid}}" />
            %end

            <button type="submit" class="btn btn-primary">Save</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>


%rebase boilerplate title = title
