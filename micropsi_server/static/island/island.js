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
    typeColors: {
        "other": new Color ("#94c2f5")
    },
    label: {
        x: 10,
        y: -10
    }
};

// TODO: this really should be loaded from the server
var available_object_types = [
    'Lightsource',
    'PalmTree',
    'Maple',
    'Braintree',
    'Wirselkraut',
    'Thornbush',
    'Juniper',
    'Champignon',
    'FlyAgaric',
    'Stone',
    'Boulder',
    'Menhir',
    'Waterhole'
];

objects = {};
symbols = {};
agents = {};

objectLayer = new Layer();
objectLayer.name = 'ObjectLayer';

currentWorldSimulationStep = -1;

var world_data = null;

if (currentWorld){
    setCurrentWorld(currentWorld);
}

scenes = {};

var objectList = $('#world_objects_list table');
var agentsList = $('#world_agents_list table');

initializeControls();
initializeMenus();


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
            $('#world_status').val(data.status_message);
            // treat agents and objects the same
            data.objects = jQuery.extend(data.objects, data.agents);
            for(var key in objects){
                if(!(key in data.objects)){
                    if(objects[key].representation){
                        objects[key].representation.remove();
                        delete objects[key];
                        if(key in scenes){
                            delete scenes[key]
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
                        agents[key] = objects[key]
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

            updateSceneViewer();
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

function updateSceneViewer(){
    var selector = $('#scene_viewer_agent');
    var selected = selector.val();
    var selector_html = '';
    for(var key in scenes){
        selector_html += '<option value="'+key+'">'+objects[key].name+'</option>';
    }
    if(selector_html != ''){
        selector_html = '<option val="">choose...</option>' + selector_html;
        $('.scene_viewer_section').show();
    } else{
        $('.scene_viewer_section').hide();
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
        refreshWorldView();
        world_data = data;
        worldRunning = data.is_active;
        currentWorldSimulationStep = data.step;
        if('assets' in data){
            var iconhtml = '';
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
    objectList.html(objectList.html() + '<tr><td><a href="#" data="'+worldobject.uid+'" class="worldobject_edit">'+worldobject.name+' ('+worldobject.type+')</a></td></tr>');
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
    worldobject.representation.position = new Point(worldobject.x, worldobject.y);
    worldobject.representation.name = worldobject.uid;
    objectLayer.addChild(worldobject.representation);
}

function createObjectShape(worldobject, bounds){
    var raster;
    switch(worldobject.type){
        case "Lightsource":
            raster = new Raster('icon_' + worldobject.type);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Braitenberg":
            raster = new Raster('icon_' + worldobject.type);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Survivor":
            raster = new Raster('icon_' + worldobject.type);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "PalmTree":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.5);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Maple":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.7);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Braintree":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.5);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Wirselkraut":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.2);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Thornbush":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(1);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Juniper":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.4);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Champignon":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.125);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "FlyAgaric":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.2);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Stone":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.2);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Boulder":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.6);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Menhir":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.4);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        case "Waterhole":
            raster = new Raster('icon_' + worldobject.type);
            raster.scale(0.4);
            raster.position = new Point(bounds.x + raster.width/2, bounds.y+bounds.height/2);
            raster.rotate(worldobject.orientation);
        return raster;

        default:
            var shape = new Path.Circle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
            if (worldobject.type in viewProperties.typeColors){
                shape.fillColor = viewProperties.typeColors[worldobject.type];
            } else {
                shape.fillColor = viewProperties.typeColors['other'];
            }
        return shape;
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
    text.content = (worldobject.name ? worldobject.name : worldobject.uid) + '('+parseInt(worldobject.x)+'/'+parseInt(worldobject.y)+')';
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

function onMouseDown(event){
    clickPosition = null;
    showDefaultForm();
    // context menus:
    if (event.modifiers.control || event.event.button == 2){
        openContextMenu("#create_object_menu", event);
    }
}

function onMouseMove(event) {
    var p = event.point;
    if(event.event.target == canvas[0]){
        $('#world_status').val('Pos: ' + p.x + ' / ' + p.y);
    } else {
        $('#world_status').val('Pos: ');
    }
    // hovering
    if (hoverUid) { // unhover
        if(hoverUid in objects){
            //objects[hoverUid].representation.scale((1/viewProperties.hoverScale));
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
    }
}

function onMouseUp(event) {
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

// --------------------------- menus -------------------------------------------------------- //

function initializeMenus(){
    $('#create_object_menu li').on('click', handleContextMenu);
}

function openContextMenu(menu_id, event){
    event.event.cancelBubble = true;
    clickPosition = event.point;
    $(menu_id).css({
        position: "absolute",
        zIndex: 500,
        marginLeft: -5, marginTop: -5,
        top: event.event.pageY, left: event.event.pageX });
    $(menu_id+" .dropdown-toggle").dropdown("toggle");
}

function handleContextMenu(event){
    var item = $(event.target);
    event.preventDefault();
    switch(item.attr('data')){
        case 'add_worldobject':
            showObjectForm();
    }
}

// --------------------------- controls -------------------------------------------------------- //

function initializeControls(){
    $('.editor_field form .controls button[type="reset"]').on('click', showDefaultForm);
    $('#add_object_link').on('click', function(event){
        event.preventDefault();
        $('#wo_uid_input').attr('disabled', 'disabled');
        showObjectForm();
    });

    $('#add_object_param').on('click', function(event){
        event.preventDefault();
        var param_table = $('#wo_parameter_list');
        var html = param_table.html();
        html += '<tr><td><input type="text" name="param_key" class="param_key inplace" /></td><td><input type="text" name="new_param_val" class="param_val inplace" /></td></tr>';
        param_table.html(html);
    });
    $('#wo_type_input').html('<option>' + available_object_types.join('</option><option>')+'</option>');
    $('#edit_worldobject .btn-primary').on('click', handleSubmitWorldobject);
    agentsList.on('click', function(event){
        event.preventDefault();
        var target = $(event.target);
        if(target.attr('class') == 'world_agent' && target.attr('data')){
            highlightAgent(target.attr('data'));
            scrollToObject(agents[target.attr('data')]);
        }
    });
    objectList.on('click', function(event){
        event.preventDefault();
        var target = $(event.target);
        if(target.attr('class') == 'worldobject_edit' && target.attr('data')){
            showObjectForm(objects[target.attr('data')]);
            highlightObject(target.attr('data'));
            scrollToObject(objects[target.attr('data')]);
        }
    });
    $('#scene_viewer_agent').on('change', refreshSceneView);
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


// ------------------------ side bar form stuff --------------------------------------------- //

function showDefaultForm(){
    $('#world_forms .form-horizontal').hide();
    $('#world_forms .form-default').show();
}

function showObjectForm(worldobject){
    if(!worldobject) worldobject = {};
    $('#world_forms .form-horizontal').hide();
    $('#wo_uid_input').val(worldobject.uid);
    $('#wo_name_input').val(worldobject.name);
    $('#wo_type_input').val(worldobject.type);
    var param_table = $('#wo_parameter_list');
    var param_html = '';
    for(var key in worldobject.parameters){
        param_html += "<tr><td><input type=\"text\" class=\"param_name inplace\" name=\"param_name\" value=\""+key+"\" /></td><td><input type=\"text\" class=\"inplace\" name=\"param_"+key+"\" val=\""+worldobject.params[key]+"\" /></td></tr>";
    }
    param_table.html(param_html);
    $('#edit_worldobject').show();
}


// ------------------------ API Communication --------------------------------------------------- //

function handleSubmitWorldobject(event){
    event.preventDefault();
    var uid = $('#wo_uid_input').val();
    data = {
        'world_uid': currentWorld,
        'name': $('#wo_name_input').val(),
        'type': $('#wo_type_input').val(),
        'position': [10, 10],
        'parameters': {}
    };
    var param_fields = $('input[name^="param_"]', $('#edit_worldobject'));
    for(var i in param_fields){
        if(param_fields[i].name == "param_name"){
            data.parameters[param_fields[i].value] = param_fields[++i].value;
        }
    }
    if(uid){
        setObjectProperties(objects[uid], null, null, data.name, null, data.parameters);
    } else {
        var pos;
        if(clickPosition){
            pos = clickPosition;
        } else {
            var parent = canvas.parent();
            pos = new Point(parent.scrollTop() + (parent.innerHeight() / 2), parent.scrollLeft() + (parent.innerWidth()/2));
        }
        data.position = [pos.x, pos.y];
        api.call('add_worldobject', data, function(result){
            if(result.status =='success'){
                addObject(new WorldObject(result.uid, pos.x, pos.y, 0, data.name, data.type, data.parameters));
            }
            updateViewSize();
        }, api.defaultErrorCallback);
    }
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
        if(result.status =='success'){
            redrawObject(worldobject);
        }
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
        if(result.status =='success'){
            redrawObject(worldobject);
        }
    }, api.defaultErrorCallback);
}
