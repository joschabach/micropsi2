
<div class="dialogform modal">

    <form class="form-horizontal" action="/set_password_submit" method="POST">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>{{title}}</h3>
    </div>

    <div class="modal-body">

            <legend>Enter a new password  for user ‘{{userid}}’</legend>
            <fieldset class="well">
                <div class="control-group">
                    <label class="control-label" for="password">New password</label>
                    <div class="controls">
                        <input type="hidden" id="userid" name="userid" value="{{userid}}" />
                        <input type="text" class="input-xlarge" maxlength="256" id="password" name="password"/>
                    </div>
                </div>
            </fieldset>
    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Set password</button>
        <a class="btn" data-dismiss="modal">Cancel</a>
    </div>

    </form>
</div>
