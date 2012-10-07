
%include menu.tpl version = version, user_id = user_id, permissions = permissions

<div class="row-fluid">

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
                          <a href="#" id="world_start" class="btn"><i class="icon-play"></i></a>
                          <a href="#" id="world_step_forward" class="btn"><i class="icon-step-forward"></i></a>
                          <a href="#" id="world_stop" class="btn"><i class="icon-pause"></i></a>
                        </span>
                                </td>

                                <td align="right"><input id="world_step" type="text" disabled="disabled"
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
    <script src="/static/js/world.js" type="text/paperscript" canvas="world"></script>


%rebase boilerplate title = "MicroPsi World"
