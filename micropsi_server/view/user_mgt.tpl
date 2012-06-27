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
                <th>Permissions</th>
                <th></th>
            </tr>
            </thead>
            <tbody>
            %for user_id in userlist:
            <tr>
                <td>{{user_id}}</td>
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

                </td>
            </tr>
            %end
            </tbody>
        </table>
    </div>
    <div class="row-fluid">
        <p>
        <a class="btn" href="/create_user"><i class="icon-plus"></i> Create a new user</a>
        </p>
    </div>
    <div class="row-fluid">
        <a class="btn" href="/">Back</a>
    </div>
</div>

%rebase boilerplate title = "Manage Users"
