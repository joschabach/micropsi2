
%include("menu.tpl", version=version, permissions=permissions, user_id=user_id)

<script src="/static/js/paper-full.js" type="text/javascript"></script>

<div class="row-fluid">
    <div id="loading" class="modal">
        <p>
            <img src="static/img/loading_bubbles.gif"/><br/>
            Loading
        </p>
    </div>
%if mode == "nodenet":
    %include("nodenet.tpl")
% end
%if mode == "monitors":
	%include("monitors.tpl", logging_levels=logging_levels)
%end
%if mode == "world":
    %include("world.tpl", mine=mine, others=others, current=current, world_assets=world_assets)
% end
%if mode == "dashboard":
    %include("dashboard.tpl", logging_levels=logging_levels)
% end

%if mode == "all":
    %include("nodenet.tpl")
    %include("monitors.tpl", logging_levels=logging_levels)
    %include("world.tpl", mine=mine, others=others, current=current, world_assets=world_assets)
% end

%if defined('first_user') and first_user:
<script type="text/javascript">
    $(function(){
        dialogs.remote_form_dialog($('a.login').attr('href'), function(){window.location.reload();});
    });
</script>
%end
</div>

%rebase("boilerplate.tpl", title="MicroPsi Simulator")
