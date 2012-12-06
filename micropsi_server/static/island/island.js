/*
 * viewer for the world.
 */

var canvas = $('#world');

var viewProperties = {
    frameWidth: 1445,
    zoomFactor: 1,
    objectWidth: 12,
    lineHeight: 15,
    objectLabelColor: new Color ("#94c2f5"),
    objectForegroundColor: new Color ("#000000"),
    fontSize: 10,
    symbolSize: 14,
    highlightColor: new Color ("#ffffff"),
    gateShadowColor: new Color("#888888"),
    shadowColor: new Color ("#000000"),
    shadowStrokeWidth: 0,
    shadowDisplacement: new Point(0.5,1.5),
    innerShadowDisplacement: new Point(0.2,0.7),
    padding: 3,
    label: {
        x: 10,
        y: -10
    }
};

objects = {};
symbols = {};

currentWorld = $.cookie('selected_world') || null;

objectLayer = new Layer();
objectLayer.name = 'ObjectLayer';

currentWorldSimulationStep = -1;

var world_data = null;

if (currentWorld){
    setCurrentWorld(currentWorld);
}
initializeControls();

worldRunning = false;

$('#world_objects').html(
    '<div><a href="#" id="add_object_link" class="add_link">add Object</a></div>' +
    '<div id="island_objects"><strong>Objects</strong><table class="table-striped table-condensed"></table></div>');

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

function refreshWorldView(){
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
            $('#world_status').val(data.status_message);
            for(var key in objects){
                if(!(key in data.objects)){
                    if(objects[key].representation){
                        objects[key].representation.remove();
                        delete objects[key];
                    }
                } else {
                    if(data.objects[key].pos && data.objects[key].pos.length == 2){
                        objects[key].x = data.objects[key].pos[0];
                        objects[key].y = data.objects[key].pos[1];
                        objects[key].representation.rotate(data.objects[key].orientation - objects[key].orientation);
                        objects[key].orientation = data.objects[key].orientation;
                        objects[key].representation.position = new Point(objects[key].x, objects[key].y);
                    } else {
                        console.log('obj has no pos: ' + key);
                    }
                }
                delete data.objects[key];
            }
            for(key in data.objects){
                if(data.objects[key].pos && data.objects[key].pos.length == 2){
                    addObject(new WorldObject(key, data.objects[key].pos[0], data.objects[key].pos[1], data.objects[key].orientation, data.objects[key].name, data.objects[key].type));
                } else {
                    console.log('obj has no pos ' + key);
                }
            }

            updateViewSize();
            if(worldRunning){
                refreshWorldView();
            }
        }, error=function(data){
            $.cookie('selected_world', '', {expires:-1, path:'/'});
            dialogs.notification(data.Error, 'error');
        }
    );
}

function setCurrentWorld(uid){
    currentWorld = uid;
    $.cookie('selected_world', currentWorld, {expires:7, path:'/'});
    loadWorldInfo();
    loadWorldObjects();
    refreshWorldView();
}

function loadWorldObjects(){

}

function loadWorldInfo(){
    api.call('get_world_properties', {
        world_uid: currentWorld
    }, success=function(data){
        world_data = data;
        worldRunning = data.is_active;
        currentWorldSimulationStep = data.step;
        console.log(data);
        if('assets' in data){
            if(data.assets.x && data.assets.y){
                view.viewSize = new Size(data.assets.x, data.assets.y);
            }
            canvas.css('background', 'url("/static/'+ data.assets.background + '") no-repeat top left');
        }
    }, error=function(data){
        $.cookie('selected_world', '', {expires:-1, path:'/'});
        dialogs.notification(data.Error, 'error');
    });
}

function updateViewSize() {
    view.draw(true);
}


function WorldObject(uid, x, y, orientation, name, type){
    this.uid = uid;
    this.x = x;
    this.y = y;
    this.orientation = orientation || 0;
    this.name = name || "";
    this.type = type || "";
}

function addObject(worldobject){
    if(! (worldobject.uid in objects)) {
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    }
    return worldobject;
}

function redrawObject(obj){
    if(objects[obj.uid].representation){
        objects[obj.uid].representation.remove();
    }
    renderObject(obj);
}

function renderObject(worldobject){
    if(!(worldobject.type in symbols)){
        var bounds = calculateObjectBounds(worldobject);
        var path = createTrain(worldobject, bounds);
        symbols[worldobject.type] = new Symbol(path);
        //objectLayer.addChild(symbols[worldobject.type]);
    }
    worldobject.representation = symbols[worldobject.type].place();
    worldobject.representation.position = new Point(worldobject.x, worldobject.y);
    objectLayer.addChild(worldobject.representation);
}

function calculateObjectBounds(worldobject){
    var size = viewProperties.objectWidth * viewProperties.zoomFactor;
    return {
        x: worldobject.x*viewProperties.zoomFactor - size/2,
        y: worldobject.y*viewProperties.zoomFactor - size/2,
        width: size,
        height: size
    };
}

function getLegend(worldobject){
    var legend = new Group();
    legend.name = 'objectLegend';
    var bounds = worldobject.representation.bounds;
    var height = (viewProperties.fontSize*viewProperties.zoomFactor + 2*viewProperties.padding);
    var point = new Point(
        bounds.x + (viewProperties.label.x * viewProperties.zoomFactor),
        Math.max(height, bounds.y + (viewProperties.label.y * viewProperties.zoomFactor)));
    var text = new PointText(point);
    text.justification = 'left';
    text.content = (worldobject.name ? worldobject.name : worldobject.uid);
    text.characterStyle = {
        fillColor: 'black',
        fontSize: viewProperties.fontSize*viewProperties.zoomFactor
    };
    if(point.x + text.bounds.width + 2*viewProperties.padding > view.viewSize.width){
        point = new Point(
            view.viewSize.width - (text.bounds.width + 3*viewProperties.padding),
            point.y);
        text.point = point;
    }
    var container = new Path.Rectangle(new Point(point.x - viewProperties.padding, point.y + viewProperties.padding), new Size(text.bounds.width + 2*viewProperties.padding, -height));
    container.fillColor = 'white';
    legend.addChild(container);
    legend.addChild(text);
    return legend;
}

// -------------------------- mouse/ key listener --------------------------------------------//

hoverUid = false;
label = false;

clickLabel = false;
clickHighlight = false;

function onMouseMove(event) {
    var p = event.point;
    // hovering
    if (hoverUid) { // unhover
        if(hoverUid in objects){
            objects[hoverUid].representation.scale((1/viewProperties.hoverScale));
        }
        hoverUid = null;
    }
    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    for (var uid in objects) {
        if(objects[uid].representation){
            var bounds = objects[uid].representation.bounds;
            if (bounds.contains(p)) {
                if (hoverUid != uid){
                    hoverUid = uid;
                    if (label){
                        label.remove();
                    }
                    if(clickHighlight){
                        removeClickHighlight();
                    }
                    objects[uid].representation.scale(viewProperties.hoverScale);
                    label = getLegend(objects[hoverUid]);
                    objectLayer.addChild(label);
                }
                return;
            }
        }
    }
    if (!hoverUid && label){
        label.remove();
        label = null;
    }
}

function highlightWorldobject(event){
    event.preventDefault();
    var link = $(event.target);
    var uid = link.attr('data');
    removeClickHighlight();
    var obj = objects[uid];
    obj.representation.scale(viewProperties.hoverScale);
    clickHighlight = uid;
    label = getLegend(obj);
    objectLayer.addChild(label);
    if(!objectInViewport(obj)){
        scrollToObject(obj);
    }
    view.draw(true);
}

function removeClickHighlight(){
    if(clickHighlight) {
        objects[clickHighlight].representation.scale(1/viewProperties.hoverScale);
        clickHighlight = null;
    }
    if(label){
        label.remove();
        label = null;
    }
}

function objectInViewport(obj) {
    var parent = canvas.parent();
    var bounds = obj.representation.bounds;
    return (
        bounds.y > parent.scrollTop() &&
        bounds.x > parent.scrollLeft() &&
        (bounds.y + bounds.height) < (parent.innerHeight() + parent.scrollTop() - 20) &&
        (bounds.x + bounds.width) < (parent.innerWidth() + parent.scrollLeft() - 20)
    );
}

function scrollToObject(obj){
    var parent = canvas.parent();
    var bounds = obj.representation.bounds;
    if(bounds.y <= parent.scrollTop()) parent.scrollTop(bounds.y - 20);
    else if(bounds.y + bounds.height >= (parent.innerHeight() + parent.scrollTop() - 20)) parent.scrollTop(bounds.y + 20);
    if(bounds.x <= parent.scrollLeft()) parent.scrollLeft(bounds.x - 20);
    else if (bounds.x + bounds.width >= (parent.innerWidth() + parent.scrollLeft() - 20)) parent.scrollLeft(bounds.x + 20);
}

// --------------------------- controls -------------------------------------------------------- //

function initializeControls(){
    $('#world_reset').on('click', resetWorld);
    $('#world_step_forward').on('click', stepWorld);
    $('#world_start').on('click', startWorldrunner);
    $('#world_stop').on('click', stopWorldrunner);

    $('#add_object_link').on('click', function(event){
        event.preventDefault();
        
    });
}

function resetWorld(event){
    event.preventDefault();
    worldRunning = false;
    api.call('revert_world', {world_uid: currentWorld}, function(){
        setCurrentWorld(currentWorld);
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
