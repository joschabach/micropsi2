
                        <select class="input-xlarge" id="nn_worldadapter" name="nn_worldadapter">
% if not world_uid in worlds:
                            <option value="None">None</option>
% else:
   % worldadapters = worldtypes[worlds[world_uid].world_type]['class'].get_supported_worldadapters()
   % for type in sorted(worldadapters.keys()):
       % if defined("nodenet_uid") and nodenet_uid in nodenets and nodenets[nodenet_uid].worldadapter == type:
                            <option data-devices_supported="{{worldadapters[type].supports_devices()}}" value="{{type}}" selected="selected">{{type}}</option>
       % else:
                            <option data-devices_supported="{{worldadapters[type].supports_devices()}}" value="{{type}}">{{type}}</option>
       %end
   %end

%end
                        </select>
                        <div class="hint small docstring" id="nn_worldadapter_hint">Select a worldadapter to see a description</div>

%if world_uid in worlds:
<script type="text/javascript">
$(function(){
    var adapters = {};
    %for name, data in worldtypes[worlds[world_uid].world_type]['class'].get_supported_worldadapters().items():
        adapters["{{name}}"] = "{{(data.__doc__ or '').replace('\n', ' ')}}";
    %end
    var el = $('#nn_worldadapter');
    var updateDescription = function(){
        var val = el.val();
        $('#nn_worldadapter_hint').text(adapters[val]);
    }
    var updateOptions = function(){
        var val = $('#nn_worldadapter').val();
        $('.worldadapter-config').hide();
        $('.worldadapter-'+val).show();
    }
    el.on('change', updateOptions)
    el.on('change', updateDescription);
    updateDescription();
    updateOptions();
});
</script>
%end


