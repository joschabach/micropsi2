
$(function(){

    var container = $('#timeseries_controls');

    var slider = $('#timeseries_slider');

    var initialized = false;

    var first, last, total;

    function get_world_data(){
        return {step: currentWorldSimulationStep};
    }

    function set_world_data(data){
        if(!initialized){
            first = new Date(data['first_timestamp']);
            last = new Date(data['last_timestamp']);
            total = data['total_timestamps'];
            slider.slider({
                'min': 0,
                'max': data['total_timestamps'],
                'width': '100%',
                'step': 1,
                'value': data['current_step'],
                'tooltip': 'show',
                'handle': 'triangle',
                'selection': 'none',
                'formater': function(index){
                    if (index > 0){
                        var interval = parseInt((last.getTime() - first.getTime()) / total);
                        return new Date(first.getTime() + (interval * index)).toLocaleString('de');
                    } else {
                        return first.toLocaleString('de');
                    }
                }

            });
            $('.firstval', container).text(first.toLocaleString('de'));
            $('.lastval', container).text(last.toLocaleString('de'));
            initialized = true;
            slider.on('slideStop', set_world_state);
        }
        slider.slider('setValue', data['current_step']);
    }

    function set_world_state(event){
        console.log(event);
    }

    register_stepping_function('world', get_world_data, set_world_data);

    api.call('get_world_view', {'world_uid': currentWorld, 'step': 0}, set_world_data);
});