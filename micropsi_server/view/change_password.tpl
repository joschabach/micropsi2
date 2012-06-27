%include menu.tpl version = version

<div class="row-fluid">
    <p>
    <h1>Change password</h1>
    </p>

    <div class="row-fluid">
        <form class="form-horizontal well span8" action="change_password_submit" method="POST">
            %if defined('cookie_warning') and cookie_warning:
            <div class="alert alert-info">
                <b>Important:</b> Make sure that cookies are enabled in your browser.
            </div>
            %end
            <legend>Enter a new password  for user ‘{{userid}}’</legend>
            <fieldset>
                %if not defined("old_password_error"):
                <div class="control-group">
                    <label class="control-label" for="old_password">Old password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="old_password" name="old_password"
                        %if defined('old_password'):
                        value="{{old_password}}"
                        %end
                        />
                    </div>
                </div>
                %else:
                <div class="control-group error">
                    <label class="control-label" for="old_password">Old password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="old_password" name="old_password"
                        %if defined('old_password'):
                        value="{{old_password}}"
                        %end
                        />
                        <span class="help-inline">{{old_password_error}}</span>
                    </div>
                </div>
                %end

                %if not defined("new_password_error"):
                <div class="control-group">
                    <label class="control-label" for="new_password">New password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="new_password" name="new_password"
                        %if defined('new_password'):
                        value="{{new_password}}"
                        %end
                        />
                    </div>
                </div>
                %else:
                <div class="control-group error">
                    <label class="control-label" for="new_password">New password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="new_password" name="new_password"
                        %if defined('new_password'):
                        value="{{new_password}}"
                        %end
                        />
                        <span class="help-inline">{{new_password_error}}</span>
                    </div>
                </div>
                %end
            </fieldset>
            <button type="submit" class="btn btn-primary">Change password</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>


%rebase boilerplate title = "Change the password"
