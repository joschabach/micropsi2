

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
                      <a href="#" id="world_reset" class="btn"><i class="icon-fast-backward"></i></a>
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
            <form class="form-horizontal">
                <h4>World Status</h4>
                <textarea disabled="disabled" id="world_status" rows="4" cols="60" class="input-xlarge"></textarea>
            </form>
            <form class="form-horizontal">
                <h4>World Objects</h4>
                <table class="table-striped table-condensed" id="world_objects">
                </table>
            </form>
        </div>
    </div>
</div>

<script src="/static/js/world.js" type="text/paperscript" canvas="world"></script>


