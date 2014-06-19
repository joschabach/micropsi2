

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
                                    %include nodenet_list type="world",mine=mine,others=others,current=current
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
                                  <a href="#" id="world_reset" class="btn"><i class="icon-fast-backward"></i></a>
                                  <a href="#" id="world_start" class="btn"><i class="icon-play"></i></a>
                                  <a href="#" id="world_step_forward" class="btn"><i class="icon-step-forward"></i></a>
                                  <a href="#" id="world_stop" class="btn"><i class="icon-pause"></i></a>
                                </div>
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
    <div class="world section">
        %if world_assets.get('template'):
            %include(world_assets['template'], assets=world_assets)
        %else:
            <div class="editor_field">
                <canvas id="world" width="100%" height="500" style="background:#eeeeee; width:100%"></canvas>
            </div>
        %end
    </div>
    <div class="seperator" style="text-align:center;"><a class="resizeHandle" id="worldSizeHandle"> </a></div>
</div>

<div class="dropdown" id="create_object_menu">
    <a class="dropdown-toggle" data-toggle="dropdown" href="#create_object_menu"></a>
    <ul class="world_menu dropdown-menu">
        <li><a href="#" data="add_worldobject">Add worldobject</a></li>
    </ul>
</div>


<script src="/static/js/world.js" type="text/paperscript" canvas="world"></script>

%if world_assets.get('js'):
    <script src="/static/{{world_assets['js']}}" type="text/paperscript" canvas="world"></script>
%end
