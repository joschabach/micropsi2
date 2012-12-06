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
% for uid in mine:
    % if uid != current:
      % if type=="world":
        <li><a href="?select_world={{uid}}" class="{{type}}_select">{{mine[uid].name}}</a></li>
      % else:
        <li><a href="/rpc/select_{{type}}" data="{{uid}}" class="{{type}}_select">{{mine[uid].name}}</a></li>
      % end
    % end
% end

% for uid in others:
    % if uid != current:
      % if type=="world":
        <li><a href="?select_world={{uid}}" class="{{type}}_select">{{others[uid].name}} ({{others[uid].owner}})</a></li>
      % else:
        <li><a href="/rpc/select_{{type}}" data="{{uid}}" class="{{type}}_select">{{others[uid].name}} ({{others[uid].owner}})</a></li>
      % end
    % end
% end
</ul>
%end