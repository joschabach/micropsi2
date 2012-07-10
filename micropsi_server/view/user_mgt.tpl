%include menu.tpl version = version, permissions = permissions, user = user

<div class="row-fluid">
    <p>
    <h2>User Console</h2>
    </p>

    <div class="row-fluid">
        <table class="table table-bordered table-striped">
            <thead>
            <tr>
                <th>UserID</th>
                <th>Active</th>
                <th>Permissions</th>
                <th>Actions</th>
            </tr>
            </thead>
            <tbody>
            %for user_id in userlist:
            %if user_id!=user:
            <tr>
                <td>{{user_id}}</td>
                <td>
                    %if userlist[user_id]["is_active"]:
                    <i class="icon-ok"></i>
                    %else:
                    &nbsp;
                    %end
                </td>
                <td>
                    <div class="btn-group">
                        <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
                            {{userlist[user_id]["role"]}}
                            <span class="caret"></span>
                        </a>
                        <ul class="dropdown-menu">
                            <li><a href="/set_permissions/{{user_id}}/Administrator">Administrator</a></li>
                            <li><a href="/set_permissions/{{user_id}}/Full">Full</a></li>
                            <li><a href="/set_permissions/{{user_id}}/Restricted">Restricted</a></li>
                        </ul>
                    </div>
                </td>
                <td>
                    <a href="/set_password/{{user_id}}" class="btn set_new_password">Set new password</a>
                    <a href="/delete_user/{{user_id}}" class="btn">Delete user</a>
                </td>
            </tr>
            %end
            %end
            </tbody>
        </table>
    </div>
    <div class="row-fluid">
        <p>
        <a class="btn create_user" href="/create_user"><i class="icon-plus"></i> Create a new user</a>
        </p>
    </div>
    <div class="row-fluid">
        <a class="btn" href="/">Back</a>
    </div>
</div>

%rebase boilerplate title = "Manage Users"
