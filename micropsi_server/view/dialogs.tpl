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
      <h3>Agent runner interrupted</h3>
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
                <div class="control-group all_monitors">
                    <label class="control-label" for="monitor_name_input">Name</label>
                    <div class="controls">
                        <input type="text" name="monitor_name_input"class="input-xlarge" id="monitor_name_input">
                    </div>
                </div>
                <div class="control-group custom_monitor">
                    <label class="control-label" for="monitor_code_input">Function</label>
                    <div class="controls">
                        <textarea name="monitor_code_input" class="input-xlarge monospace" id="monitor_code_input" rows="10"></textarea>
                        <p class="help-block">You can enter custom python code returning a float for each step. You have access to the netapi.</p>
                    </div>
                </div>
                <input type="hidden" id="monitor_node_input" name="monitor_node_input"/>
                <div class="control-group node_monitor">
                    <label class="control-label">Type</label>
                    <div class="controls">
                        <label><input type="radio" id="monitor_node_type_gate" name="monitor_node_type"/> Gate Monitor</label>
                        <label><input type="radio" id="monitor_node_type_slot" name="monitor_node_type"/> Slot Monitor</label>
                    </div>
                </div>
                <div class="control-group gate_monitor">
                    <label class="control-label" for="monitor_gate_input">Gate</label>
                    <div class="controls">
                        <select id="monitor_gate_input" name="monitor_gate_input"></select>
                    </div>
                </div>
                <div class="control-group slot_monitor">
                    <label class="control-label" for="monitor_slot_input">Slot</label>
                    <div class="controls">
                        <select id="monitor_slot_input" name="monitor_slot_input"></select>
                    </div>
                </div>
                <div class="control-group modulator_monitor">
                    <label class="control-label" for="monitor_modulator_input">Modulator</label>
                    <div class="controls">
                        <input type="text" id="monitor_modulator_input" name="monitor_modulator_input" />
                    </div>
                </div>
                <div class="control-group link_monitor">
                    <label class="control-label" for="monitor_link_input">Link</label>
                    <div class="controls">
                        <input type="text" id="monitor_link_input" name="monitor_link_input"/>
                    </div>
                    <input type="hidden" name="monitor_link_sourcenode_uid_input" id="monitor_link_sourcenode_uid_input">
                    <input type="hidden" name="monitor_link_sourcegate_type_input" id="monitor_link_sourcegate_type_input">
                    <input type="hidden" name="monitor_link_targetnode_uid_input" id="monitor_link_targetnode_uid_input">
                    <input type="hidden" name="monitor_link_targetslot_type_input" id="monitor_link_targetslot_type_input">
                </div>
                <div class="control-group all_monitors">
                    <label class="control-label" for="monitor_color_input">Color</label>
                    <div class="controls color-chooser">
                        <span class="input-group-addon"><i></i></span>
                        <input type="text" id="monitor_color_input" name="monitor_color_input" value="#990000"/>
                    </div>
                </div>
                <input type="hidden" name="monitor_type" id="monitor_type"/>
                <input type="hidden" name="monitor_node_uid_input" id="monitor_node_uid_input"/>
            </fieldset>
            <input type="submit" style="display:none"/>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Save</button>
    </div>
</div>

<div class="modal hide" id="recipe_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Run Recipe</h3>
    </div>
    <div class="modal-body" style="min-height:400px">
        <p class="default_explanation">You can place a python file with useful functions called "recipes.py" in your resource directory (next to nodefunctions.py) and run them via this dialog. All functions must have the netapi as their first mandatory parameter, and can define additional parameters which you can then specify in this dialog</p>
        <p class="docstring"></p>
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="recipe_name_input">Name</label>
                    <div class="controls">
                        <select name="recipe_name_input" class="input-xlarge" id="recipe_name_input">
                        </select>
                    </div>
                </div>
            </fieldset>
            <fieldset class="recipe_param_container">
            </fieldset>
            <input type="submit" style="display:none"/>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Run</button>
    </div>
</div>

<div class="modal hide" id="operations-modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3></h3>
    </div>
    <div class="modal-body">
        <p class="docstring"></p>
        <form class="form-horizontal">
            <fieldset></fieldset>
            <input type="submit" style="display:none"/>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Run</button>
    </div>
</div>

<div id="recipe_result" class="modal hide">
    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>Result</h3>
    </div>
    <div class="modal-body">
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
    </div>
</div>

<div class="modal hide" id="run_nodenet_dialog">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Run Agent</h3>
    </div>
    <div class="modal-body">
        <p>Run the agent until one of the following conditions is met:</p>
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="run_condition_steps">Number of steps</label>
                    <div class="controls">
                        <input type="text" name="run_condition_steps" class="input-xlarge" id="run_condition_steps"/>
                        <p class="help-block">Run until the agent was advanced for X number of steps</p>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="run_condition_monitor_value">Monitor value</label>
                    <div class="controls">
                        <select id="run_condition_monitor_selector"></select>
                        <input type="text" name="run_condition_monitor_value" class="input-mini" id="run_condition_monitor_value"/>
                        <p class="help-block">Run until the given monitor has the given value.</p>
                    </div>
                </div>
            </fieldset>
            <fieldset class="recipe_param_container">
            </fieldset>
            <input type="submit" style="display:none"/>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Save</button>
    </div>
</div>
