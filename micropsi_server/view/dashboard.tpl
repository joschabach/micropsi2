

<div id="dashboard_viewer" class="section-margin frontend_section collapse in">
      <div class="sectionbar">
        <form class="navbar-form">
            <table>
                <tr>
                    <td><span data-toggle="collapse" data-target="#monitor, #monitor_controls"><i
                            class="icon-chevron-right"></i></span></td>

                    <td data-toggle="collapse" data-target="#monitor, #monitor_controls"> Agent Dashboard &nbsp;</td>
                    <td>
                        <div class="btn-group nodenet_list">
                            <a class="btn" href="#">
                                (no nodenet selected)
                            </a>
                        </div>
                    </td>
                </tr>
            </table>
        </form>
    </div>
    <div id="dashboard" class="section-margin frontend_section">
        <div id="dashboard_container">
            <div class="span5">
                <div id="dashboard_urges" class="dashboard-item"></div>
                <div id="dashboard_modulators" class="dashboard-item"></div>
            </div>
            <div class="span3">
                <div id="dashboard_valence" class="dashboard-item left"></div>
                <div id="dashboard_face" class="dashboard-item left"></div>
                <div id="dashboard_nodes" class="dashboard-item left"></div>
                <p style="clear:both"/>
            </div>
            <div class="span4">
                <div id="dashboard_datatable" class="dashboard-item"></div>
            </div>
        </div>
    </div>
</div>

<script src="/static/js/d3.v2.min.js" type="text/javascript"></script>
<script src="/static/js/dashboard.js" type="text/javascript"></script>
