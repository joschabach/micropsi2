
%include menu.tpl version = version, user_id = user_id, permissions = permissions

<div class="row-fluid">
    <div class="sectionbar">
        <form class="navbar-form">
            <table width="100%">
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td><span data-toggle="collapse" data-target="#nodenet_editor, #nodespace_control"><i
                                        class="icon-chevron-right"></i></span></td>

                                <td>
                                    <div class="btn-group" id="nodenet_list">
                                        <a class="btn" href="#">
                                            (no nodenet selected)
                                        </a>
                                    </div>
                                </td>
                                <td style="white-space:nowrap;">
                                    <div id="nodespace_control" class="collapse in">
                                        &nbsp;&nbsp;Nodespace:
                                        <input id="nodespace_name" class="input-large" disabled="disabled"
                                               value="Root"/>
                                        <a href="#" id="nodespace_up" class="btn"><i class="icon-share"></i></a>
                                    </div>

                                </td>
                            </tr>
                        </table>
                    </td>
                    <td>
                        <table class="pull-right">
                            <tr>
                                <td style="white-space:nowrap;">
                        <span class="btn-group">
                          <a href="#" class="btn"><i class="icon-fast-backward"></i></a>
                          <a href="#" class="btn"><i class="icon-play"></i></a>
                          <a href="#" id="nodenet_step_forward" class="btn"><i class="icon-step-forward"></i></a>
                          <a href="#" class="btn"><i class="icon-pause"></i></a>
                        </span>
                                </td>

                                <td align="right"><input id="nodenet_step" disabled="disabled"
                                                         style="text-align:right; width:60px;" value="0"/></td>

                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </form>
    </div>


    <div id="nodenet_editor" class="section-margin collapse in">
        <div class="section">
            <div class="editor_field span9">
                <canvas id="nodenet" width="700" height="500" style="background:#eeeeee"></canvas>
            </div>
            <div class="editor_field " id="nodenet_forms">

                <form class="form-horizontal hide" id="edit_nodenet_form">
                    <h4>Nodenet</h4>
                    <fieldset>
                        <div class="control-group">
                            <label class="control-label" for="nodenet_name">Name</label>
                            <div class="controls">
                                <input type="text" name="nodenet_name" id="nodenet_name">
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label" for="nodenet_worldadapter">Worldadapter</label>
                            <div class="controls">
                                <select name="nodenet_worldadapter" id="nodenet_worldadapter"></select>
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label">Nodetypes</label>
                            <div class="controls">
                                <table id="nodenet_nodetypes" class="table-striped table-condensed"></table>
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label">Datasources</label>
                            <div class="controls">
                                <table id="nodenet_datasources" class="table-striped table-condensed"></table>
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label">Datatargets</label>
                            <div class="controls">
                                <table id="nodenet_datatargets" class="table-striped table-condensed"></table>
                            </div>
                        </div>
                        <div class="controls">
                            <button type="submit" class="btn btn-primary">Save</button>
                        </div>
                    </fieldset>

                </form>

                <form class="form-horizontal hide" id="edit_link_form">
                    <h4>Link</h4>
                    <fieldset>
                        <div class="control-group">
                            <label class="control-label" for="link_weight_input">Weight</label>
                            <div class="controls">
                                <input type="text" class="" name="link_weight" id="link_weight_input">
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label" for="link_certainty_input">Certainty</label>
                            <div class="controls">
                                <input type="text" class="" name="link_certainty" id="link_certainty_input">
                            </div>
                        </div>
                    </fieldset>
                    <div class="controls">
                        <button type="submit" class="btn btn-primary">Save</button>
                    </div>
                </form>

                <form class="form-horizontal hide" id="edit_node_form">
                    <h4>Node</h4>
                    <fieldset>
                        <div class="control-group">
                            <label class="control-label" for="node_uid_input">UID</label>
                            <div class="controls">
                                <input type="text" disabled="disabled" id="node_uid_input" />
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label" for="node_name_input">Name</label>
                            <div class="controls">
                                <input type="text" name="node_name" id="node_name_input">
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label" for="node_type_input">Type</label>
                            <div class="controls">
                                <input type="text" name="node_type" disabled="disabled" id="node_type_input" />
                            </div>
                        </div>
                        <div class="control-group node state">
                            <label class="control-label" for="node_state_input">State</label>
                            <div class="controls">
                                <select type="text" name="node_state" id="node_state_input"></select>
                            </div>
                        </div>
                        <div class="control-group node">
                            <label class="control-label" for="node_activation_input">Activation</label>
                            <div class="controls">
                                <input type="text" name="node_activation" id="node_activation_input">
                            </div>
                        </div>
                        <div class="control-group node parameters">
                            <label class="control-label">Parameters</label>
                            <div class="controls">
                                <table id="node_parameters" class="table-striped table-condensed">
                                </table>
                            </div>
                        </div>
                    </fieldset>
                    <div class="controls">
                        <button type="submit" class="btn btn-primary">Save</button>
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
                        <button type="submit" class="btn btn-primary">Save</button>
                    </div>
                </form>

            </div>
        </div>
    </div>
    <div class="sectionbar">
        <form class="navbar-form">
            <table>
                <tr>
                    <td><span data-toggle="collapse" data-target="#monitor, #monitor_controls"><i
                            class="icon-chevron-right"></i></span></td>

                    <td> Nodenet Monitor &nbsp;</td>

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
                <canvas id="nodenet_monitor" width="700" height="500" style="background:#eeeeee"></canvas>
            </div>
            <div class="monitor_field " id="monitor_legend">
                <form>
                    <div>
                        <ul class="nav nav-list" id="monitor_list">
                            <li class="nav-header">Current monitors</li>
                            <li class="active"><a href="#">Monitor1</a></li>
                            <li><a href="#">Monitor2</a></li>
                            <li><a href="#">Monitor3</a></li>
                            <li><a href="#">Monitor4</a></li>
                        </ul>
                    </div>
                </form>
            </div>
        </div>
    </div>


    <div class="sectionbar">
        <form class="navbar-form">
            <table width="100%">
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td><span data-toggle="collapse" data-target="#world_editor"><i
                                        class="icon-chevron-right"></i></span></td>

                                 <td>
                                    <div class="btn-group" id="world_list">
                                        <a class="btn" href="#">
                                            (no world selected)
                                        </a>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                    <td>
                        <table class="pull-right">
                            <tr>
                                <td style="white-space:nowrap;">
                        <span class="btn-group">
                          <a href="#" class="btn"><i class="icon-fast-backward"></i></a>
                          <a href="#" class="btn"><i class="icon-play"></i></a>
                          <a href="#" class="btn"><i class="icon-step-forward"></i></a>
                          <a href="#" class="btn"><i class="icon-pause"></i></a>
                        </span>
                                </td>

                                <td align="right"><input id="world_step" disabled="disabled"
                                                         style="text-align:right; width:60px;" value="0"/></td>

                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </form>
    </div>

    <div id="world_editor" class="section-margin collapse in">
        <div class="section">
            <div class="editor_field span9">
                <canvas id="world" width="1445" height="900" style="background:#eeeeee"></canvas>
            </div>
            <div class="editor_field " id="world_forms">
                <form>
                    <div>
                        <ul class="nav nav-list" id="object_list">
                            <li class="nav-header">Active Context</li>
                            <li><a href="#">Object1</a></li>
                            <li><a href="#">Object2</a></li>
                            <li><a href="#">Object3</a></li>
                        </ul>
                    </div>
                </form>
            </div>
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
        <li><a href="#">Add monitor to slot</a></li>
    </ul>
</div>

<div class="dropdown" id="gate_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#gate_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
        <li><a href="#">Create link</a></li>
        <li><a href="#">Add monitor to gate</a></li>
    </ul>
</div>

<div class="dropdown" id="create_node_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#create_node_menu"></a>
    <ul class="nodenet_menu dropdown-menu">
        <li><a href="#">Create concept node</a></li>
        <li><a href="#">Create register</a></li>
        <li><a href="#">Create sensor</a></li>
        <li><a href="#">Create actor</a></li>
        <li><a href="#">Create event</a></li>
        <li><a href="#">Create node space</a></li>
        <li><a href="#">Create native module</a></li>
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
        <a href="#" class="btn btn-primary">Save changes</a>
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
        <a href="#" class="btn btn-primary">Save</a>
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
        <a href="#" class="btn btn-primary">Save</a>
    </div>
</div>

<div class="modal hide" id="edit_native_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3>Native module</h3>
    </div>
    <div class="modal-body">

    </div>
    <div class="modal-footer footer-next native-default">
        <a href="#" class="btn" data-dismiss="modal">Cancel</a>
        <a href="#" class="btn btn-primary native-next">Next</a>
    </div>
    <div class="modal-footer footer-save native-details hide">
        <a href="#" class="btn" data-dismiss="modal">Close</a>
        <a href="#" class="btn btn-primary native-save">Save</a>
    </div>
</div>



    <script src="/static/js/paper_nightly.js" type="text/javascript"></script>
    <script src="/static/js/nodenet.js" type="text/paperscript" canvas="nodenet"></script>
    <script src="/static/js/world.js" type="text/paperscript" canvas="world"></script>


%rebase boilerplate title = "MicroPsi Simulator"
