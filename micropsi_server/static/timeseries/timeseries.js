
$(function(){

    var container = $('#timeseries_controls');

    var slider = $('#timeseries_slider');

    var initialized = false;

    var first, last, total;

    var advance_nodenet = $('#timeseries_controls_nodenet');
    var nodenet_amount = $('#timeseries_controls_nodenet_amount')

    function get_world_data(){
        return {step: currentWorldSimulationStep};
    }

    $('.section.world .editor_field').height('auto');

    function set_world_data(data){
        if(!initialized){
            first = new Date(data['first_timestamp']);
            last = new Date(data['last_timestamp']);
            total = data['total_timestamps'];
            slider.slider({
                'min': 0,
                'max': total - 1,
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
            $('.firstval', container).html(first.toLocaleString('de').replace(', ', '<br />'));
            $('.lastval', container).html(last.toLocaleString('de').replace(', ', '<br />'));
            initialized = true;
            slider.on('slideStop', set_world_state);
        }
        slider.slider('setValue', data['current_step']);
        $('.world_step').text(data.current_step);
    }

    function set_world_state(event){
        var value = parseInt(slider.val());
        api.call('set_world_data', {world_uid: currentWorld, data: {step: value}}, function(){
            if(advance_nodenet.attr('checked')){
                var nn_uid = (currentNodenet) ? currentNodenet : null;
                api.call('step_nodenets_in_world', {world_uid: currentWorld, nodenet_uid: nn_uid, steps: parseInt(nodenet_amount.val())}, function(){
                    if(nn_uid){
                        $(document).trigger('runner_stepped');
                    } else {
                        console.log('qwer');
                    }
                });
            } else {
                get_world_state();
            }
        });
    }

    function get_world_state(){
        api.call('get_world_view', {'world_uid': currentWorld, 'step': 0}, set_world_data);
    }

    register_stepping_function('world', get_world_data, set_world_data);

    get_world_state();

});