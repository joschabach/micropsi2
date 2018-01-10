
<div class="dialogform modal">

    <form class="form-horizontal" action="{{action}}" method="POST">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>Runner Properties</h3>
    </div>

    <div class="modal-body">

            %if defined('error') and error:
            <div class="alert alert-info">
                <b>Error:</b> {{error}}.
            </div>
            %end

            <fieldset class="well">
                <p>Runner</p>

                %if not defined("name_error"):
                <div class="control-group">
                %else:
                <div class="control-group error">
                %end
                    <label class="control-label" for="timestep">Interval in milliseconds</label>
                    <div class="controls">
                        <input type="text" class="input-medium" maxlength="256" id="timestep" name="timestep" value="{{value['timestep']}}" />
                        %if defined("name_error"):
                        <span class="help-inline">{{name_error}}</span>
                        %end
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="infguard">NaN/Inf Guard</label>
                    <div class="controls">
                        <input type="checkbox" class="input-medium" id="infguard" name="infguard"
                        %if 'infguard' in value and value['infguard']:
                            checked="checked"
                        %end
                        />
                        <span class="help-inline hint small">Stop runner if NaNs detected in flow</span>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="profile_nodenet">Profile nodenet</label>
                    <div class="controls">
                        <input type="checkbox" class="input-medium" id="profile_nodenet" name="profile_nodenet"
                        %if 'profile_nodenet' in value and value['profile_nodenet']:
                            checked="checked"
                        %end
                        />
                        <span class="help-inline hint small">Log profile info for nodenet</span>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="profile_world">Profile world</label>
                    <div class="controls">
                        <input type="checkbox" class="input-medium" id="profile_world" name="profile_world"
                        %if 'profile_world' in value and value['profile_world']:
                            checked="checked"
                        %end
                        />
                        <span class="help-inline hint small">Log profile info for world</span>
                    </div>
                </div>
             </fieldset>
             <fieldset class="well">
                <p>Logging</p>
                % for name in ["system", "world", "agent"]:
                    <div class="control-group">
                        <label class="control-label" for="log_level_{{name}}">{{name}}</label>
                        <div class="controls">
                            <select id="log_level_{{name}}" name="log_level_{{name}}" class="input-medium">
                                % for lvl in ["debug", "info", "warning", "error", "critical"]:
                                    <option
                                    % if lvl.upper() == value['log_levels'][name].upper():
                                        selected = "selected"
                                    %end
                                    >{{lvl}}</option>
                                %end
                            </select>
                        </div>
                    </div>
                %end
                <div class="control-group">
                    <label class="control-label" for="log_file">Logfile</label>
                    <div class="controls">
                        <input type="text" class="input-medium" id="log_file" name="log_file" value="{{value['log_file'] or ''}}"
                        />
                    </div>
                </div>
            </fieldset>
    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Save</button>
        <a class="btn" data-dismiss="modal">Cancel</a>
    </div>

    </form>

</div>
