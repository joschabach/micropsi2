
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
                                <div class="btn-group" id="nodenet_list">
                                    <a class="btn" href="#">
                                        (no nodenet selected)
                                    </a>
                                </div>
                            </td>
                            <td> &nbsp; &nbsp; Nodespace:
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
                                    <i class="icon-share"></i>
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
                <td>
                    <table class="pull-right">
                        <tr>
                            <td style="white-space:nowrap;">
                                <div class="btn-group">
                                  <a href="#" id="nodenet_reset" class="btn" data-nodenet-control><i class="icon-fast-backward"></i></a>
                                  <a href="#" id="nodenet_start" class="btn" data-nodenet-control><i class="icon-play"></i></a>
                                  <a href="#" id="nodenet_step_forward" class="btn" data-nodenet-control><i class="icon-step-forward"></i></a>
                                  <a href="#" id="nodenet_stop" class="btn" data-nodenet-control><i class="icon-pause"></i></a>
                                </div>
                            </td>

                            <td align="right"><input id="nodenet_step" type="text" disabled="disabled"
                                                     style="text-align:right; width:60px;" value="0"/></td>

                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </form>
</div>


<div id="nodenet_editor" class="section-margin collapse in">
    <div class="nodenet section">
        <div class="editor_field span9">
            <canvas id="nodenet" width="700" height="100%" style="background:#eeeeee"></canvas>
        </div>
        <div class="editor_field " id="nodenet_forms">

            <form class="form-horizontal default_form hide" id="edit_nodenet_form">
                <h4>Nodenet</h4>
                <table>
                    <tr>
                        <td><label for="nodenet_uid">UID</label></td>
                        <td><input type="text" name="nodenet_uid" disabled="disabled" id="nodenet_uid"></td>
                    </tr>
                    <tr>
                        <td><label for="nodenet_name">Name</label></td>
                        <td><input type="text" name="nodenet_name" id="nodenet_name"></td>
                    </tr>
                    <tr>
                        <td><label for="nodenet_world">World</label></td>
                        <td><select name="nodenet_world" id="nodenet_world"></select></td>
                    </tr>
                    <tr>
                        <td><label for="nodenet_worldadapter">Worldadapter</label></td>
                        <td><select name="nodenet_worldadapter" id="nodenet_worldadapter"></select></td>
                    </tr>
                </table>
                <div class="controls">
                    <button type="submit" class="btn btn-primary">Apply</button>
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
                        <td><label for="nodespace_gatefunction_nodetype">Gatefunction</label></td>
                        <td><select name="nodespace_gatefunction_nodetype" id="nodespace_gatefunction_nodetype"></select></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                        <td><select name="nodespace_gatefunction_gate" id="nodespace_gatefunction_gate"></select></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                        <td><div class="pythoncode">
                                <div class="textareafake">
                                    <span class="loc">def gatefunction(x, r, t):</span>
                                    <span class="loc indent">import math</span>
                                    <div class="textarea indent1">
                                        <textarea class="loc" name="nodespace_gatefunction" id="nodespace_gatefunction"></textarea>
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>
                </table>
                <div class="controls">
                    <button type="submit" class="btn btn-primary">Apply</button>
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
                        <td><label for="link_certainty_input">Certainty</label></td>
                        <td><input type="text" class="" name="link_certainty" id="link_certainty_input"></td>
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
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>

            <form class="form-horizontal hide" id="edit_gate_form">
                <h4>Gate <span class="gate_gatetype"></span></h4>
                <table>
                    <tr>
                        <td><label for="gate_activation">Activation</label></td>
                        <td><input type="text" class="" name="activation" id="gate_activation" disabled="disabled"></td>
                    </tr>
                    <tr>
                        <td><label for="gate_minimum">Minimum</label></td>
                        <td><input type="text" class="" name="minimum" id="gate_minimum"></td>
                    </tr>
                    <tr>
                        <td><label for="gate_maximum">Maximum</label></td>
                        <td><input type="text" class="" name="maximum" id="gate_maximum"></td>
                    </tr>
                    <tr>
                        <td><label for="gate_certainty">Certainty</label></td>
                        <td><input type="text" class="" name="certainty" id="gate_certainty"></td>
                    </tr>
                    <tr>
                        <td><label for="gate_amplification">Amplification</label></td>
                        <td><input type="text" class="" name="amplification" id="gate_amplification"></td>
                    </tr>
                    <tr>
                        <td><label for="gate_threshold">Threshold</label></td>
                        <td><input type="text" class="" name="threshold" id="gate_threshold"></td>
                    </tr>
                    <tr>
                        <td><label for="gate_decay">Decay</label></td>
                        <td><input type="text" class="" name="decay" id="gate_decay"></td>
                    </tr>
                    <tr>
                        <td colspan="2"><a href="#" class="gate_additional_trigger">Show additional parameters</a> (for gatefunction)</td>
                    </tr>
                    <tr class="gate_additional hide">
                        <td><label for="gate_rho">Rho</label></td>
                        <td><input type="text" class="" name="rho" id="gate_rho"></td>
                    </tr>
                    <tr class="gate_additional hide">
                        <td><label for="gate_theta">Theta</label></td>
                        <td><input type="text" class="" name="theta" id="gate_theta"></td>
                    </tr>
                    <tr>
                        <td><label for="">Gatefunction</label></td>
                        <td>
                           <textarea name="gatefunction" id="" disabled="disabled"></textarea>
                        </td>
                    </tr>
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
                <div class="controls">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>


            <form class="form-horizontal hide" id="native_module_form">
                <h4>Native Module</h4>

                <fielset id="native_choose_type" class="native-default">
                    <p class="help-inline">You can either choose the type of this native module by choosing from an existing type...</p>
                    <div class="control-group">
                        <label class="control-label" for="native_type">Type</label>
                        <div class="controls">
                            <select id="native_type" name="native_type"></select>
                        </div>
                    </div>
                    <p class="help-inline">or you can create your own type:</p>
                    <div class="control-group">
                        <label class="control-label" for="native_new_type">Typename</label>
                        <div class="controls">
                            <input id="native_new_type" name="native_new_type" type="text"/>
                        </div>
                     </div>
                </fielset>
                <fieldset id="native_basics" class="native-details native-template hide">
                    <div class="control-group">
                        <label class="control-label" for="native_name">Name</label>
                        <div class="controls">
                            <input id="native_name" name="native_name" type="text"/>
                        </div>
                    </div>
                    <div class="control-group">
                        <label class="control-label" for="native_params">Parameters</label>
                        <div class="controls">
                            <table id="native_parameters" class="table-striped table-condensed">
                            </table>
                            <a href="#" class="btn btn-mini" id="native_add_param">add parameter</a>
                        </div>
                    </div>
                </fieldset>
                <fieldset id="native_typedef"  class="native-details native-custom hide">
                    <div class="control-group">
                        <label class="control-label" for="native_function">Nodefunction</label>
                        <div class="controls dropdown">
                            <code>def nodefunction(nodenet, node
                                <span id="params"></span>
                                ):
                            </code>
                           <textarea name="native_function" id="native_function"></textarea>
                        </div>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Slots and Gates</label>
                        <div class="controls">
                            <table id="native_slots_gates" class="table-striped table-condensed">
                                <tr><th>Type</th><th>Slot</th><th>Gate</th></tr>
                                <tr><td>gen</td>
                                    <td><input type="checkbox" name="gen_slot"/></td>
                                    <td><input type="checkbox" name="gen_gate"/></td>
                                </tr>
                                <tr><td>por/ret</td>
                                    <td><input type="checkbox" name="por_slot"/></td>
                                    <td><input type="checkbox" name="por_gate"/></td>
                                </tr>
                                <tr><td>sub/sur</td>
                                    <td><input type="checkbox" name="sub_slot"/></td>
                                    <td><input type="checkbox" name="sub_gate"/></td>
                                </tr>
                                <tr><td>is-a/exp</td>
                                    <td><input type="checkbox" name="isa_slot"/></td>
                                    <td><input type="checkbox" name="isa_gate"/></td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </fieldset>
                <div class="controls buttons">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>

        </div>
    </div>
    <div class="seperator" style="text-align:center;"><a class="resizeHandle" id="nodenetSizeHandle"> </a></div>
</div>
<div class="sectionbar">
    <form class="navbar-form">
        <table>
            <tr>
                <td><span data-toggle="collapse" data-target="#monitor, #monitor_controls"><i
                        class="icon-chevron-right"></i></span></td>

                <td data-toggle="collapse" data-target="#monitor, #monitor_controls"> Nodenet Monitor &nbsp;</td>

                <td><div class="collapse" id="monitor_controls">
                    <button class="btn">Clear</button>
                </div></td>

            </tr>
        </table>
    </form>
</div>

<div id="monitor" class="section-margin collapse">
    <div class="section">
        <div class="monitor_field span9">
            <div id="graph"></div>
        </div>
        <div class="editor_field monitor_field " id="monitor_legend">
            <form class="form-horizontal">
                <h4>Current Monitors</h4>
                <div id="monitor_list">
                </div>
            </form>
        </div>
    </div>
</div>



<div class="dropdown" id="node_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#node_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
    </ul>
</div>

<div class="dropdown" id="link_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#link_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
        <li><a href="#">Edit link</a></li>
        <li><a href="#">Delete link</a></li>
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
        <a href="#" class="btn" data-dismiss="modal">Close</a>
        <a href="#" class="btn btn-primary">Apply changes</a>
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
        <a href="#" class="btn" data-dismiss="modal">Cancel</a>
        <a href="#" class="btn btn-primary">Create</a>
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
        <a href="#" class="btn" data-dismiss="modal">Close</a>
        <a href="#" class="btn btn-primary">Apply</a>
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
        <a href="#" class="btn" data-dismiss="modal">Close</a>
        <a href="#" class="btn btn-primary">Apply</a>
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
        <a href="#" class="btn" data-dismiss="modal">Cancel</a>
        <a href="#" class="btn btn-primary">Create</a>
    </div>
</div>

<script src="/static/js/d3.v2.min.js" type="text/javascript"></script>
<script src="/static/js/monitor.js" type="text/javascript"></script>
<script src="/static/js/nodenet.js" type="text/paperscript" canvas="nodenet"></script>
