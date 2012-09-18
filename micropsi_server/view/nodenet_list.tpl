% if len(my_nodenets) + len(other_nodenets) > 0:
<a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
% else:
<a class="btn" href="#">
% end

% if current_nodenet in my_nodenets:
   {{my_nodenets[current_nodenet].name}}
% elif current_nodenet in other_nodenets:
   {{other_nodenets[current_nodenet].name}} ({{other_nodenets[current_nodenet].owner}})
% else:
   (no nodenet selected)
% end

% if len(my_nodenets) + len(other_nodenets) == 0:
</a>
% else:
    <span class="caret"></span>
</a>
<ul class="dropdown-menu">
% for uid in my_nodenets:
    % if uid != current_nodenet:
<li><a href="/rpc/select_nodenet" data="{{uid}}" class="nodenet_select">{{my_nodenets[uid].name}}</a></li>
    % end
% end

% for uid in other_nodenets:
    % if uid != current_nodenet:
<li><a href="/rpc/select_nodenet" data="{{uid}}" class="nodenet_select">{{other_nodenets[uid].name}} ({{other_nodenets[uid].owner}})</a></li>
    % end
% end
</ul>
%end

