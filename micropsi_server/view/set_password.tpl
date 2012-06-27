%include menu.tpl version = version, permissions = permissions, user = user

<div class="row-fluid">
    <p>
    <h1>Change password</h1>
    </p>

    <div class="row-fluid">
        <form class="form-horizontal well span8" action="/set_password_submit" method="POST">

            <legend>Enter a new password  for user ‘{{user_id}}’</legend>
            <fieldset>
                <div class="control-group">
                    <label class="control-label" for="password">New password</label>
                    <div class="controls">
                        <input type="hidden" id="userid" name="userid" value="{{user_id}}" />
                        <input type="text" class="input-xlarge" maxlength="256" id="password" name="password"/>
                    </div>
                </div>

            </fieldset>
            <button type="submit" class="btn btn-primary">Set password</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>


%rebase boilerplate title = "Change the password"
