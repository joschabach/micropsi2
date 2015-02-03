<div>
    <script src="/static/js/d3.v2.min.js" type="text/javascript"></script>
    <script src="/static/js/monitor.js" type="text/javascript"></script>
    <div class="sectionbar">
        <form class="navbar-form">
            <table>
                <tr>
                    <td><span data-toggle="collapse" data-target="#monitor, #monitor_controls"><i
                            class="icon-chevron-right"></i></span></td>

                    <td data-toggle="collapse" data-target="#monitor, #monitor_controls"> Nodenet Monitor &nbsp;</td>

                    <td><div class="" id="monitor_controls collapse in">
                        <button class="add_custom_monitor btn">Add custom Monitor</button>
                        <button class="btn">Clear</button>
                    </div></td>

                </tr>
            </table>
        </form>
    </div>

    <div id="monitor" class="section-margin frontend_section collapse in">
        <div class="section multiple">
            <div class="monitor_field span6">
                <h4>Monitors</h4>
                <div class="contentbox section">
                    <div id="graph"></div>
                    <div class="monitor_seperator">
                        <ul id="monitor_selector" class="monitor_list">
                        </ul>
                    </div>
                </div>
            </div>
            <div class="logger_field span6">
                <h4>Logs</h4>
                <div class="contentbox section">
                    <div id="logs"></div>
                    <form class="form-horizontal monitor_seperator">
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
                                <label for="log_nodenet" class="nodenet_log">
                                    <input type="checkbox" id="log_nodenet" class="log_switch" data="nodenet" />
                                    Nodenet
                                </label>
                                <select id="level_log_nodenet" class="log_level_switch" data="nodenet">
                                    <option value="DEBUG" {{'selected="selected"' if logging_levels['nodenet'] == "DEBUG" else ""}}>Debug</option>
                                    <option value="INFO" {{'selected="selected"' if logging_levels['nodenet'] == "INFO" else ""}}>Info</option>
                                    <option value="WARNING" {{'selected="selected"' if logging_levels['nodenet'] == "WARNING" else ""}}>Warning</option>
                                    <option value="ERROR" {{'selected="selected"' if logging_levels['nodenet'] == "ERROR" else ""}}>Error</option>
                                </select>
                            </li>
                        </ul>
                    </form>
                </div>
            </div>
            <p style="clear:both">&nbsp;</p>
        </div>
    </div>
</div>