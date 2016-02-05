
                        <select class="input-xlarge" id="nn_worldadapter" name="nn_worldadapter">
% if not world_uid in worlds:
                            <option value="None">None</option>
% else:
   % for type in sorted(worlds[world_uid].supported_worldadapters.keys()):
       % if defined("nodenet_uid") and nodenet_uid in nodenets and nodenets[nodenet_uid].worldadapter == type:
                            <option value="{{type}}" selected="selected">{{type}}</option>
       % else:
                            <option value="{{type}}">{{type}}</option>
       %end
   %end

%end
                        </select>
                        <div class="hint small docstring" id="nn_worldadapter_hint">Select a worldadapter to see a description</div>

%if world_uid in worlds:
<script type="text/javascript">
$(function(){
    var adapters = {};
    %for name in worlds[world_uid].supported_worldadapters:
    adapters["{{name}}"] = "{{worlds[world_uid].supported_worldadapters[name].__doc__ or ''}}";
    %end
    var el = $('#nn_worldadapter');
    var updateDescription = function(){
        var val = el.val();
        $('#nn_worldadapter_hint').text(adapters[val]);
    }
    el.on('change', updateDescription);
    updateDescription();
});
</script>
%end


