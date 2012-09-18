
                        <select class="input-xlarge" id="nodenet_worldadapter" name="nodenet_worldadapter">
% if not world_uid in worlds:
                            <option value="None">None</option>
% else:
   % for type in worlds[world_uid].supported_worldadapters:
       % if defined("nodenet_uid") and nodenet_uid in nodenets and nodenets[nodenet_uid].worldadapter == type:
                            <option value="{{type}}" selected="selected">{{type}}</option>
       % else:
                            <option value="{{type}}">{{type}}</option>
       %end
   %end
%end


