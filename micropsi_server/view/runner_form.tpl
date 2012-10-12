
<div class="dialogform modal">

    <form class="form-horizontal" action="{{action}}" method="POST">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>Timestep for {{mode}}runner</h3>
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
                    <label class="control-label" for="runner_timestep">Interval in milliseconds</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge" maxlength="256" id="runner_timestep" name="runner_timestep" value="{{value}}" />
                        %if defined("name_error"):
                        <span class="help-inline">{{name_error}}</span>
                        %else:
                        <span class="help-inline">The runner will update the {{mode}} in the respective interval</span>
                        %end
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
