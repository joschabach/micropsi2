
%include menu.tpl version = version, user_id = user_id, permissions = permissions

<script src="/static/js/paper-full.js" type="text/javascript"></script>

<div class="row-fluid">
%if mode == "nodenet":
    %include nodenet
% end
%if mode == "monitors":
	%include monitors logging_levels=logging_levels
%end
%if mode == "world":
    %include world  mine=mine,others=others,current=current,world_assets=world_assets
% end

%if mode == "all":
    %include nodenet
    %include monitors  logging_levels=logging_levels
    %include world  mine=mine,others=others,current=current,world_assets=world_assets
% end
</div>

%rebase boilerplate title = "MicroPsi Simulator"
