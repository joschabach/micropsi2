
<div class="dialogform modal">

    <form class="form-horizontal" action="{{action}}" enctype="multipart/form-data" method="POST">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">×</button>
      <h3>{{title}}</h3>
    </div>

    <div class="modal-body">

            %if defined('error') and error:
            <div class="alert alert-info">
                <b>Error:</b> {{error}}.
            </div>
            %end
            <legend>{{message}}</legend>
            <fieldset class="well">

                 <div class="control-group">
                    <label class="control-label" for="file_upload">Choose file</label>
                    <div class="controls">
                        <input type="file" class="input-xlarge" id="file_upload" name="file_upload" />
                        <span class="help-inline"></span>
                    </div>
                </div>

            </fieldset>
    </div>

    <div class="modal-footer">
        <button type="submit" class="btn btn-primary">Submit</button>
        <a class="btn" data-dismiss="modal">Cancel</a>
    </div>

    </form>

</div>
