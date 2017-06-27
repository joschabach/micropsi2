
<div class="dialogform modal">

    <form class="form-horizontal" action="/login_submit" method="POST">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>{{title}}</h3>
    </div>

    <div class="modal-body">

            %if defined('cookie_warning') and cookie_warning:
            <div class="alert alert-info">
                <div class="lead">Without logging in, you may not create and edit agents.</div>
                <b>Important:</b> Make sure that cookies are enabled in your browser.
            </div>
            %end

            %if defined('login_error'):
            <div class="alert alert-error">{{login_error}}</div>
            %end

            <legend>Already got a login? Please enter user name and password.</legend>
            <fieldset class="well">

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

            %if defined('permissions') and ("create restricted" in permissions or "create full" in permissions):
            <legend>If you do not have a login:</legend>
            <fieldset>
                <a class="btn modal_followup" href="/signup">
                    Create a new user
                </a>
            </fieldset>
            %end

    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Log in</button>
        <a class="btn cancel" data-dismiss="modal">Cancel</a>
    </div>

    </form>

</div>
