<div class="navbar navbar-fixed-top navbar-inverse">
    <div class="navbar-inner">
        <div class="container-fluid">
            <a class="brand" href="/">MicroPsi 2
                %if defined('version'):
                v{{version}}
                %end
            </a>
            <ul class="nav">
                %if defined('permissions'):
                %if "manage nodenets" in permissions:
                <li class="dropdown" id="menu_nodenet">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_nodenet">Nodenet
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/nodenet/edit" class="nodenet_new">New...</a></li>
                        <li class="divider"></li>
                        <li><a href="#" class="nodenet_delete">Delete</a></li>
                        <li><a href="#" class="nodenet_save">Save</a></li>
                        <li><a href="#" class="nodenet_revert">Revert</a></li>
                        <li class="divider"></li>
                        <li><a href="#" class="run_recipe">Run a recipe</a></li>
                        <li><a href="#" class="reload_native_modules">Reload Native Modules</a></li>
                        <li class="divider"></li>
                        <li><a href="/nodenet/export" class="nodenet_export">Export to file...</a></li>
                        <li><a href="/nodenet/import" class="nodenet_import">Import file...</a></li>
                        <li><a href="/nodenet/merge" class="nodenet_merge">Merge file...</a></li>
                        %if "manage nodenets" in permissions:
                        <li class="divider"></li>
                        <li><a href="/nodenet_mgt">Show nodenet console...</a></li>
                        %end
                    </ul>
                </li>
                %end
                %if "manage worlds" in permissions:
                <li class="dropdown" id="menu_world">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_world">Environment
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/world/edit" class="world_new">New...</a></li>
                        <li class="divider"></li>
                        <li><a href="#" class="world_delete">Delete</a></li>
                        <li><a href="#" class="world_save">Save</a></li>
                        <li><a href="#" class="world_revert">Revert</a></li>
                        <li class="divider"></li>
                        <li><a href="/world/export" class="world_export">Export to file...</a></li>
                        <li><a href="/world/import" class="world_import">Import from file...</a></li>
                    </ul>
                </li>
                %end
                %if "manage users" in permissions:
                <li class="dropdown" id="menu_users">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_users">Users
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/user_mgt">Show user console...</a></li>
                    </ul>
                </li>
                %end
                %if "manage server" in permissions:
                <li class="dropdown" id="menu_config">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_config">Config
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/config/runner" class="remote_form_dialog edit_runner_properties">Runner Properties</a></li>
                    </ul>
                </li>
                %end
                %end
                <li class="dropdown" id="menu_help">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_help">Help
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/about">About</a></li>
                        <li><a href="/docs">Documentation</a></li>
                        <li class="divider"></li>
                        <li><a href="/contact">Contact</a></li>
                    </ul>
                </li>
            </ul>
            %if defined('user_id'):
                <div class="btn-group pull-right">
                    %if user_id != "Guest":
                    <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
                        <i class="icon-user"></i> {{user_id}}
                        <span class="caret"></span>
                    </a>
                    <ul class="dropdown-menu">
                        <li><a href="change_password" class="set_new_password">Change Password</a></li>
                        <li class="divider"></li>
                        <li><a href="logout">Sign Out</a></li>
                    </ul>
                    %else:
                    <a class="btn login" href="/login">
                        <i class="icon-user"></i> Log in
                    </a>
                    %end
                </div>
            %end
                <div id="simulation_controls" class="dropdown btn-group pull-right">
                    <span class="btn running_indicator disabled">
                        <span class="running_icon runner_paused"><img src="/static/img/resting.gif" /></span>
                        <span class="running_icon runner_running" style="display:none"><img src="/static/img/working.gif" /></span>
                        <span class="running_text running_conditional" style="display:none">
                            <span>Condition:</span>
                            <span class="runner_condition">Monitor</span>
                        </span>
                    </span>
                    <span class="btn step_counters  disabled">
                        World:<span class="world_step">0</span><br/>
                        Net:<span class="nodenet_step">0</span>
                    </span>
                  <a href="#" id="nodenet_reset" class="btn"  title="revert nodenet" data-nodenet-control><i class="icon-fast-backward"></i></a>
                  <a href="#" id="nodenet_step_forward" class="btn separated" title="step simulation" data-nodenet-control><i class="icon-step-forward"></i></a>
                  <a href="#" id="nodenet_start" class="btn" title="run simulation" data-nodenet-control><i class="icon-play"></i></a>
                  <a href="#" class="btn btn-expand" title="simulation settings" data-toggle="dropdown" data-nodenet-control>
                  ▼</a>
                    <ul id="run_nodenet_choices" class="run_nodenet_choices dropdown-menu">
                        <li><a href="#run" id="remove_runner_condition" data-run="indef">Remove condition</a></li>
                        <li><a href="#condition" id="set_runner_condition" data-run="condition">Set a condition for the runner</a></li>
                    </ul>

                  <a href="#" id="nodenet_stop" title="stop simulation" class="btn" data-nodenet-control><i class="icon-pause"></i></a>
                </div>

        </div>
    </div>
</div>
