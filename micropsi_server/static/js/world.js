
var canvas = $('#world');

currentWorld = $.cookie('selected_world') || null;
currentWorldSimulationStep = 0;

worldRunning = false;
wasRunning = false;

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

function get_world_data(){
    return {step: currentWorldSimulationStep};
}

function set_world_data(data){
    data = data.world
    if(!jQuery.isEmptyObject(data)){
        currentWorldSimulationStep = data.current_step;
        $('#world_step').val(currentWorldSimulationStep);
    }
}

register_stepping_function('world', get_world_data, set_world_data);

refreshWorldView = function(){
    api.call('get_world_view', {
        world_uid: currentWorld,
        step: currentWorldSimulationStep},
        success=set_world_data,
        error=function(data, outcome, type){
            $.cookie('selected_world', '', {expires:-1, path:'/'});
            worldRunning = false;
            api.defaultErrorCallback(data, outcome, type)
        }
    );
}

function updateViewSize() {
    view.draw(true);
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
