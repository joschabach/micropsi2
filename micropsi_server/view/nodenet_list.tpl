% if len(mine) + len(others) > 0:
<a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
% else:
<a class="btn" href="#">
% end

% if current in mine:
   {{mine[current].name}}
% elif current in others:
   {{others[current].name}} ({{others[current].owner}})
% else:
   (no {{type}} selected)
% end

% if len(mine) + len(others) == 0:
</a>
% else:
    <span class="caret"></span>
</a>
<ul class="dropdown-menu">
% for item in sorted(mine.items(), key=lambda foo: foo[1].name.lower()):
    % if item[0] != current:
      % if type=="environment":
        <li><a href="?select_world={{item[0]}}" class="world_select">{{item[1].name}}</a></li>
      % else:
        <li><a href="/rpc/select_nodenet" data="{{item[0]}}" class="nodenet_select">{{item[1].name}}</a></li>
      % end
    % end
% end

% for item in sorted(others.items(), key=lambda foo: foo[1].name.lower()):
    % if item[0] != current:
      % if type=="environment":
        <li><a href="?select_world={{item[0]}}" class="world_select">{{item[1].name}} ({{item[1].owner}})</a></li>
      % else:
        <li><a href="/rpc/select_nodenet" data="{{item[0]}}" class="nodenet_select">{{item[1].name}} ({{item[1].owner}})</a></li>
      % end
    % end
% end
</ul>
%end