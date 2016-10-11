
<div class="sectionbar">
    <form class="navbar-form">
        <table width="100%">
            <tr>
                <td>
                    <table>
                        <tr>
                            <td><span data-toggle="collapse" data-target="#nodenet_editor"><i
                                    class="icon-chevron-right"></i></span></td>

                            <td>
                                <div class="btn-group nodenet_list">
                                    <a class="btn" href="#">
                                        (no agent selected)
                                    </a>
                                </div>
                            </td>
                            <td> &nbsp; &nbsp; Nodespace:
                            </td>
                            <td>
                                <a href="#" id="nodespace_add" title="Add new nodespace" class="btn" data-nodenet-control>
                                    <i class="icon-plus-sign"></i>
                                </a>
                            </td>
                            <td style="white-space:nowrap;">
                                <div id="nodespace_control" class="btn-group">
                                    <a href="#" class="btn dropdown-toggle" data-toggle="dropdown" data-nodenet-control>
                                        <span id="current_nodespace_name">Root</span>
                                        <b class="caret"></b>
                                    </a>
                                    <ul class="dropdown-menu">
                                    </ul>
                                </div>
                            </td>
                            <td>
                                <a href="#" id="nodespace_up" title="Go to parent nodespace" class="btn" data-nodenet-control>
                                    <i class="icon-eject"></i>
                                </a>
                            </td>
                            <td> &nbsp; &nbsp; Zoom:</td>
                            <td>
                                <div class="btn-group" id="nodenet_list">
                                    <a class="btn" id="zoomIn" href="#" data-nodenet-control>+</a>
                                    <a class="btn" id="zoomOut" href="#" data-nodenet-control>-</a>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </form>
</div>


<div id="nodenet_editor" class="section-margin frontend_section collapse in">
    <div class="nodenet section">
        <div class="editor_field span9">
            <canvas id="nodenet" width="700" height="100%" style="background:#eeeeee"></canvas>
        </div>
        <div class="editor_field " id="nodenet_forms">

            <form class="form-horizontal default_form hide" id="edit_nodenet_form">
                <h4>Agent</h4>
                <table>
                    <tr>
                        <td><label for="nodenet_uid">UID</label></td>
                        <td><input type="text" name="nodenet_uid" disabled="disabled" id="nodenet_uid"></td>
                    </tr>
                    <tr>
                        <td><label for="nodenet_nodenet_name">Name</label></td>
                        <td><input type="text" name="nodenet_nodenet_name" id="nodenet_nodenet_name"></td>
                    </tr>
                    <tr>
                        <td><label for="nodenet_world_uid">Environment</label></td>
                        <td><select name="nodenet_world_uid" id="nodenet_world_uid"></select></td>
                    </tr>
                    <tr>
                        <td><label for="nodenet_worldadapter">Worldadapter</label></td>
                        <td><select name="nodenet_worldadapter" id="nodenet_worldadapter"></select></td>
                    </tr>
                    <tr>
                        <td colspan="2" class="worldadapter_config">
                    </tr>
                    <tr>
                        <td><label for="ui_snap">Snap to grid</label></td>
                        <td><input type="checkbox" name="ui_snap" id="ui_snap" /></td>
                    </tr>
                </table>
                <div class="controls">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
                <p>&nbsp;</p>
                <div class="modulators_container">
                    <strong>global modulators</strong>
                    <table class="modulators table-striped table-condensed">
                    </table>
                </div>
            </form>

            <form class="form-horizontal default_form hide" id="edit_nodespace_form">
                <h4>Nodespace</h4>
                <table>
                    <tr>
                        <td><label for="nodespace_uid">UID</label></td>
                        <td><input type="text" name="nodespace_uid" disabled="disabled" id="nodespace_uid"></td>
                    </tr>
                    <tr>
                        <td><label for="nodespace_name">Name</label></td>
                        <td><input type="text" name="nodespace_name" id="nodespace_name"></td>
                    </tr>
                    <tr>
                        <td><label for="nodespace_renderlinks">render links</label></td>
                        <td><select name="nodespace_renderlinks" type="checkbox" name="nodespace_renderlinks" id="nodespace_renderlinks">
                            <option value="always">always</option>
                            <option value="selection">on selected nodes</option>
                            <option value="no">never</opeion>
                        </select></td>
                    </tr>
                    <tr>
                        <td><label for="nodespace_activation_display">activation display</label></td>
                        <td><select name="nodespace_activation_display" type="checkbox" name="nodespace_activation_display" id="nodespace_activation_display">
                            <option value="redgreen">red / green</option>
                            <option value="alpha">opacity / green</option>
                        </select></td>
                    </tr>
                </table>
                <div class="controls">
                    <button type="submit" class="btn btn-primary">Apply</button>
                    <button type="button" id="delete_nodespace" class="btn btn-danger">Delete</button>
                </div>
            </form>

            <form class="form-horizontal hide" id="edit_link_form">
                <h4>Link</h4>
                <table class="table-condensed">
                    <tr>
                        <td><label for="link_weight_input">Weight</label></td>
                        <td><input type="text" class="" name="link_weight" id="link_weight_input"></td>
                    </tr>
                    <tr>
                        <td><label>Source</label></td>
                        <td class="link_source_node"></td>
                    </tr>
                    <tr>
                        <td><label>Target</label></td>
                        <td class="link_target_node"></td>
                    </tr>
                </table>
                <div class="controls">
                    <button type="button" class="deleteLink btn btn-danger btn-mini">Delete link</button>
                    <button type="submit" class="saveLink btn btn-primary">Apply</button>
                </div>
            </form>

            <form class="form-horizontal hide" id="edit_gate_form">
                <h4>Gate <span class="gate_gatetype"></span></h4>
                <p class="highdim"></p>
                <table>
                    <tbody>
                        <tr>
                            <td><label for="gate_activation">Activation</label></td>
                            <td><input type="text" class="" name="activation" id="gate_activation" disabled="disabled"></td>
                        </tr>
                        <tr>
                            <td><label for="">Gatefunction</label></td>
                            <td>
                               <select name="gate_gatefunction" id="gate_gatefunction">
                               </select>
                            </td>
                        </tr>
                    </tbody>
                    <tbody id="gatefunction_param_container">
                    </tbody>
                </table>
                <div class="controls">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>

            <form class="form-horizontal hide" id="edit_node_form">
                <h4>Node</h4>
                <table class="table-condensed">
                    <tr>
                        <td><label for="node_uid_input">UID</label></td>
                        <td><input type="text" disabled="disabled" id="node_uid_input" /></td>
                    </tr>
                    <tr>
                        <td><label for="node_name_input">Name</label></td>
                        <td><input type="text" name="node_name" id="node_name_input"></td>
                    </tr>
                    <tr>
                        <td><label for="node_type_input">Type</label></td>
                        <td><input type="text" name="node_type" disabled="disabled" id="node_type_input" /></td>
                    </tr>
                    <tr class="comment">
                        <td><label for="node_comment_input">Content</label></td>
                        <td><textarea name="node_comment" id="node_comment_input" rows="5" cols="25"></textarea></td>
                    </tr>
                    <tr class="state node">
                        <td><label for="node_state_input">State</label></td>
                        <td><select type="text" name="node_state" id="node_state_input"></select></td>
                    </tr>
                    <tr class="node">
                        <td><label for="node_activation_input">Activation</label></td>
                        <td><input type="text" name="node_activation" id="node_activation_input"></td>
                    </tr>
                    <tr class="node">
                        <td><label>Parameters</label></td>
                        <td><table id="node_parameters" class="table-striped table-condensed">
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td> &nbsp;</td>
                        <td>
                            <button type="submit" class="btn btn-primary">Apply</button>
                        </td>
                    </tr>

                    <tr class="node">
                        <td><label>in links</label></td>
                        <td><table id="node_slots" class="table-striped table-condensed">
                            </table>
                        </td>
                    </tr>
                    <tr class="node">
                        <td><label>out links</label></td>
                        <td><table id="node_gates" class="table-striped table-condensed">
                            </table>
                        </td>
                    </tr>
                </table>
            </form>

        </div>
    </div>
    <div class="seperator" style="text-align:center;"><a class="resizeHandle" id="nodenetSizeHandle"> </a></div>
</div>

% if console:
    % include("netapi_console")
% end

<div class="dropdown" id="node_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#node_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
    </ul>
</div>

<div class="dropdown" id="multi_node_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#multi_node_menu"></a>
    <ul class="nodenet_menu dropdown-menu all_nodes">
    </ul>
</div>

<div class="dropdown" id="link_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#link_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
        <li><a href="#">Delete link</a></li>
        <li><a data-add-monitor href="#">Add link-weight monitor</a></li>
        <li><a data-remove-monitor href="#">Remove link monitor</a></li>
    </ul>
</div>

<div class="dropdown" id="slot_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#slot_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
        <li><a href="#" data-add-monitor>Add monitor to slot</a></li>
        <li><a href="#" data-remove-monitor>Remove monitor from slot</a></li>
    </ul>
</div>

<div class="dropdown" id="gate_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#gate_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
        <li><a href="#">Draw link</a></li>
        <li><a href="#" data-add-monitor>Add monitor to gate</a></li>
        <li><a href="#" data-remove-monitor>Remove monitor from gate</a></li>
    </ul>
</div>

<div class="dropdown" id="create_node_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#create_node_menu"></a>
    <ul class="nodenet_menu dropdown-menu" data-nodetype-entries>
    </ul>
</div>

<div class="modal hide" id="rename_node_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Rename net entity</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="rename_node_input">Node name</label>
                    <div class="controls">
                        <input type="text" name="node_name"class="input-xlarge" id="rename_node_input">
                        <p class="help-block">If you do not give the net entity a name, it will be referred by its uid.</p>
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Apply changes</button>
    </div>
</div>


<div class="modal hide" id="copy_paste_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3 class="title"></h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <div class="control-group">
                <fieldset>
                    <textarea id="copy_paste_text"></textarea>
                </fieldset>
            </div>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
    </div>
</div>


<div class="modal hide" id="create_link_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Create a link</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="link_source_gate">Source Gate</label>
                    <div class="controls">
                        <select name="source_gate" id="link_source_gate">
                        </select>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="link_target_nodespace">Nodespace</label>
                    <div class="controls">
                        <select name="target_nodespace" id="link_target_nodespace">
                        </select>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="link_target_node">Target Node</label>
                    <div class="controls">
                        <select name="target_node" id="link_target_node">
                        </select>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="link_target_slot">Target Slot</label>
                    <div class="controls">
                        <select data-nodespace name="target_slot" id="link_target_slot">
                        </select>
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Cancel</button>
        <button class="btn btn-primary">Create</button>
    </div>
</div>


<div class="modal hide edit_node_modal" id="select_datasource_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Select datasource</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="datasource_select">Datasource</label>
                    <div class="controls">
                        <select class="input-xlarge" id="datasource_select">
                        </select>
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Apply</button>
    </div>
</div>
<div class="modal hide" id="select_datatarget_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Select datatarget</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="datatarget_select">Datatarget</label>
                    <div class="controls">
                        <select class="input-xlarge" id="datatarget_select">
                        </select>
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Apply</button>
    </div>
</div>

<div class="modal hide" id="paste_mode_selection_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Paste Nodes</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="paste_mode_selection">Do you also want to copy the links?</label>
                    <div class="controls">
                        <label for="past_mode_all">
                            <input type="radio" name="past_mode" class="input-xlarge" value="all" id="past_mode_all"/>
                            Copy all links
                        </label>
                        <label for="past_mode_internal">
                            <input type="radio" checked="checked" name="past_mode" class="input-xlarge" value="internal" id="past_mode_internal"/>
                            Copy links within selection only
                        </label>
                        <label for="past_mode_none">
                            <input type="radio" name="past_mode" class="input-xlarge" value="none" id="past_mode_none"/>
                            Do not copy links
                        </label>
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Cancel</button>
        <button class="btn btn-primary">Apply</button>
    </div>
</div>
<div class="modal hide" id="edit_native_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Native module</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="native_module_type">Type</label>
                    <div class="controls">
                        <select name="type" id="native_module_type" data-native-module-type>
                        </select>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="native_module_name">Name</label>
                    <div class="controls">
                        <input name="name" type="text" id="native_module_name" />
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer native-default">
        <button class="btn" data-dismiss="modal">Cancel</button>
        <button class="btn btn-primary">Create</button>
    </div>
</div>

<script src="/static/js/nodenet.js" type="text/paperscript" canvas="nodenet"></script>
