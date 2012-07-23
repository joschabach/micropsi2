
<div class="dialogform modal">

    <form class="form-horizontal" action="/change_password_submit" method="POST">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>{{title}}</h3>
    </div>

    <div class="modal-body">

            %if defined('cookie_warning') and cookie_warning:
            <div class="alert alert-info">
                <b>Important:</b> Make sure that cookies are enabled in your browser.
            </div>
            %end
            <legend>Enter a new password  for user ‘{{user_id}}’</legend>
            <fieldset class="well">
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
                        <input type="password" class="input-xlarge focused" maxlength="256" id="old_password" name="old_password"
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
    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Change password</button>
        <a class="btn" data-dismiss="modal">Cancel</a>
    </div>

    </form>

</div>
