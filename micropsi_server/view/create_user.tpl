%include menu.tpl version = version, permissions = permissions, user = user

<div class="row-fluid">
    <p>
    <h1>Create a user for the MicroPsi server</h1>
    </p>


    <div class="row-fluid">
        <form class="form-horizontal well span8" action="create_user_submit" method="POST">

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
                    <label class="control-label" for="password">Set a password</label>
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
            </fieldset>
            <button type="submit" class="btn btn-primary">Create new user</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>


%rebase boilerplate title = "Create new user"
