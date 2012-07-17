    <li class="nav-header">Current World</li>
% if objects:
    % for uid in objects:
        % if uid == current_object:
    <li id="{{uid}}" class="active"><a href="/rpc/select_object(object_uid='{{uid}}')">{{objects[uid]["name"]}}</a></li>
        % else:
    <li id="{{uid}}"><a href="/rpc/select_object(object_uid='{{uid}}')">{{objects[uid]["name"]}}</a></li>
        % end
    % end
% else
    <li>(empty)</li>
%end


