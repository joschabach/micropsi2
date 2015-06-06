
%include menu.tpl version = version, user_id = user_id, permissions = permissions

<script src="/static/js/paper-full.js" type="text/javascript"></script>

<div class="row-fluid">
    <div id="loading" class="modal">
        <p>
            <img src="static/img/loading_bubbles.gif"/><br/>
            Loading
        </p>
    </div>
%if mode == "nodenet":
    %include nodenet
% end
%if mode == "monitors":
	%include monitors logging_levels=logging_levels
%end
%if mode == "world":
    %include world  mine=mine,others=others,current=current,world_assets=world_assets
% end
%if mode == "face":
    %include face
% end

%if mode == "all":
    %include nodenet
    %include monitors  logging_levels=logging_levels
    %include world  mine=mine,others=others,current=current,world_assets=world_assets
% end

%if defined('first_user') and first_user:
<script type="text/javascript">
    $(function(){
        dialogs.remote_form_dialog($('a.login').attr('href'), function(){window.location.reload();});
    });
</script>
%end
</div>

%rebase boilerplate title = "MicroPsi Simulator"
