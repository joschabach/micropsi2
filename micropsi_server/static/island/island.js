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
    hoverScale: 1.5,
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

// accordion for trains and stations, commented for performance reasons
// $('#island_objects').html(
//     '<div class="accordion" id="worldobject_accordion">
//         <div class="accordion-group">
//             <div class="accordion-header"><a class="accordion-toggle" data-toggle="collapse" data-parent="#worldobject_accordion" href="#berlinStations"><i class="icon-chevron-right"></i>Stations</a></div>
//             <div id="berlinStations" class="accordion-body collapse">
//                 <table class="table-striped table-condensed"></table>
//             </div>
//         </div>
//         <div class="accordion-group">
//             <div class="accordion-header"><a class="accordion-toggle" data-toggle="collapse" data-parent="#worldobject_accordion" href="#berlinTrains"><i class="icon-chevron-right"></i>Trains</a></div>
//             <div id="berlinTrains" class="accordion-body collapse">
//                 <table class="table-striped table-condensed"></table>
//             </div>
//         </div>
//     </div>');

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
                        objects[key].representation.position = new Point(objects[key].x, objects[key].y);
                    } else {
                        console.log('obj has no pos: ' + key);
                    }
                }
                delete data.objects[key];
            }
            for(key in data.objects){
                if(data.objects[key].pos && data.objects[key].pos.length == 2){
                    addObject(new WorldObject(key, data.objects[key].pos[0], data.objects[key].pos[1], data.objects[key].traintype + ' ' + data.objects[key].line, data.objects[key].traintype));
                } else {
                    console.log('obj has no pos ' + key);
                }
            }
            // fill accordion with list of trains. see above.
            // var list_trains_html = '';
            // for(key in objects){
            //     list_trains_html += '<tr><td><a href="#" class="highlight_train">' + objects[key].name + '</a></td></tr>';
            // }
            // $('#berlinTrains table').html(list_trains_html);
            // $('.hightlight_train').on('click', highlightWorldobject);

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

function loadWorldInfo(){
    api.call('get_world_properties', {
        world_uid: currentWorld
    }, success=function(data){
        world_data = data;
        worldRunning = data.is_active;
        currentWorldSimulationStep = data.step;
        if('representation_2d' in data){
            view.viewSize = new Size(data['representation_2d']['x'], data['representation_2d']['y']);
            canvas.css('background', 'url("/static/img/'+ data['representation_2d']['image'] + '") no-repeat top left');
        }
    }, error=function(data){
        $.cookie('selected_world', '', {expires:-1, path:'/'});
        dialogs.notification(data.Error, 'error');
    });
}

function loadWorldObjects(){
    api.call('get_world_objects', {world_uid: currentWorld, type: 'stations'}, success=function(data){
        objectLayer.removeChildren();
        stations = {};
        var list_stations_html = '';
        for (var key in data){
            addStation(new WorldObject(key, data[key].pos[0], data[key].pos[1], data[key].name, data[key].stationtype));
            list_stations_html += '<tr><td><a href="#" data="' + key + '"class="highlight_station">' + data[key].name + '</a></td></tr>';
        }
        $('#island_objects table').html(list_stations_html);
        $('.highlight_station').on('click', highlightWorldobject);
        updateViewSize();
    }, error=function(data){
        $.cookie('selected_world', '', {expires:-1, path:'/'});
        dialogs.notification(data.Error, 'error');
    });
}

function updateViewSize() {
    view.draw(true);
}


function WorldObject(uid, x, y, name, type){
    this.uid = uid;
    this.x = x;
    this.y = y;
    this.name = name;
    this.type = type;
}

function addObject(worldobject){
    if(! (worldobject.uid in objects)) {
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    }
    return worldobject;
}

function addStation(station){
    if(!(station.uid in stations)){
        renderStation(station);
        stations[station.uid] = station;
    }
    return station;
}

function redrawObject(obj){
    if(objects[obj.uid].representation){
        objects[obj.uid].representation.remove();
    }
    renderObject(obj);
}

function renderStation(station){
    if(!('station_'+station.type in symbols)){
        var bounds = calculateStationBounds(station);
        var path = new Path.Rectangle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
        path.style = {
            fillColor: '#999999'
        };
        symbols['station_'+station.type] = new Symbol(path);
        //objectLayer.addChild(symbols[worldobject.type]);
    }
    station.representation = symbols['station_'+station.type].place();
    station.representation.position = new Point(station.x, station.y);
    objectLayer.addChild(station.representation);
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

function calculateStationBounds(station){
    var size;
    switch(station.type){
        case "Bus":
        case "Tram": size = 5; break;
        case "S":
        case "S+U":
        case "U": size = 10;
    }
    return {
        x: station.x*viewProperties.zoomFactor - size/2,
        y: station.y*viewProperties.zoomFactor - size/2,
        width: size,
        height: size
    };
}

function calculateObjectBounds(worldobject){
    var size = viewProperties.objectWidth * viewProperties.zoomFactor;
    if (worldobject.type == "Tram"){
        size = 8;
    } else if (['S', 'U', 'RE', 'RB', 'ICE'].indexOf(worldobject.type) < 0){
        size = 5;
    }
    return {
        x: worldobject.x*viewProperties.zoomFactor - size/2,
        y: worldobject.y*viewProperties.zoomFactor - size/2,
        width: size,
        height: size
    };
}

function createTrain(worldobject, bounds){
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
stationmarker = false;


clickLabel = false;
clickHighlight = false;

function onMouseMove(event) {
    var p = event.point;
    // hovering
    if (hoverUid) { // unhover
        if(hoverUid in objects){
            objects[hoverUid].representation.scale((1/viewProperties.hoverScale));
        }
        if(hoverUid in stations && stationmarker){
            stationmarker.remove();
            stationmarker = null;
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
    if(!hoverUid && stationmarker){
        stationmarker.remove();
        stationmarker = null;
    }
}

function highlightWorldobject(event){
    event.preventDefault();
    var link = $(event.target);
    var uid = link.attr('data');
    removeClickHighlight();
    var obj;
    if(link.hasClass('highlight_station')){
        obj = stations[uid];
        stationmarker = new Path.Rectangle(obj.representation.bounds);
        stationmarker.fillColor='black';
        label = getLegend(obj);
        objectLayer.addChild(label);
        objectLayer.addChild(stationmarker);
    } else {
        obj = objects[uid];
        obj.representation.scale(viewProperties.hoverScale);
        clickHighlight = uid;
        label = getLegend(obj);
        objectLayer.addChild(label);
    }
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
    if(stationmarker){
        stationmarker.remove();
        stationmarker = null;
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
