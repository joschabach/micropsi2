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
        </div>
</div>