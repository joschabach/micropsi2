
%include menu.tpl version = version, user_id = user_id, permissions = permissions

<script src="/static/js/paper.js" type="text/javascript"></script>

<div class="row-fluid">
%if mode == "nodenet":
    %include nodenet
% end
%if mode == "world":
    %include world
% end
%if mode == "all":
    %include nodenet
    %include world
% end
</div>

%rebase boilerplate title = "MicroPsi Simulator"
