
var canvas = $('#world');

currentWorld = $.cookie('selected_world') || null;
currentWorldSimulationStep = 0;

worldRunning = false;
wasRunning = false;

initialize_world_controls();

registerResizeHandler();

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

function updateViewSize() {
    view.draw(true);
}

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

function registerResizeHandler(){
    // resize handler for nodenet viewer:
    var isDragging = false;
    var container = $('.section.world .editor_field');
    if($.cookie('world_editor_height')){
        container.height($.cookie('world_editor_height'));
        try{
            updateViewSize();
        } catch(err){}
    }
    var startHeight, startPos, newHeight;
    $("a#worldSizeHandle").mousedown(function(event) {
        startHeight = container.height();
        startPos = event.pageY;
        $(window).mousemove(function(event) {
            isDragging = true;
            newHeight = startHeight + (event.pageY - startPos);
            container.height(newHeight);
            updateViewSize();
        });
    });
    $(window).mouseup(function(event) {
        if(isDragging){
            $.cookie('world_editor_height', container.height(), {expires:7, path:'/'});
        }
        isDragging = false;
        $(window).unbind("mousemove");
    });
}
