

$(function(){

    var container = $('#vrep_world');

    var view = $('#vrep_world_view');

    var initialized = false;

    function get_world_data(){
        return {step: currentWorldSimulationStep};
    }

    $('.section.world .editor_field').height('auto');

    function set_world_data(data){
        var agent_html = '';
        for(var uid in data.agents){
            agent_html += '<p><strong>' + data.agents[uid].name + ' ('+data.agents[uid].type+')</strong>';
            if(uid in data.plots){
                agent_html += '<br \><img src="data:image/png;base64,'+data.plots[uid]+'" />';
            }
            agent_html += '</p>'

        }
        view.html(agent_html);
    }

    function get_world_state(){
        api.call('get_world_view', {'world_uid': currentWorld, 'step': 0}, set_world_data);
    }

    register_stepping_function('world', get_world_data, set_world_data);

    get_world_state();

});
