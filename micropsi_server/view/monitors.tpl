<div>
    <script src="/static/js/d3.v2.min.js" type="text/javascript"></script>
    <script src="/static/js/monitor.js" type="text/javascript"></script>
    <div class="sectionbar">
        <form class="navbar-form">
            <div class="pull-right">
                <button data="vertical" class="layoutbtn btn">◫</button>
                <button data="horizontal" class="layoutbtn btn" style="-webkit-transform: rotate(-90deg);
                        -moz-transform: rotate(-90deg);
                        -ms-transform: rotate(-90deg);
                        -o-transform: rotate(-90deg);">◫</button>
            </div>
            <table>
                <tr>
                    <td><span data-toggle="collapse" data-target="#monitor, #monitor_controls"><i
                            class="icon-chevron-right"></i></span></td>

                    <td data-toggle="collapse" data-target="#monitor, #monitor_controls"> Agent Monitor &nbsp;</td>
                    <td>
                        <div class="btn-group nodenet_list">
                            <a class="btn" href="#">
                                (no agent selected)
                            </a>
                        </div>
                    </td>

                    <td><div class="" id="monitor_controls collapse in">
                    </div></td>

                </tr>
            </table>
        </form>
    </div>

    <div id="monitor" class="section-margin frontend_section collapse in">
        <div class="section multiple">
            <div class="monitor_field layout_field">
                <h4>Monitors</h4>
                <div class="contentbox section">
                    <div id="graph"></div>
                    <div class="monitor_seperator">
                        <form class="form-horizontal monitor_list">
                            <label for="monitor_x_axis">
                                No. of steps:
                            </label>
                            <select id="monitor_x_axis" class="input-mini">
                                <option>100</option>
                                <option>200</option>
                                <option>500</option>
                                <option>1000</option>
                                <option value="-1">all</option>
                            </select>
                        </form>
                        <p class="monitor_list">
                            <button class="add_custom_monitor btn btn-small">Add custom Monitor</button>
                        </p>
                        <ul id="monitor_selector" class="monitor_list">
                        </ul>
                    </div>
                </div>
            </div>
            <div class="logger_field layout_field">
                <h4>Logs</h4>
                <div class="contentbox section">
                    <div id="logs"></div>
                    <div class="section">
                        <form class="form-horizontal span4 monitor_seperator">
                            <ul id="log_selector" class="monitor_list">
                                <li>
                                    <label for="log_system" class="system_log">
                                        <input type="checkbox" id="log_system" class="log_switch" data="system" />
                                        System
                                    </label>
                                    <select id="level_log_system" class="log_level_switch" data="system">
                                        <option value="DEBUG" {{'selected="selected"' if logging_levels['system'] == "DEBUG" else ""}}>Debug</option>
                                        <option value="INFO" {{'selected="selected"' if logging_levels['system'] == "INFO" else ""}}>Info</option>
                                        <option value="WARNING" {{'selected="selected"' if logging_levels['system'] == "WARNING" else ""}}>Warning</option>
                                        <option value="ERROR" {{'selected="selected"' if logging_levels['system'] == "ERROR" else ""}}>Error</option>
                                    </select>
                                </li>
                                <li>
                                    <label for="log_world" class="world_log">
                                        <input type="checkbox" id="log_world" class="log_switch" data="world" />
                                        World
                                    </label>
                                    <select id="level_log_world" class="log_level_switch" data="world">
                                        <option value="DEBUG" {{'selected="selected"' if logging_levels['world'] == "DEBUG" else ""}}>Debug</option>
                                        <option value="INFO" {{'selected="selected"' if logging_levels['world'] == "INFO" else ""}}>Info</option>
                                        <option value="WARNING" {{'selected="selected"' if logging_levels['world'] == "WARNING" else ""}}>Warning</option>
                                        <option value="ERROR" {{'selected="selected"' if logging_levels['world'] == "ERROR" else ""}}>Error</option>
                                    </select>
                                </li>
                                <li>
                                    <label for="log_agent" class="agent_log">
                                        <input type="checkbox" id="log_agent" class="log_switch" data="agent" />
                                        Agent
                                    </label>
                                    <select id="level_log_agent" class="log_level_switch" data="agent">
                                        <option value="DEBUG" {{'selected="selected"' if logging_levels['agent'] == "DEBUG" else ""}}>Debug</option>
                                        <option value="INFO" {{'selected="selected"' if logging_levels['agent'] == "INFO" else ""}}>Info</option>
                                        <option value="WARNING" {{'selected="selected"' if logging_levels['agent'] == "WARNING" else ""}}>Warning</option>
                                        <option value="ERROR" {{'selected="selected"' if logging_levels['agent'] == "ERROR" else ""}}>Error</option>
                                    </select>
                                </li>
                            </ul>
                        </form>
                        <form class="form-horizontal span4 monitor_list">
                            <p><label for="monitor_filter_logs">Filter:</label>
                            <input type="text" value="" id="monitor_filter_logs" class="input-small"/></p>
                            <p><button id="clear_logs" class="btn btn-small">clear logs</button></p>
                        </form>
                        <p style="clear:both">&nbsp;</p>
                    </div>
                </div>
            </div>
            % if theano_available:
                <div class="recorder_field layout_field">
                    <h4>Recorders</h4>
                    <form id="export_recorders" method="post">
                        <div class="contentbox section">
                            <table id="recorder_table" class="table-striped table-condensed">
                            </table>
                        </div>
                        <div class="section">
                            <p class="monitor_list">
                                <button data-action="add_recorder" class="add_recorder btn btn-small">Add recorder</button>
                                <button data-action="export_selected_recorders" type="submit" class="export_recorders btn btn-small">Export selected recorders</button>
                            </p>
                        </div>
                    </form>
                </div>
            % end
            <p style="clear:both">&nbsp;</p>
        </div>
    </div>
</div>

<div class="modal hide" id="recorder_modal">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">×</button>
        <h3 class="title">Add Recorder</h3>
    </div>
    <div class="modal-body">
        <form class="form-horizontal">
            <fieldset>
            <div class="control-group">
                <label class="control-label" for="recorder_type_input">Type:</label>
                <div class="controls">
                    <select id="recorder_type_input">
                        <option value="gate_activation_recorder">Gate Activation recorder</option>
                        <option value="node_activation_recorder">Node Activation recorder</option>
                        <option value="linkweight_recorder">Linkweight recorder</option>
                    </select>
                </div>
            </div>
            </fieldset>
            <fieldset class="node_activation_recorder gate_activation_recorder recorder_specific">
                <legend>Nodes</legend>
                <div class="control-group">
                    <label class="control-label" for="recorder_nodespace_uid">Nodespace</label>
                    <div class="controls">
                    <select class="recorder_nodespace_dropdown" id="recorder_nodespace_uid"></select>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="recorder_node_uids">Node uids</label>
                    <div class="controls">
                        <input type="text" id="recorder_node_uids"/>
                    </div>
                    <label class="control-label" for="recorder_node_name_prefix">or name prefix</label>
                    <div class="controls">
                        <input type="text" id="recorder_node_name_prefix"/>
                    </div>
                </div>
                <div class="control-group gate_activation_recorder recorder_specific">
                    <label class="control-label" for="recorder_gate">Gate</label>
                    <div class="controls">
                        <input type="text" id="recorder_gate" value="gen"/>
                    </div>
                </div>
            </fieldset>
            <fieldset class="linkweight_recorder recorder_specific">
                <legend>From nodes</legend>
                <div class="control-group">
                    <label class="control-label" for="recorder_from_nodespace_uid">Nodespace</label>
                    <div class="controls">
                    <select class="recorder_nodespace_dropdown" id="recorder_from_nodespace_uid"></select>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="recorder_from_node_uids">Node uids</label>
                    <div class="controls">
                        <input type="text" id="recorder_from_node_uids"/>
                    </div>
                    <label class="control-label" for="recorder_from_node_name_prefix">or name prefix</label>
                    <div class="controls">
                        <input type="text" id="recorder_from_node_name_prefix"/>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="recorder_from_gate">Gate</label>
                    <div class="controls">
                        <input type="text" id="recorder_from_gate" value="gen"/>
                    </div>
                </div>
            </fieldset>
            <fieldset class="linkweight_recorder recorder_specific">
                <legend>To nodes</legend>
                <div class="control-group">
                    <label class="control-label" for="recorder_to_nodespace_uid">Nodespace</label>
                    <div class="controls">
                    <select class="recorder_nodespace_dropdown" id="recorder_to_nodespace_uid"></select>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="recorder_to_node_uids">Node uids</label>
                    <div class="controls">
                        <input type="text" id="recorder_to_node_uids"/>
                    </div>
                    <label class="control-label" for="recorder_to_node_name_prefix">or name prefix</label>
                    <div class="controls">
                        <input type="text" id="recorder_to_node_name_prefix"/>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label" for="recorder_to_slot">Slot</label>
                    <div class="controls">
                        <input type="text" id="recorder_to_slot" value="gen"/>
                    </div>
                </div>
            </fieldset>
            <fieldset>
                <legend>Recorder</legend>
                <div class="control-group activation_recorder">
                    <label class="control-label" for="recorder_interval">Interval</label>
                    <div class="controls">
                        <input type="text" id="recorder_interval" value="1"/>
                    </div>
                </div>
                <div class="control-group activation_recorder">
                    <label class="control-label" for="recorder_name">Name</label>
                    <div class="controls">
                        <input type="text" id="recorder_name" value=""/>
                    </div>
                </div>
            </fieldset>
        </form>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal">Close</button>
        <button class="btn btn-primary">Add Recorder</button>
    </div>
</div>
