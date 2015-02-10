<div id="confirm_dialog" class="modal hide">
    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>Confirmation</h3>
    </div>
    <div class="modal-body">
        <p class="message"></p>
    </div>
    <div class="modal-footer">
      <a href="#" class="btn" data-dismiss="modal">Close</a>
      <a href="#" class="btn-confirm btn btn-primary">Continue</a>
    </div>
</div>

<div id="remote_form_dialog" class="hide">
</div>

<div id="notification" class="notifications top-center">
</div>


<div id="nodenet_user_prompt" class="modal hide">
    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>Nodenet interrupted</h3>
    </div>
    <div class="modal-body">
    </div>
    <div class="modal-footer">
      <a href="#" class="btn-confirm btn btn-primary">Confirm</a>
    </div>
</div>

<div class="modal hide" id="monitor_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Add Monitor</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="monitor_name_input">Name</label>
                    <div class="controls">
                        <input type="text" name="monitor_name_input"class="input-xlarge" id="monitor_name_input">
                        <p class="help-block">If you do not give the net entity a name, it will be referred by its uid.</p>
                    </div>
                </div>
                <div class="control-group custom_monitor">
                    <label class="control-label" for="monitor_code_input">Function</label>
                    <div class="controls">
                        <textarea name="monitor_code_input" class="input-xlarge monospace" id="monitor_code_input" rows="10"></textarea>
                        <p class="help-block">You can enter custom python code returning a float for each step. You have access to the netapi.</p>
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Save</button>
    </div>
</div>