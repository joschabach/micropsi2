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
    hoverScale: 2,
    padding: 3,
    typeColors: {
        S: new Color('#006600'),
        U: new Color('#000099'),
        Tram: new Color('#990000'),
        Bus: new Color('#7000ff'),
        NE: new Color('#7000ff'),
        other: new Color('#304451'),
        RE: new Color('#ff0000'),
        RB: new Color('#ff0000')
    },
    label: {
        x: 10,
        y: -10
    }
};

objects = {};

currentWorld = $.cookie('selected_world') || null;

objectLayer = new Layer();
objectLayer.name = 'ObjectLayer';

objPrerenderLayer = new Layer();
objPrerenderLayer.name = 'PrerenderLayer';
objPrerenderLayer.visible = false;
currentWorldSimulationStep = -1;

var world_data = null;

refreshWorldList();
if (currentWorld){
    setCurrentWorld(currentWorld);
}
initializeControls();

worldRunning = false;

function refreshWorldList(){
    $("#world_list").load("/world_list/"+(currentWorld || ''), function(data){
        $('#world_list .world_select').on('click', function(event){
            event.preventDefault();
            var el = $(event.target);
            var uid = el.attr('data');
            setCurrentWorld(uid);
        });
    });
}

function refreshWorldView(){
    api.call('get_world_view',
        {world_uid: currentWorld, step: currentWorldSimulationStep},
        function(data){
            if(jQuery.isEmptyObject(data)){
                if(worldRunning){
                    setTimeout(refreshWorldView, 800);
                }
                return null;
            }
            currentWorldSimulationStep = data.currentSimulationStep;
            $('#world_step').val(currentWorldSimulationStep);
            //var tablerows = '';
            for(var key in objects){
                if(!(key in data.objects)){
                    if(objects[key].representation){
                        objects[key].representation.remove();
                        delete objects[key];
                    }
                } else {
                    if(data.objects[key].pos && data.objects[key].pos.length == 2){
                        obj = new WorldObject(key, data.objects[key].pos[0], data.objects[key].pos[1], data.objects[key].line, data.objects[key].traintype);
                        redrawObject(obj);
                        objects[key] = obj;
                    }
                }
                delete data.objects[key];
            }
            for(key in data.objects){
                if(data.objects[key].pos && data.objects[key].pos.length == 2){
                    addObject(new WorldObject(key, data.objects[key].pos[0], data.objects[key].pos[1], data.objects[key].line, data.objects[key].traintype));
                } else {
                    console.log('obj has no pos ' + key);
                }
            }
            //tablerows += '<tr><td><a class="link_object" data="'+obj.uid+'">'+obj.name+'</a></td></tr>';
            //$('#world_objects').html(tablerows);
            //$('.link_object').on('click', highlightWorldobject);

            updateViewSize();
            if(worldRunning){
                refreshWorldView();
            }
        }
    );
}

function hasObjectChanged(uid, data){
    return uid in objects && (objects[uid].x != data.pos[0] || objects[uid].y != data.pos[1] || objects[uid].name != data.name);
}

function setCurrentWorld(uid){
    currentWorld = uid;
    $.cookie('selected_world', currentWorld, {expires:7, path:'/'});
    refreshWorldList();
    loadWorldInfo();
    // loadWorldObjects();
    refreshWorldView();
}

function loadWorldInfo(){
    api.call('get_world_properties', {
        world_uid: currentWorld
    }, function(data){
        world_data = data;
        currentWorldSimulationStep = data.step;
        if('representation_2d' in data){
            view.viewSize = new Size(data['representation_2d']['x'], data['representation_2d']['y']);
            canvas.css('background', 'url("/static/img/'+ data['representation_2d']['image'] + '") no-repeat top left');
        }
    });
}

function loadWorldObjects(){
    api.call('get_world_objects', {world_uid: currentWorld, type: 'trains'}, function(data){
        objectLayer.removeChildren();
        objects = {};
        var tablerows = '';
        var obj = null;
        for(var key in data){
            obj = new WorldObject(key, data[key].pos[0], data[key].pos[1], data[key].line, data[key].traintype);
            tablerows += '<tr><td><a class="link_object" data="'+obj.uid+'">'+obj.name+'</a></td></tr>';
            addObject(obj);
        }
        $('#world_objects').html(tablerows);
        $('.link_object').on('click', highlightWorldobject);
        updateViewSize();
    });
}

function updateViewSize() {
    view.draw(true);
}


function WorldObject(uid, x, y, name, type){
    this.uid = uid;
    this.x = x;
    this.y = y;
    this.name = type + ' ' + name;
    this.type = type;
    this.bounds = null;
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
    worldobject.bounds = calculateObjectBounds(worldobject);
    worldobject.representation = createStation(worldobject);
    //worldobject.representation.name = worldobject.uid;
    objectLayer.addChild(worldobject.representation);
}

function calculateObjectBounds(worldobject){
    var width, height;
    width = height = viewProperties.objectWidth * viewProperties.zoomFactor;
    if (worldobject.type == "Tram"){
        width = height = 8;
    } else if (['S', 'U', 'RE', 'RB'].indexOf(worldobject.type) < 0){
        width = height = 5;
    }
    return new Rectangle(worldobject.x*viewProperties.zoomFactor - width/2,
        worldobject.y*viewProperties.zoomFactor - height/2, // center worldobject on origin
        width, height);
}

function createStation(worldobject, idx){
    var bounds = worldobject.bounds;
    var shape = new Path.Circle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
    if (worldobject.type in viewProperties.typeColors){
        shape.fillColor = viewProperties.typeColors[worldobject.type];
    } else {
        shape.fillColor = viewProperties.typeColors['other'];
    }
    return shape;
}

function getLegend(worldobject){
    var legend = new Group();
    legend.name = 'stationLegend';
    var bounds = worldobject.bounds;
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
hoverPath = false;
path = false;
label = false;

clickLabel = false;
clickHighlight = false;

function onMouseMove(event) {
    var p = event.point;
    // hovering
    if (hoverUid) { // unhover
        objects[hoverUid].representation.scale((1/viewProperties.hoverScale));
        hoverUid = null;
    }
    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    for (var uid in objects) {
        var bounds = objects[uid].bounds;
        if (bounds.contains(p) && objects[uid].representation) {
            if (hoverUid != uid){
                hoverUid = uid;
                if (label){
                    label.remove();
                    label = null;
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
    if (!hoverUid && label){
        label.remove();
        label = null;
    }
}

function highlightWorldobject(event){
    var uid = $(event.target).attr('data');
    if(clickHighlight != uid){
        removeClickHighlight();
        objects[uid].representation.scale(viewProperties.hoverScale);
        clickHighlight = uid;
        clickLabel = getLegend(objects[uid]);
        objectLayer.addChild(clickLabel);
        if(!objectInViewport(uid)){
            scrollToObject(uid);
        }
        view.draw(true);
    }
}

function removeClickHighlight(){
    if(clickHighlight) {
        objects[clickHighlight].representation.scale(1/viewProperties.hoverScale);
        clickHighlight = null;
    }
    if(clickLabel){
        clickLabel.remove();
        clickLabel = null;
    }
}

function objectInViewport(uid) {
    var parent = canvas.parent();
    return (
        objects[uid].bounds.y > parent.scrollTop() &&
        objects[uid].bounds.x > parent.scrollLeft() &&
        (objects[uid].bounds.y + objects[uid].bounds.height) < (parent.innerHeight() + parent.scrollTop() - 20) &&
        (objects[uid].bounds.x + objects[uid].bounds.width) < (parent.innerWidth() + parent.scrollLeft() - 20)
    );
}

function scrollToObject(uid){
    var parent = canvas.parent();
    var obj = objects[uid];
    if(obj.bounds.y <= parent.scrollTop()) parent.scrollTop(obj.bounds.y - 20);
    else if(obj.bounds.y + obj.bounds.height >= (parent.innerHeight() + parent.scrollTop() - 20)) parent.scrollTop(obj.bounds.y + 20);
    if(obj.bounds.x <= parent.scrollLeft()) parent.scrollLeft(obj.bounds.x - 20);
    else if (obj.bounds.x + obj.bounds.width >= (parent.innerWidth() + parent.scrollLeft() - 20)) parent.scrollLeft(obj.bounds.x + 20);
}

// --------------------------- controls -------------------------------------------------------- //

function initializeControls(){
    $('#world_reset').on('click', resetWorld);
    $('#world_step_forward').on('click', stepWorld);
    $('#world_start').on('click', startWorldrunner);
    $('#world_stop').on('click', stopWorldrunner);
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
    api.call('step_world', {world_uid: currentWorld}, function(){
        if(worldRunning){
            stopWorldrunner(event);
        }
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
