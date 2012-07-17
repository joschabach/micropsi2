% if len(my_agents) + len(other_agents) > 1:
<a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
% else:
<a class="btn" href="#">
% end
% if current_agent in my_agents:
   {{my_agents[current_agent]["name"]}}
% elif current_agent in other_agents:
   {{other_agents[current_agent]["name"]}}
% else:
   (no agent selected)
% end
% if len(my_agents) + len(other_agents) == 1:
</a>
% else:
    <span class="caret"></span>
</a>
<ul class="dropdown-menu">
% for uid in my_agents:
    % if uid != current_agent:
<li><a href="/rpc/select_agent(agent_uid='{{uid}}')">{{my_agents[uid]["name"]}}</a></li>
    % end
% end

% for uid in other_agents:
    % if uid != current_agent:
<li><a href="/rpc/select_agent(agent_uid='{{uid}}')">{{other_agents[uid]["name"]}} ({{other_agents[uid]["owner"]}})</a></li>
    % end
% end
</ul>
%end

