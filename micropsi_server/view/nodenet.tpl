
%include menu.tpl version = version, user = user, permissions = permissions

<div class="container-fluid">
    <div class="row-fluid">
        <div class="span2">
            <div class="well sidebar-nav">
                <ul class="nav nav-list">
                    <li class="nav-header">My Blueprints</li>
                    <li class="active"><a href="#">Blueprint1</a></li>
                    <li><a href="#">Blueprint2</a></li>
                    <li><a href="#">Blueprint3</a></li>
                    <li><a href="#">Blueprint4</a></li>
                    <li class="nav-header">Other Blueprints</li>
                    <li><a href="#">Blueprint10</a></li>
                    <li><a href="#">Blueprint11</a></li>
                    <li class="nav-header">Active Context</li>
                    <li><a href="#">Object1</a></li>
                    <li><a href="#">Object2</a></li>
                    <li><a href="#">Object3</a></li>
                </ul>
            </div>
            <!--/.well -->
        </div>
        <!--/span-->
        <div class="span10">
            <div class="sectionbar">
                <form class="navbar-form">
                    <table>
                        <tr>
                            <td><span data-toggle="collapse" data-target="#nodenet_editor, #nodespace_control"><i
                                    class="icon-chevron-right"></i></span></td>


                            <td><input disabled="disabled" value="Blueprint1"/></td>

                            <td><span class="btn-group">
                                  <button class="btn"><i class="icon-fast-backward"></i></button>
                                  <button class="btn"><i class="icon-play"></i></button>
                                  <button class="btn"><i class="icon-step-forward"></i></button>
                                  <button class="btn"><i class="icon-pause"></i></button>
                             </span></td>

                            <td><input disabled="disabled" style="text-align:right" value="0"/></td>
                            <td><div id="nodespace_control" class="collapse in">
                                &nbsp;Nodespace:
                                <input id="nodespace_name" disabled="disabled" value="Root"/>
                                <button id="nodespace_up" class="btn"><i class="icon-share"></i></button>
                            </div>

                            </td>
                        </tr>
                    </table>
                </form>
            </div>


            <div id="nodenet_editor" class="collapse in">
                <div style="overflow:scroll; height:500px">
                    <canvas id="nodenet" width="700" height="500" style="background:#eeeeee"></canvas>
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


            <div id="monitor" class="collapse">
                <div class="hero-unit">
                    <p>Monitor plugin for individual activities</p>
                </div>
            </div>
            <div class="sectionbar">
                <form class="navbar-form">
                    <table>
                        <tr>
                            <td><span data-toggle="collapse" data-target="#world_editor"><i
                                    class="icon-chevron-right"></i></span></td>


                            <td><input disabled="disabled" value="Context"/></td>

                            <td><span class="btn-group">
                          <button class="btn"><i class="icon-fast-backward"></i></button>
                          <button class="btn"><i class="icon-play"></i></button>
                          <button class="btn"><i class="icon-step-forward"></i></button>
                          <button class="btn"><i class="icon-pause"></i></button>
                    </span></td>

                            <td><input disabled="disabled" style="text-align:right" value="0"/></td>
                        </tr>
                    </table>

                </form>
            </div>


            <div id="world_editor" class="collapse">
                <div class="hero-unit">
                    <p>Context Viewer Placeholder</p>
                </div>
            </div>


            <!--/span-->
        </div>
        <!--/row-->
    </div>
    <!--/span-->
</div>
<!--/row-->


</div><!--/.fluid-container-->

<div class="dropdown" id="node_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#node_menu"></a>
    <ul class="dropdown-menu">
    </ul>
</div>

<div class="dropdown" id="link_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#link_menu"></a>
    <ul class="dropdown-menu">
        <li><a href="#">Delete link</a></li>
    </ul>
</div>

<div class="dropdown" id="slot_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#slot_menu"></a>
    <ul class="dropdown-menu">
        <li><a href="#">Add monitor to slot</a></li>
    </ul>
</div>

<div class="dropdown" id="gate_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#gate_menu"></a>
    <ul class="dropdown-menu">
        <li><a href="#">Create link</a></li>
        <li><a href="#">Add monitor to gate</a></li>
    </ul>
</div>

<div class="dropdown" id="create_node_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#create_node_menu"></a>
    <ul class="dropdown-menu">
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
                        <input type="text" class="input-xlarge" id="rename_node_input">
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

    <script src="/static/js/micropsiviewer.js" type="text/javascript"></script>
    <script src="/static/js/paper_nightly.js" type="text/javascript"></script>
    <script src="/static/js/nodenet.js" type="text/paperscript" canvas="nodenet"></script>

%rebase boilerplate title = "MicroPsi Simulator"
