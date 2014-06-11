
var canvas = $('#world');

currentWorld = $.cookie('selected_world') || null;
currentWorldSimulationStep = 0;

worldRunning = false;
wasRunning = false;

refreshWorldView = function(){
    api.call('get_world_view',
        {world_uid: currentWorld, step: currentWorldSimulationStep},
        function(data){
            if(jQuery.isEmptyObject(data)){
                if(worldRunning){
                    setTimeout(refreshWorldView, 100);
                }
                return null;
            }
            currentWorldSimulationStep = data.current_step;
            $('#world_step').val(currentWorldSimulationStep);
            if(worldRunning){
                refreshWorldView();
            }
        }, error=function(data){
            $.cookie('selected_world', '', {expires:-1, path:'/'});
            dialogs.notification(data.Error, 'error');
        }
    );
}

$(window).focus(function() {
    worldRunning = wasRunning;
    if(wasRunning){
        if(refreshWorldView) refreshWorldView();
    }
})
.blur(function() {
    wasRunning = worldRunning;
    worldRunning = false;
});

initialize_world_controls();

function initialize_world_controls(){
    $('#world_reset').on('click', resetWorld);
    $('#world_step_forward').on('click', stepWorld);
    $('#world_start').on('click', startWorldrunner);
    $('#world_stop').on('click', stopWorldrunner);
}


function resetWorld(event){
    event.preventDefault();
    worldRunning = false;
    api.call('revert_world', {world_uid: currentWorld}, function(){
        window.location.reload();
    });
}

function stepWorld(event){
    event.preventDefault();
    if(worldRunning){
        stopWorldrunner(event);
    }
    api.call('step_world', {world_uid: currentWorld}, function(data){
        currentWorldSimulationStep = data.step;
        $('#world_step').val(currentWorldSimulationStep);
        if(refreshWorldView) refreshWorldView();
    });
}

function startWorldrunner(event){
    event.preventDefault();
    api.call('start_worldrunner', {world_uid: currentWorld}, function(){
        worldRunning = true;
        if(refreshWorldView) refreshWorldView();
    });
}

function stopWorldrunner(event){
    event.preventDefault();
    worldRunning = false;
    api.call('stop_worldrunner', {world_uid: currentWorld}, function(){
        $('#world_step').val(currentWorldSimulationStep);
    });
}