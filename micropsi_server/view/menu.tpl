<div class="navbar navbar-fixed-top">
    <div class="navbar-inner">
        <div class="container-fluid">
            <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </a>
            <a class="brand" href="/">MicroPsi 2
                %if defined('version'):
                v{{version}}
                %end
            </a>
            %if defined('user'):
                <div class="btn-group pull-right">
                    %if user != "Guest":
                    <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
                        <i class="icon-user"></i> {{user}}
                        <span class="caret"></span>
                    </a>
                    <ul class="dropdown-menu">
                        <li><a href="change_password">Change Password</a></li>
                        <li class="divider"></li>
                        <li><a href="logout">Sign Out</a></li>
                    </ul>
                    %else:
                    <a class="btn" href="login">
                        <i class="icon-user"></i> Log in
                    </a>
                    %end
                </div>
            %end
            <div class="nav-collapse">
                <ul class="nav">
                    %if defined('permissions'):
                    %if "manage agents" in permissions:
                    <li class="dropdown" id="menu_agent">
                        <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_agent">Blueprint
                            <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="blueprint_new">New...</a></li>
                            <li><a href="blueprint_edit">Edit...</a></li>
                            <li class="divider"></li>
                            <li><a href="#" class="agent_delete">Delete</a></li>
                            <li><a href="#" class="agent_save">Save</a></li>
                            <li><a href="#" class="agent_revert">Revert</a></li>
                            <li class="divider"></li>
                            <li><a href="#">Export to file...</a></li>
                            <li><a href="#">Import from file...</a></li>
                            <li><a href="#">Merge with file...</a></li>
                        </ul>
                    </li>
                    %end
                    %if "manage worlds" in permissions:
                    <li class="dropdown" id="menu_world">
                        <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_world">Context
                            <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="#">New...</a></li>
                            <li><a href="#">Edit...</a></li>
                            <li class="divider"></li>
                            <li><a href="#" class="world_delete">Delete</a></li>
                            <li><a href="#" class="world_save">Save</a></li>
                            <li><a href="#" class="world_revert">Revert</a></li>
                            <li class="divider"></li>
                            <li><a href="#">Export to file...</a></li>
                            <li><a href="#">Import from file...</a></li>
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
                            <li><a href="#">Server</a></li>
                            <li><a href="#">Blueprint runner</a></li>
                            <li><a href="#">Context runner</a></li>
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
            </div>
            <!--/.nav-collapse -->
        </div>
    </div>
</div>
