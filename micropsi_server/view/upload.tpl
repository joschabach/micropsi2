%include menu.tpl version = version, permissions = permissions, user_id = user_id

<div class="row-fluid">
    <p>
    <h1>{{title}}</h1>
    </p>

    <div class="row-fluid">
        <form class="form-horizontal well" action="{{action}}" method="POST">
            %if defined('error') and error:
            <div class="alert alert-info">
                <b>Error:</b> {{error}}.
            </div>
            %end
            <legend>{{message}}</legend>
            <fieldset>

             <div class="control-group">
                <label class="control-label" for="file_upload">Choose file</label>
                <div class="controls">
                    <input type="file" class="input-xlarge" id="file_upload" name="file_upload" />
                    <span class="help-inline"></span>
                </div>
            </div>

            </fieldset>
            <button type="submit" class="btn btn-primary">Submit</button>
            <a class="btn" href="/">Cancel</a>
        </form>
    </div>
</div>


%rebase boilerplate title = title
