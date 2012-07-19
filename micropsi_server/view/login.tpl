%include menu.tpl version = version

<div class="row-fluid">
    <p>
    <h1>Log in to the MicroPsi server</h1>
    <div class="lead">Without logging in, you may not create and edit nodenets.</div>
    </p>


    <div class="row-fluid">
        <form class="form-horizontal well span8" action="login_submit" method="POST">
            %if defined('cookie_warning') and cookie_warning:
            <div class="alert alert-info">
                <b>Important:</b> Make sure that cookies are enabled in your browser.
            </div>
            %end

            <fieldset>
                %if defined('login_error'):
                <div class="alert alert-error">{{login_error}}</div>
                %else:
                <legend>Already got a login? Please enter user name and password.</legend>
                %end

                %if not defined("userid_error"):
                <div class="control-group">
                    <label class="control-label" for="userid">User name</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge" maxlength="21" id="userid" name="userid"
                        %if defined('userid'):
                        value="{{userid}}"
                        %else:
                        placeholder="UserID"
                        %end
                        />
                    </div>
                </div>
                %else:
                <div class="control-group error">
                    <label class="control-label" for="userid">User name</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge" maxlength="21" id="userid" name="userid"
                        %if defined('userid'):
                        value="{{userid}}"
                        %else:
                        placeholder="UserID"
                        %end
                        />
                        <span class="help-inline">{{userid_error}}</span>
                    </div>
                </div>
                %end

                %if not defined("password_error"):
                <div class="control-group">
                    <label class="control-label" for="password">Password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="password" name="password">
                    </div>
                </div>
                %else:
                <div class="control-group error">
                    <label class="control-label" for="password">Password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="password" name="password">
                        <span class="help-inline">{{password_error}}</span>
                    </div>
                </div>
                %end

                <div class="control-group">
                    <label class="checkbox">
                        <input name="keep_logged_in" type="checkbox" checked="checked"> Keep me logged in
                    </label>
                </div>
            </fieldset>
            <button type="submit" class="btn btn-primary">Log in</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
    <div class="row-fluid">
        %if defined('permissions') and ("create restricted" in permissions or "create full" in permissions):
        <h3>If you do not have a login:</h3>
        <a class="btn btn-large" href="signup">
            Create a new user
        </a>
        %end
    </div>
</div>


%rebase boilerplate title = "Log in to use MicroPsi"
