
var canvas = $('#world');

currentWorld = $.cookie('selected_world') || null;

worldRunning = false;
wasRunning = false;

$(window).focus(function() {
    worldRunning = wasRunning;
    if(wasRunning){
        refreshWorldView();
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
    api.call('step_world', {world_uid: currentWorld}, function(){
        refreshWorldView();
    });
}

function startWorldrunner(event){
    event.preventDefault();
    api.call('start_worldrunner', {world_uid: currentWorld}, function(){
        worldRunning = true;
        refreshWorldView();
    });
}

function stopWorldrunner(event){
    event.preventDefault();
    worldRunning = false;
    api.call('stop_worldrunner', {world_uid: currentWorld}, function(){
        $('#world_step').val(currentWorldSimulationStep);
    });
}