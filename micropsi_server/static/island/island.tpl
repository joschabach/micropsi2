<div>
        <div class="editor_field span9">
            <canvas id="world" width="700" height="500" style="background:#eeeeee"></canvas>
        </div>

        <div class="editor_field " id="world_forms">
            <form class="form-horizontal form-default">
                <h4>World Status</h4>
                <textarea disabled="disabled" id="world_status" rows="4" cols="60" class="input-xlarge"></textarea>
            </form>
            <form class="form-horizontal form-default scene_viewer_section">
                <h4>Scene Viewer</h4>
                <p>
                    <label for="scene_viewer_agent">Agent</label>
                    <select id="scene_viewer_agent"></select>
                <div id="scene_viewer">
                </div>
            </form>
            <form class="form-horizontal form-default" id="world_objects">
                <h4>Agents</h4>
                <div id="world_agents_list">
                    <table class="table-striped table-condensed"></table>
                </div>
                <h4>World Objects</h4>
                <div id="world_objects_list">
                    <select id="available_worldobjects">
                    </select>
                    <button id="set_worldobject_sprinkle_mode" class="btn">add Objects</button>
                </div>
                <div id="world_objects_icons" style="height:0; overflow:hidden;"></div>
            </form>

            <form class="form-horizontal hide" id="edit_worldobject">
                <h4>World Object</h4>
                <table class="table-condensed">
                    <tr>
                        <td><label for="wo_uid_input">Uid</label></td>
                        <td><input type="text" class="" name="wo_uid" id="wo_uid_input" /></td>
                    </tr>
                    <tr>
                        <td><label for="wo_name_input">Name</label></td>
                        <td><input type="text" class="" name="wo_name" id="wo_name_input" /></td>
                    </tr>
                    <tr>
                        <td><label>Parameters</label></td>
                        <td class="wo_parameters"><table id="wo_parameter_list"></table>
                            <button id="add_object_param">Add parameter</button></td>
                    </tr>
                </table>
                <div class="controls">
                    <button type="reset" class="btn">Cancel</button>
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>
        </div>
</div>