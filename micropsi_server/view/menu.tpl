<div class="navbar navbar-fixed-top navbar-inverse">
    <div class="navbar-inner">
        <div class="container-fluid">
            <a class="brand" href="/">MicroPsi Runtime
                %if defined('version'):
                v{{version}}
                %end
            </a>
            <ul class="nav">
                %if defined('permissions'):
                %if "manage nodenets" in permissions:
                <li class="dropdown" id="menu_nodenet">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_nodenet">Agent
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/agent/edit" class="nodenet_new">New...</a></li>
                        <li class="divider"></li>
                        <li data="nodenet-needed"><a href="/agent/edit?id=" class="nodenet_edit">Edit</a></li>
                        <li data="nodenet-needed"><a href="#" class="nodenet_delete">Delete</a></li>
                        <li data="nodenet-needed"><a href="#" class="nodenet_save">Save</a></li>
                        <li data="nodenet-needed"><a href="#" class="nodenet_revert">Revert</a></li>
                        <li class="divider"></li>
                        <li data="nodenet-needed"><a href="#" class="run_recipe">Run a recipe</a></li>
                        <li class="divider"></li>
                        <li><a href="#" class="reload_code">Reload Code</a></li>
                        <li data="nodenet-needed"><a href="#" class="reload_code reload_revert">Reload &amp; Revert</a></li>
                        <li class="divider"></li>
                        <li data="nodenet-needed"><a href="/agent/export" class="nodenet_export">Export to file...</a></li>
                        <li><a href="/agent/import" class="nodenet_import">Import file...</a></li>
                        <li data="nodenet-needed"><a href="/agent/merge" class="nodenet_merge">Merge file...</a></li>
                        %if "manage nodenets" in permissions:
                        <li class="divider"></li>
                        <li><a href="/agent_mgt">Show agent console...</a></li>
                        %end
                    </ul>
                </li>
                %end
                %if "manage worlds" in permissions:
                <li class="dropdown" id="menu_world">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_world">Environment
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/environment/edit" class="world_manage">Manage worlds</a></li>
                        <li class="divider"></li>
                        <li><a href="/device/edit" class="device_manage">Manage devices</a></li>
                        <li class="divider"></li>
                        <li data="world-needed"><a href="#" class="world_delete">Delete</a></li>
                        <li data="world-needed"><a href="#" class="world_save">Save</a></li>
                        <li data="world-needed"><a href="#" class="world_revert">Revert</a></li>
                        <li class="divider"></li>
                        <li data="world-needed"><a href="/environment/export" class="world_export">Export to file...</a></li>
                        <li><a href="/environment/import" class="world_import">Import from file...</a></li>
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
                <li class="dropdown" id="menu_config">
                    <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_view">View
                        <b class="caret"></b></a>
                    <ul class="dropdown-menu">
                        <li><a href="/">Default</a></li>
                        <li><a href="/agent">Agent</a></li>
                        <li><a href="/monitors">Monitors</a></li>
                        <li><a href="/environment">Environment</a></li>
                        <li><a href="/dashboard">Dashboard</a></li>
                    </ul>
                </li>
                <li class="dropdown" id="menu_help">
                    <a href="/about">About</a>
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
                <div id="calculation_controls" class="dropdown btn-group pull-right">
                    <span class="btn running_indicator disabled">
                        <span class="running_icon runner_paused"><img src="/static/img/resting.gif" /></span>
                        <span class="running_icon runner_running" style="display:none"><img src="/static/img/working.gif" /></span>
                        <span class="running_text running_conditional" style="display:none">
                            <span>Condition:</span>
                            <span class="runner_condition">Monitor</span>
                        </span>
                    </span>
                    <span class="btn step_counters  disabled">
                        Environment:<span class="world_step">0</span><br/>
                        Agent:<span class="nodenet_step">0</span>
                    </span>
                  <a href="#" id="revert_all" class="btn"  title="revert all" data-nodenet-control><i class="icon-fast-backward"></i></a>
                  <a href="#" id="nodenet_step_forward" class="btn separated" title="step calculation" data-nodenet-control><i class="icon-step-forward"></i></a>
                  <a href="#" id="nodenet_start" class="btn" title="run calculation" data-nodenet-control><i class="icon-play"></i></a>
                  <a href="#" class="btn btn-expand" title="calculation settings" data-toggle="dropdown" data-nodenet-control>
                  ▼</a>
                    <ul id="run_nodenet_choices" class="run_nodenet_choices dropdown-menu">
                        <li><a href="#run" id="remove_runner_condition" data-run="indef">Remove condition</a></li>
                        <li><a href="#condition" id="set_runner_condition" data-run="condition">Set a condition for the runner</a></li>
                    </ul>

                  <a href="#" id="nodenet_stop" title="stop calculation" class="btn" data-nodenet-control><i class="icon-pause"></i></a>
                </div>

        </div>
    </div>
</div>
