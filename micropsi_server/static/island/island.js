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
    selectionColor: new Color("#99ccff"),
    innerShadowDisplacement: new Point(0.2,0.7),
    padding: 3,
    typeColors: {
        "other": new Color ("#94c2f5")
    },
    label: {
        x: 10,
        y: -10
    }
};

available_object_types = [];

var scale_factors = {
    'Lightsource': 1,
    'Braitenberg': 1,
    'Survivor': 1,
    'PalmTree': 0.5,
    'Maple': 0.7,
    'Braintree': 0.5,
    'Wirselkraut': 0.2,
    'Thornbush': 1,
    'Juniper': 0.4,
    'Champignon': 0.125,
    'FlyAgaric': 0.2,
    'Stone': 0.2,
    'Boulder': 0.6,
    'Menhir': 0.4,
    'Waterhole': 0.4
}

objects = {};
symbols = {};
agents = {};

objectLayer = new Layer();
objectLayer.name = 'ObjectLayer';

currentWorldSimulationStep = -1;

var world_data = null;

var worldscope = paper;

if(typeof currentWorld != 'undefined'){
    setCurrentWorld(currentWorld);
} else {
    currentWorld = $.cookie('selected_world') || null;
}

scenes = {};

addObjectMode = null;
addObjectGhost = null;

var agentsList = $('#world_agents_list table');

function get_world_data(){
    return {step: currentWorldSimulationStep};
}

function set_world_data(data){

    worldscope.activate();
    currentWorldSimulationStep = data.current_step;
    $('#world_step').val(currentWorldSimulationStep);
    $('#world_status').val(data.status_message);
    // treat agents and objects the same
    data.objects = jQuery.extend(data.objects, data.agents);
    for(var key in objects){
        if(!(key in data.objects)){
            if(objects[key].representation){
                objects[key].representation.remove();
                delete objects[key];
                if(key in scenes){
                    delete scenes[key];
                }
            }
        } else {
            if(data.objects[key].position && data.objects[key].position.length == 2){
                if(!(path && path.objectMoved && path.name == key)){
                    objects[key].x = data.objects[key].position[0];
                    objects[key].y = data.objects[key].position[1];
                    objects[key].representation.position = new Point(objects[key].x, objects[key].y);
                }
                if(data.objects[key].orientation){
                    objects[key].representation.rotate(data.objects[key].orientation - objects[key].orientation);
                }
                objects[key].orientation = data.objects[key].orientation;
                if(key in scenes){
                    scenes[key] = data.objects[key].scene;
                }
            } else {
                console.log('obj has no pos: ' + key);
            }
        }
        delete data.objects[key];
    }
    for(key in data.objects){
        if(data.objects[key].position && data.objects[key].position.length == 2){
            if(key in data.agents){
                addAgent(new WorldObject(key, data.objects[key].position[0], data.objects[key].position[1], data.objects[key].orientation, data.objects[key].name, data.objects[key].type));
                agents[key] = objects[key];
                if('scene' in data.agents[key]){
                    scenes[data.agents[key].uid] = data.agents[key].scene;
                }
            } else {
                addObject(new WorldObject(key, data.objects[key].position[0], data.objects[key].position[1], data.objects[key].orientation, data.objects[key].name, data.objects[key].type));
            }
        } else {
            console.log('obj has no pos ' + key);
        }
    }
    // purge agent list
    for(key in agents){
        if(!(key in data.agents)){
            $("#world_agents_list a[data='" + key + "']").parent().parent().remove();
        }
    }

    updateSceneViewer();
    updateViewSize();
}

register_stepping_function('world', get_world_data, set_world_data);

refreshWorldView = function(){
    api.call('get_world_view',
        {world_uid: currentWorld, step: currentWorldSimulationStep},
        success = set_world_data,
        error=function(data){
            $.cookie('selected_world', '', {expires:-1, path:'/'});
            dialogs.notification(data.Error, 'error');
        }
    )
};

function updateSceneViewer(){
    var selector = $('#scene_viewer_agent');
    var selected = selector.val();
    var selector_html = '';
    for(var key in scenes){
        selector_html += '<option value="'+key+'">'+objects[key].name+'</option>';
    }
    if(selector_html != ''){
        selector_html = '<option val="">choose...</option>' + selector_html;
        $('.scene_viewer_section').addClass('form-default').show();
    } else{
        $('.scene_viewer_section').removeClass('form-default').hide();
    }
    selector.html(selector_html);
    var keys = Object.keys(scenes);
    if(!selected && keys.length == 1){
        selected = keys[0];
        selector.val(selected);
    } else {
        selector.val(selected);
    }
    if(selected){
        refreshSceneView();
    }
}

function refreshSceneView(event){
    var selector = $('#scene_viewer_agent');
    var scene = scenes[selector.val()];
    var viewer = $('#scene_viewer');
    var html = '';
    var grid_factor = {};
    if(scene){
        grid_factor['y'] = scene.shape_grid.length - 1;
        grid_factor['x'] = scene.shape_grid[0].length - 1;
        for(var row in scene.shape_grid){
            for(var col in scene.shape_grid[row]){
                var classnames = [];
                if((scene.fovea_x + (grid_factor.x/2) == col) &&
                    Math.abs(scene.fovea_y - (grid_factor.y/2)) == row){
                    classnames.push('active');
                }
                if(scene.shape_grid[row][col]){
                    for(var prop in scene.shape_grid[row][col]){
                        classnames.push(scene.shape_grid[row][col][prop]);
                    }
                    html += '<b class="'+classnames.join(' ')+'"></b>';
                } else {
                    html += '<b class="'+classnames.join(' ')+'">&nbsp;</b>';
                }
            }
            html += '<br/>';
        }
    }
    viewer.html(html);
}

function setCurrentWorld(uid){
    currentWorld = uid;
    $.cookie('selected_world', currentWorld, {expires:7, path:'/'});
    loadWorldInfo();
}

function loadWorldInfo(){
    api.call('get_world_properties', {
        world_uid: currentWorld
    }, success=function(data){
        available_object_types = data.available_worldobjects.sort();
        initializeControls();
        refreshWorldView();
        world_data = data;
        worldRunning = data.is_active;
        currentWorldSimulationStep = data.current_step;
        if('assets' in data){
            var iconhtml = '<img src="/static/island/unknownbox.png" id="icon_default_object" /><img src="/static/island/Micropsi.png" id="icon_default_agent" />';
            for(var key in data.assets.icons){
                iconhtml += '<img src="/static/'+data.assets.icons[key]+'" id="icon_' + key + '" /> ';
            }
            $('#world_objects_icons').html(iconhtml);
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


function WorldObject(uid, x, y, orientation, name, type, parameters){
    this.uid = uid;
    this.x = x;
    this.y = y;
    this.orientation = orientation || 0;
    this.name = name || "";
    this.type = type || "";
    this.parameters = parameters;
}

function addObject(worldobject){
    if(! (worldobject.uid in objects)) {
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    } else {
        redrawObject(objects[worldobject.uid]);
    }
    return worldobject;
}

function addAgent(worldobject){
    if(! (worldobject.uid in objects)) {
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    } else {
        redrawObject(objects[worldobject.uid]);
    }
    objects[worldobject.uid] = worldobject;
    agentsList.html(agentsList.html() + '<tr><td><a href="#" data="'+worldobject.uid+'" class="world_agent">'+worldobject.name+' ('+worldobject.type+')</a></td></tr>');
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
        var path = createObjectShape(worldobject, bounds);
        symbols[worldobject.type] = new Symbol(path);
        //objectLayer.addChild(symbols[worldobject.type]);
    }
    worldobject.representation = symbols[worldobject.type].place();
    if(worldobject.orientation){
        worldobject.representation.rotate(worldobject.orientation);
    }
    worldobject.representation.position = new Point(worldobject.x, worldobject.y);
    worldobject.representation.name = worldobject.uid;
    objectLayer.addChild(worldobject.representation);
}

function createObjectShape(worldobject, bounds){
    var raster = new Raster(getObjectIcon(worldobject));
    if(worldobject.type in scale_factors){
        raster.scale(scale_factors[worldobject.type]);
    }
    raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
    return raster;
}

function getObjectIcon(worldobject){
    switch(worldobject.type){
        case "Lightsource":
        case "Braitenberg":
        case "Survivor":
        case "PalmTree":
        case "Maple":
        case "Braintree":
        case "Wirselkraut":
        case "Thornbush":
        case "Juniper":
        case "Champignon":
        case "FlyAgaric":
        case "Stone":
        case "Boulder":
        case "Menhir":
        case "Waterhole":
            return 'icon_'+worldobject.type;
        default:
            if(worldobject.uid  && worldobject.uid in agents){
                return 'icon_default_agent';
            } else {
                return 'icon_default_object';
            }
    }
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
    var content = '';
    if(worldobject.uid in agents){
        content = (worldobject.name) ? worldobject.name : worldobject.uid;
    } else {
        content = worldobject.type;
    }
    content += ' ('+parseInt(worldobject.x)+'/'+parseInt(worldobject.y)+')';
    text.content = content;
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

movePath = false;
path = null;

clickLabel = false;
clickHighlight = false;
clickPosition = null;

selected = null;

$('body').mousedown(function(event){
    if(addObjectMode && event.target != canvas[0] && event.target != $('#set_worldobject_sprinkle_mode')[0]){
        unsetAddObjectMode();
    }
});

function setAddObjectMode(objecttype){
    addObjectMode = objecttype;
    addObjectGhost = new Raster(getObjectIcon({type:addObjectMode}));
    addObjectGhost.scale(scale_factors[addObjectMode] / 2);
    addObject.position = new Point(-100, -100);
    objectLayer.addChild(addObjectGhost);
    $('#set_worldobject_sprinkle_mode').text("Done").addClass('active');
}

function unsetAddObjectMode(){
    addObjectMode = null;
    addObjectGhost.remove();
    addObjectGhost = null;
    $('#set_worldobject_sprinkle_mode').text("add objects").removeClass('active').blur();
}

function onKeyDown(event) {
    if(!addObjectMode){
        if (event.key == "backspace" || event.key == "delete") {
            if (event.event.target.tagName == "BODY") {
                event.preventDefault(); // browser-back
                if(selected){
                    if(!(selected.uid in agents)){
                        deleteWorldObject(selected);
                        unselectObject();
                        selected = null;
                    }
                }
            }
        }
    } else if(event.key == 'escape'){
        unsetAddObjectMode();
    }
}

function onMouseDown(event){
    clickPosition = null;
    showDefaultForm();
    var p = event.point;
    if(addObjectMode){
        if(event.event.button == 2){
            unsetAddObjectMode();
            return;
        } else {
            createWorldObject(addObjectMode, p);
            return;
        }
    }
    var hit = false;
    for (var uid in objects) {
        if(objects[uid].representation && objects[uid].representation.hitTest(p)){
            selected = objects[uid];
            selectObject(objects[uid]);
            hit = true;
            break;
        }
    }
    if(!hit){
        unselectObject();
    }
}

function onMouseMove(event) {
    var p = event.point;
    if(event.event.target == canvas[0]){
        $('#world_status').val('Pos: ' + p.x + ' / ' + p.y);
    } else {
        $('#world_status').val('Pos: ');
    }

    if(addObjectMode && addObjectGhost){
        addObjectGhost.position = p;
    }

    // hovering
    if (hoverUid) { // unhover
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
                    highlightObject(hoverUid);
                }
                path = objectLayer.children[uid];
                movePath = true;
                return;
            }
        }
    }
    if (!hoverUid && label){
        label.remove();
        label = null;
        movePath = null;
    }
}

function onMouseDrag(event) {
    var p = event.point;
    if(event.event.target == canvas[0]){
        $('#world_status').val('Pos: ' + p.x + ' / ' + p.y);
    } else {
        $('#world_status').val('Pos: ');
    }
    if (movePath) {
        path.objectMoved = true;
        path.position += event.delta;
        var obj = objects[path.name];
        obj.x += event.delta.x/viewProperties.zoomFactor;
        obj.y += event.delta.y/viewProperties.zoomFactor;
        obj.bounds = calculateObjectBounds(obj);
        if(label){
            var height = (viewProperties.fontSize*viewProperties.zoomFactor + 2*viewProperties.padding);
            label.position = new Point(
                obj.bounds.x + (viewProperties.label.x * viewProperties.zoomFactor),
                Math.max(height, obj.bounds.y + (viewProperties.label.y * viewProperties.zoomFactor)));
        }
        if(selectionBorder){
            selectionBorder.position += event.delta;
        }
    }
}

function onMouseUp(event) {
    var p = event.point;
    if (movePath) {
        if(path.objectMoved && objects[path.name]){
            // update position on server
            path.objectMoved = false;
            setObjectProperties(objects[path.name], objects[path.name].x, objects[path.name].y);
            movePath = false;
            updateViewSize();
        }
    }
}

selectionBorder = null;
function unselectObject(){
    if(selectionBorder){
        selectionBorder.remove();
    }
}
function selectObject(worldobject){
    if(selectionBorder){
        unselectObject();
    }
    var bounds = worldobject.representation.bounds;
    selectionBorder = new Path.Rectangle(worldobject.x - (bounds.width / 2), worldobject.y - (bounds.height  /2), bounds.width , bounds.height );
    selectionBorder.strokeWidth = 1;
    selectionBorder.name = 'selectionBorder';
    selectionBorder.strokeColor = viewProperties.selectionColor;
    if(worldobject.orientation){
        selectionBorder.rotate(worldobject.orientation);
    }
    objectLayer.addChild(selectionBorder);

}

function highlightObject(uid){
    label = getLegend(objects[uid]);
    objectLayer.addChild(label);
    view.draw(true);
}

function highlightAgent(uid){
    label = getLegend(agents[uid]);
    objectLayer.addChild(label);
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
    if(bounds.y <= parent.scrollTop()) parent.scrollTop(bounds.y - 50);
    else if(bounds.y + bounds.height >= (parent.innerHeight() + parent.scrollTop())) parent.scrollTop(bounds.y - parent.innerHeight() + bounds.height + 50);
    if(bounds.x <= parent.scrollLeft()) parent.scrollLeft(bounds.x - 50);
    else if (bounds.x + bounds.width >= (parent.innerWidth() + parent.scrollLeft())) parent.scrollLeft(bounds.x - parent.innerWidth() + bounds.width + 50);
}


// --------------------------- controls -------------------------------------------------------- //

function initializeControls(){
    $('.editor_field form .controls button[type="reset"]').on('click', showDefaultForm);

    $('#available_worldobjects').html('<option>' + available_object_types.join('</option><option>')+'</option>');
    agentsList.on('click', function(event){
        event.preventDefault();
        var target = $(event.target);
        if(target.attr('class') == 'world_agent' && target.attr('data')){
            highlightAgent(target.attr('data'));
            scrollToObject(agents[target.attr('data')]);
        }
    });
    $('#scene_viewer_agent').on('change', refreshSceneView);

    $('#set_worldobject_sprinkle_mode').on('click', function(event){
        event.preventDefault();
        if(addObjectMode){
            unsetAddObjectMode();
        } else {
            setAddObjectMode($('#available_worldobjects').val());
        }
    });
}



// ------------------------ side bar form stuff --------------------------------------------- //

function showDefaultForm(){
    $('#world_forms .form-horizontal').hide();
    $('#world_forms .form-default').show();
}

function showObjectForm(worldobject){
    if(worldobject && worldobject.uid in agents){
        return false;
    }
    if(!worldobject) worldobject = {};
    $('#world_forms .form-horizontal').hide();
    $('#wo_uid_input').val(worldobject.uid);
    $('#wo_name_input').val(worldobject.name);
    var param_table = $('#wo_parameter_list');
    var param_html = '';
    for(var key in worldobject.parameters){
        param_html += "<tr><td><input type=\"text\" class=\"param_name inplace\" name=\"param_name\" value=\""+key+"\" /></td><td><input type=\"text\" class=\"inplace\" name=\"param_"+key+"\" val=\""+worldobject.params[key]+"\" /></td></tr>";
    }
    param_table.html(param_html);
    $('#edit_worldobject').show();
}


// ------------------------ API Communication --------------------------------------------------- //

function createWorldObject(type, pos){
    api.call('add_worldobject', {world_uid: currentWorld, type: type, position: [pos.x, pos.y]}, function(result){
        addObject(new WorldObject(result, pos.x, pos.y, 0, '', type, {}));
        updateViewSize();
    });
}

function deleteWorldObject(worldobject){
    objects[worldobject.uid].representation.remove();
    delete objects[worldobject.uid];
    api.call('delete_worldobject', {'world_uid': currentWorld, 'object_uid': worldobject.uid}, function(){
        dialogs.notification("worldobject deleted");
    });
}

function setObjectProperties(worldobject, x, y, name, orientation, parameters){
    if(worldobject.uid in agents){
        return setAgentProperties(worldobject, x, y, name, orientation, parameters);
    }
    if(x) worldobject.x = x;
    if(y) worldobject.y = y;
    if(name) worldobject.name = name;
    if(orientation) worldobject.orientation = orientation;
    if(parameters) worldobject.parameters = parameters;
    data = {
        world_uid: currentWorld,
        uid: worldobject.uid,
        position: [worldobject.x, worldobject.y],
        name: worldobject.name,
        orientation: worldobject.orientation,
        parameters: worldobject.parameters || {}
    };
    api.call('set_worldobject_properties', data, function(result){
        redrawObject(worldobject);
    }, api.defaultErrorCallback);
}

function setAgentProperties(worldobject, x, y, name, orientation, parameters){
    if(x) worldobject.x = x;
    if(y) worldobject.y = y;
    if(name) worldobject.name = name;
    if(orientation) worldobject.orientation = orientation;
    if(parameters) worldobject.parameters = parameters;
    data = {
        world_uid: currentWorld,
        uid: worldobject.uid,
        position: [worldobject.x, worldobject.y],
        name: worldobject.name,
        orientation: worldobject.orientation,
        parameters: worldobject.parameters || {}
    };
    api.call('set_worldagent_properties', data, function(result){
        redrawObject(worldobject);
    }, api.defaultErrorCallback);
}
