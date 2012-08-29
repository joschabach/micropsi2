
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

                <form class="form-horizontal" id="edit_nodenet_form">
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
                            <label class="control-label" for="node_name_input">Name</label>
                            <div class="controls">
                                <input type="text" name="node_name" id="node_name_input">
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label" for="node_type_input">Type</label>
                            <div class="controls">
                                <input type="text" disabled="disabled" id="node_type_input" />
                            </div>
                        </div>
                        <div class="control-group">
                            <label class="control-label" for="node_activation_input">Activation</label>
                            <div class="controls">
                                <input type="text" disabled="disabled" id="node_activation_input">
                            </div>
                        </div>
                        <div class="control-group parameters">
                            <label class="control-label">Parameters</label>
                            <div class="controls">
                                <table id="node_parameters" class="table-striped table-condensed"></table>
                            </div>
                        </div>
                    </fieldset>
                    <div class="controls">
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
                                    <input id="current_world_name" disabled="disabled" value="Context"/>
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

    <div id="world_editor" class="section-margin collapse">
        <div class="section">
            <div class="editor_field span9">
                <canvas id="world" width="700" height="500" style="background:#eeeeee"></canvas>
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



    <script src="/static/js/paper_nightly.js" type="text/javascript"></script>
    <script src="/static/js/nodenet.js" type="text/paperscript" canvas="nodenet"></script>

%rebase boilerplate title = "MicroPsi Simulator"
