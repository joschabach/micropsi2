%include menu.tpl version = version

<div class="row-fluid">
    <p>
    <h1>Create {{'a new user' if not defined("first_user") else 'the administrator'}} for the MicroPsi server</h1>
    <div class="lead">Without logging in, you may not create and edit agents.</div>
    </p>


    <div class="row-fluid">
        <form class="form-horizontal well span8" action="signup_submit" method="POST">
            %if defined('cookie_warning') and cookie_warning:
            <div class="alert alert-info">
                <b>Important:</b> Make sure that cookies are enabled in your browser.
            </div>
            %end

            <fieldset>

                %if not defined("userid_error"):
                <div class="control-group">
                    <label class="control-label" for="userid">New user name</label>
                    <div class="controls">
                        <input type="text" class="input-xlarge" maxlength="21" id="userid" name="userid"
                        %if defined('userid'):
                        value="{{userid}}"
                        %else:
                        placeholder="UserID"
                        %end
                        />
                        <p class="help-block">The user id may only contain alphanumerical characters.</p>
                    </div>
                </div>
                %else:
                <div class="control-group error">
                    <label class="control-label" for="userid">New user name</label>
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
                    <label class="control-label" for="password">Choose a password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="password" name="password"
                        %if defined('password'):
                        value="{{password}}"
                        %end
                        />
                    </div>
                </div>
                %else:
                <div class="control-group error">
                    <label class="control-label" for="password">Choose a password</label>
                    <div class="controls">
                        <input type="password" class="input-xlarge" maxlength="256" id="password" name="password"
                        %if defined('password'):
                        value="{{password}}"
                        %end
                        />
                        <span class="help-inline">{{password_error}}</span>
                    </div>
                </div>
                %end

                %if defined('first_user') and first_user:
                <div class="control-group">
                    <label class="control-label" for="permissions">Permissions</label>
                    <div class="controls">
                        <select class="select-xlarge" id="permissions" name="permissions">
                            <option>Administrator</option>
                        </select>
                        <p class="help-block">The administrator has all permissions on the system.</p>
                    </div>
                </div>
                %else:
                %if defined('permissions'):
                <div class="control-group">
                    <label class="control-label" for="permissions">Permissions</label>
                    <div class="controls">
                        <select class="select-xlarge" id="permissions" name="permissions">
                            %if "create admin" in permissions:
                            <option value="Administrator">Administrator</option>
                            %end
                            %if "create full" in permissions:
                            <option value="Full">Create environments and agents</option>
                            %end
                            %if "create restricted" in permissions:
                            <option value="Restricted">Create agents</option>
                            %end
                        </select>
                        <p class="help-block">Set the access rights for this user.</p>
                    </div>
                </div>
                %end
                %end

                <div class="control-group">
                    <label class="checkbox">
                        <input name="keep_logged_in" type="checkbox" checked="checked"> Keep me logged in
                    </label>
                </div>
            </fieldset>
            <button type="submit" class="btn btn-primary">Create new user, and log in</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>


%rebase boilerplate title = "Sign up to use MicroPsi"
