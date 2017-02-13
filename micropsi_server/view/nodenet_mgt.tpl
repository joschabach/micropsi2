%include("menu.tpl", version=version, permissions=permissions, user_id=user_id)

<div class="row-fluid">
    <p>
    <h2>Agent Console</h2>
    </p>

    %if notification:
    <div class="alert alert-{{notification['status']}}">
        <button type="button" class="close" data-dismiss="alert">×</button>
        {{notification['msg']}}
    </div>
    %end

    <div class="row-fluid">
        <table class="table table-bordered table-striped" id="nodenet_mgr">
            <thead>
            <tr>
                <th>Agent UID</th>
                <th>Agent name</th>
                <th>Owner</th>
                <th>Actions</th>
            </tr>
            </thead>
            <tbody>
            %for nodenet_uid in nodenet_list:
            <tr>
                <td>{{nodenet_uid}}</td>
                <td>{{nodenet_list[nodenet_uid]["name"]}}
                </td>
                <td>{{nodenet_list[nodenet_uid]["owner"]}}
                </td>
                <td>
                    <a href="/select_nodenet_from_console/{{nodenet_uid}}" class="btn">View</a>
                    <a href="/delete_nodenet_from_console/{{nodenet_uid}}" class="btn">Delete</a>
                </td>
            </tr>
            %end
            </tbody>
        </table>
    </div>
</div>
<div class="row-fluid">
    <a class="btn" href="/">Back</a>
    <a class="btn save_all_nodenets btn-primary" href="/save_all_nodenets">Save all agents</a>
</div>

%rebase("boilerplate.tpl", title="Manage Agents")
