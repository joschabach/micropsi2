/*
 * viewer for the world.
 */

var canvas = $('#world');

var viewProperties = {
    frameWidth: 1445,
    zoomFactor: 1,
    objectWidth: 12,
    lineHeight: 15,
    objectLabelColor: new Color("#94c2f5"),
    objectForegroundColor: new Color("#000000"),
    fontSize: 10,
    symbolSize: 14,
    highlightColor: new Color("#ffffff"),
    gateShadowColor: new Color("#888888"),
    shadowColor: new Color("#000000"),
    shadowStrokeWidth: 0,
    shadowDisplacement: new Point(0.5, 1.5),
    innerShadowDisplacement: new Point(0.2, 0.7),
    padding: 3,
    label: {
        x: 10,
        y: -10
    }
};

var i = 0;
var next_refresh = 0;

var available_object_types = ['Lightsource'];

objects = {};
symbols = {};
agents = {};

currentWorld = $.cookie('selected_world') || null;

objectLayer = new Layer();
objectLayer.name = 'ObjectLayer';

currentWorldSimulationStep = -1;

var world_data = null;

if (currentWorld) {
    setCurrentWorld(currentWorld);
}

worldRunning = false;

var objectList = $('#world_objects_list table');
var agentsList = $('#world_agents_list table');

initializeControls();

//wasRunning = false;
//$(window).focus(function () {
//    worldRunning = wasRunning;
//    if (wasRunning) {
//        refreshWorldView();
//    }
//})
//    .blur(function () {
//        wasRunning = worldRunning;
//        worldRunning = false;
//    });

function refreshWorldView() {

    /* api.call('get_world_properties', {
     world_uid: currentWorld
     }, success = function (data) {
     if ('assets' in data) {
     var randomnumber = Math.floor(Math.random() * 10000001)
     //canvas.css('background', 'url("/static/' + data.assets.background + "?q=" + randomnumber + '") no-repeat top left');
     //var objContext = world.getContext('2d');
     //var objImg = new Image()
     //objImg.src = ("/static/" + data.assets.background + "?q=" + randomnumber);
     //objContext.drawImage(objImg, 200, 800);
     //console.log("canvas is " + canvas);
     //console.log("canvas.parent() is " + canvas.parent());
     //console.log("world is " + world);
     }
     }, error = function (data) {
     $.cookie('selected_world', '', {expires: -1, path: '/'});
     dialogs.notification(data.Error, 'error');
     });*/

    /*if (next_refresh == 0) {

        i++;
        var randomnumber = Math.floor(Math.random() * 10000001)
        screenshot0.src = "/minecraft/screenshot.png?q=" + i * randomnumber;
        console.log("refreshedd " + 0 + " " + i * randomnumber);
        next_refresh == 1;
    } else if (next_refresh == 1) {
        i++;
        var randomnumber = Math.floor(Math.random() * 10000001)
        screenshot1.src = "/minecraft/screenshot.png?q=" + i * randomnumber;
        console.log("refreshedd " + 1 + " " + i * randomnumber);
        next_refresh == 0;
    }*/

    api.call('get_world_view',
        {world_uid: currentWorld, step: currentWorldSimulationStep},
        function (data) {
            if (jQuery.isEmptyObject(data)) {
                if (worldRunning) {
                    setTimeout(refreshWorldView, 100);
                }
                return null;
            }
            currentWorldSimulationStep = data.current_step;
            $('#world_step').val(currentWorldSimulationStep);
            $('#world_status').val(data.status_message);
            // treat agents and objects the same
            data.objects = jQuery.extend(data.objects, data.agents);
            for (var key in objects) {
                if (!(key in data.objects)) {
                    if (objects[key].representation) {
                        objects[key].representation.remove();
                        delete objects[key];
                    }
                } else {
                    if (data.objects[key].position && data.objects[key].position.length == 2) {
                        objects[key].x = data.objects[key].position[0];
                        objects[key].y = data.objects[key].position[1];
                        objects[key].representation.rotate(data.objects[key].orientation - objects[key].orientation);
                        objects[key].orientation = data.objects[key].orientation;
                        objects[key].representation.position = new Point(objects[key].x, objects[key].y);
                    } else {
                        console.log('obj has no pos: ' + key);
                    }
                }
                delete data.objects[key];
            }
            for (key in data.objects) {
                if (data.objects[key].position && data.objects[key].position.length == 2) {
                    if (key in data.agents) {
                        addAgent(new WorldObject(key, data.objects[key].position[0], data.objects[key].position[1], data.objects[key].orientation, data.objects[key].name, data.objects[key].type));
                    } else {
                        addObject(new WorldObject(key, data.objects[key].position[0], data.objects[key].position[1], data.objects[key].orientation, data.objects[key].name, data.objects[key].type));
                    }
                } else {
                    console.log('obj has no pos ' + key);
                }
            }

            updateViewSize();
            if (worldRunning) {
                refreshWorldView();
            }
        }, error = function (data) {
            $.cookie('selected_world', '', {expires: -1, path: '/'});
            dialogs.notification(data.Error, 'error');
        }
    );
}

function setCurrentWorld(uid) {
    currentWorld = uid;
    $.cookie('selected_world', currentWorld, {expires: 7, path: '/'});
    loadWorldInfo();
}


function loadWorldInfo() {

    /*var world_div = document.getElementsByClassName("editor_field span9").item(1);
    var screenshot_div = document.createElement("div");
    screenshot_div.id = "canvas_div";
    world_div.appendChild(screenshot_div);

    var canvas_div = document.getElementById("canvas_div")

    var newImg = document.createElement("img");
    newImg.id = "screenshot0";
    //newImg.src = "/static/minecraft/screenshot.jpg";
    newImg.style = "position: absolute; top: 30px; right: 5px;";
    canvas_div.appendChild(newImg);


    var newImg2 = document.createElement("img");
    newImg2.id = "screenshot1";
    //newImg2.src = "/static/minecraft/screenshot.jpg";
    newImg2.style = "position: absolute; top: 30px; right: 5px;";
    canvas_div.appendChild(newImg2);*/

    api.call('get_world_properties', {
        world_uid: currentWorld
    }, success = function (data) {
        refreshWorldView();
        world_data = data;
        worldRunning = data.is_active;
        currentWorldSimulationStep = data.step;
        if ('assets' in data) {
            var iconhtml = '';
            for (var key in data.assets.icons) {
                iconhtml += '<img src="/static/' + data.assets.icons[key] + '" id="icon_' + key + '" /> ';
            }
            $('#world_objects_icons').html(iconhtml);
            if (data.assets.x && data.assets.y) {
                view.viewSize = new Size(data.assets.x, data.assets.y);
            }
            //canvas.css('background', 'url("/static/' + data.assets.background + '") no-repeat top left');
        }
    }, error = function (data) {
        $.cookie('selected_world', '', {expires: -1, path: '/'});
        dialogs.notification(data.Error, 'error');
    });
}

function updateViewSize() {
    view.draw(true);
}


function WorldObject(uid, x, y, orientation, name, type, parameters) {
    this.uid = uid;
    this.x = x;
    this.y = y;
    this.orientation = orientation || 0;
    this.name = name || "";
    this.type = type || "";
    this.parameters = parameters;
}

function addObject(worldobject) {
    if (!(worldobject.uid in objects)) {
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    } else {
        redrawObject(objects[worldobject.uid]);
    }
    objectList.html(objectList.html() + '<tr><td><a href="#" data="' + worldobject.uid + '" class="worldobject_edit">' + worldobject.name + ' (' + worldobject.type + ')</a></td></tr>');
    return worldobject;
}

function addAgent(worldobject) {
    if (!(worldobject.uid in objects)) {
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    } else {
        redrawObject(objects[worldobject.uid]);
    }
    agents[worldobject.uid] = worldobject;
    agentsList.html(agentsList.html() + '<tr><td><a href="#" data="' + worldobject.uid + '" class="worldobject_edit">' + worldobject.name + ' (' + worldobject.type + ')</a></td></tr>');
    return worldobject;
}

function redrawObject(obj) {
    if (objects[obj.uid].representation) {
        objects[obj.uid].representation.remove();
    }
    renderObject(obj);
}

function renderObject(worldobject) {
    if (!(worldobject.type in symbols)) {
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

function createObjectShape(worldobject, bounds) {
    var raster;
    switch (worldobject.type) {
        case "Lightsource":
            raster = new Raster('icon_Lightsource');
            raster.position = new Point(bounds.x + raster.width / 2, bounds.y + bounds.height / 2);
            raster.rotate(worldobject.orientation);
            return raster;

        case "Braitenberg":
            raster = new Raster('icon_Braitenberg');
            raster.position = new Point(bounds.x + raster.width / 2, bounds.y + bounds.height / 2);
            raster.rotate(worldobject.orientation);
            return raster;

        default:
            var shape = new Path.Circle(new Point(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2), bounds.width / 2);
            if (worldobject.type in viewProperties.typeColors) {
                shape.fillColor = viewProperties.typeColors[worldobject.type];
            } else {
                shape.fillColor = viewProperties.typeColors['other'];
            }
            return shape;
    }
}

function calculateObjectBounds(worldobject) {
    var size = viewProperties.objectWidth * viewProperties.zoomFactor;
    return {
        x: worldobject.x * viewProperties.zoomFactor - size / 2,
        y: worldobject.y * viewProperties.zoomFactor - size / 2,
        width: size,
        height: size
    };
}

function getLegend(worldobject) {
    var legend = new Group();
    legend.name = 'objectLegend';
    var bounds = worldobject.representation.bounds;
    var height = (viewProperties.fontSize * viewProperties.zoomFactor + 2 * viewProperties.padding);
    var point = new Point(
        bounds.x + (viewProperties.label.x * viewProperties.zoomFactor),
        Math.max(height, bounds.y + (viewProperties.label.y * viewProperties.zoomFactor)));
    var text = new PointText(point);
    text.justification = 'left';
    text.content = (worldobject.name ? worldobject.name : worldobject.uid);
    text.characterStyle = {
        fillColor: 'black',
        fontSize: viewProperties.fontSize * viewProperties.zoomFactor
    };
    if (point.x + text.bounds.width + 2 * viewProperties.padding > view.viewSize.width) {
        point = new Point(
            view.viewSize.width - (text.bounds.width + 3 * viewProperties.padding),
            point.y);
        text.point = point;
    }
    var container = new Path.Rectangle(new Point(point.x - viewProperties.padding, point.y + viewProperties.padding), new Size(text.bounds.width + 2 * viewProperties.padding, -height));
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

function onMouseDown(event) {
    showDefaultForm();
}

function onMouseMove(event) {
    var p = event.point;
    // hovering
    if (hoverUid) { // unhover
        if (hoverUid in objects) {
            //objects[hoverUid].representation.scale((1/viewProperties.hoverScale));
        }
        hoverUid = null;
    }
    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    for (var uid in objects) {
        if (objects[uid].representation) {
            var bounds = objects[uid].representation.bounds;
            if (bounds.contains(p)) {
                if (hoverUid != uid) {
                    hoverUid = uid;
                    if (label) {
                        label.remove();
                    }
                    if (clickHighlight) {
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
    if (!hoverUid && label) {
        label.remove();
        label = null;
        movePath = null;
    }
}

function onMouseDrag(event) {
    if (movePath) {
        path.objectMoved = true;
        path.position += event.delta;
        var obj = objects[path.name];
        obj.x += event.delta.x / viewProperties.zoomFactor;
        obj.y += event.delta.y / viewProperties.zoomFactor;
        obj.bounds = calculateObjectBounds(obj);
        if (label) {
            var height = (viewProperties.fontSize * viewProperties.zoomFactor + 2 * viewProperties.padding);
            label.position = new Point(
                obj.bounds.x + (viewProperties.label.x * viewProperties.zoomFactor),
                Math.max(height, obj.bounds.y + (viewProperties.label.y * viewProperties.zoomFactor)));
        }
    }
}

function onMouseUp(event) {
    if (movePath) {
        if (path.objectMoved && objects[path.name]) {
            // update position on server
            path.objectMoved = false;
            setObjectProperties(objects[path.name], objects[path.name].x, objects[path.name].y);
            movePath = false;
            updateViewSize();
        }
    }
}

function highlightObject(uid) {
    label = getLegend(objects[uid]);
    objectLayer.addChild(label);
    view.draw(true);
}

function removeClickHighlight() {
    if (clickHighlight) {
        objects[clickHighlight].representation.scale(1 / viewProperties.hoverScale);
        clickHighlight = null;
    }
    if (label) {
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

function scrollToObject(obj) {
    var parent = canvas.parent();
    var bounds = obj.representation.bounds;
    if (bounds.y <= parent.scrollTop()) parent.scrollTop(bounds.y - 20);
    else if (bounds.y + bounds.height >= (parent.innerHeight() + parent.scrollTop() - 20)) parent.scrollTop(bounds.y + 20);
    if (bounds.x <= parent.scrollLeft()) parent.scrollLeft(bounds.x - 20);
    else if (bounds.x + bounds.width >= (parent.innerWidth() + parent.scrollLeft() - 20)) parent.scrollLeft(bounds.x + 20);
}

// --------------------------- controls -------------------------------------------------------- //

function initializeControls() {
    $('#world_reset').on('click', resetWorld);
    $('#world_step_forward').on('click', stepWorld);
    $('#world_start').on('click', startWorldrunner);
    $('#world_stop').on('click', stopWorldrunner);

    $('#add_object_link').on('click', function (event) {
        event.preventDefault();
        $('#wo_uid_input').attr('disabled', 'disabled');
        showObjectForm();
    });

    $('#add_object_param').on('click', function (event) {
        event.preventDefault();
        var param_table = $('#wo_parameter_list');
        var html = param_table.html();
        html += '<tr><td><input type="text" name="param_key" class="param_key inplace" /></td><td><input type="text" name="new_param_val" class="param_val inplace" /></td></tr>';
        param_table.html(html);
    });
    $('#wo_type_input').html('<option>' + available_object_types.join('</option><option>') + '</option>');
    $('#edit_worldobject .btn-primary').on('click', handleSubmitWorldobject);
    objectList.on('click', function (event) {
        event.preventDefault();
        var target = $(event.target);
        if (target.attr('class') == 'worldobject_edit' && target.attr('data')) {
            showObjectForm(objects[target.attr('data')]);
            highlightObject(target.attr('data'));
        }
    });
}

function resetWorld(event) {
    event.preventDefault();
    worldRunning = false;
    api.call('revert_world', {world_uid: currentWorld}, function () {
        setCurrentWorld(currentWorld);
    });
}

function stepWorld(event) {
    event.preventDefault();
    if (worldRunning) {
        stopWorldrunner(event);
    }
    api.call('step_world', {world_uid: currentWorld}, function () {
        refreshWorldView();
    });
}

function startWorldrunner(event) {
    event.preventDefault();
    api.call('start_worldrunner', {world_uid: currentWorld}, function () {
        worldRunning = true;
        refreshWorldView();
    });
}

function stopWorldrunner(event) {
    event.preventDefault();
    worldRunning = false;
    api.call('stop_worldrunner', {world_uid: currentWorld}, function () {
        $('#world_step').val(currentWorldSimulationStep);
    });
}


// ------------------------ side bar form stuff --------------------------------------------- //

function showDefaultForm() {
    $('#world_forms .form-horizontal').hide();
    $('#world_status').show();
    $('#world_objects').show();
}

function showObjectForm(worldobject) {
    if (!worldobject) worldobject = {};
    $('#world_forms .form-horizontal').hide();
    $('#wo_uid_input').val(worldobject.uid);
    $('#wo_name_input').val(worldobject.name);
    $('#wo_type_input').val(worldobject.type);
    var param_table = $('#wo_parameter_list');
    var param_html = '';
    for (var key in worldobject.parameters) {
        param_html += "<tr><td><input type=\"text\" class=\"param_name inplace\" name=\"param_name\" value=\"" + key + "\" /></td><td><input type=\"text\" class=\"inplace\" name=\"param_" + key + "\" val=\"" + worldobject.params[key] + "\" /></td></tr>";
    }
    param_table.html(param_html);
    $('#edit_worldobject').show();
}


// ------------------------ API Communication --------------------------------------------------- //

function handleSubmitWorldobject(event) {
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
    for (var i in param_fields) {
        if (param_fields[i].name == "param_name") {
            data.parameters[param_fields[i].value] = param_fields[++i].value;
        }
    }
    if (uid) {
        setObjectProperties(objects[uid], null, null, data.name, null, data.parameters);
    } else {
        api.call('add_worldobject', data, function (result) {
            if (result.status == 'success') {
                addObject(new WorldObject(result.uid, 10, 10, 0, data.name, data.type, data.parameters));
            }
            updateViewSize();
        }, api.defaultErrorCallback);
    }
}

function setObjectProperties(worldobject, x, y, name, orientation, parameters) {
    if (worldobject.uid in agents) {
        return setAgentProperties(worldobject, x, y, name, orientation, parameters);
    }
    if (x) worldobject.x = x;
    if (y) worldobject.y = y;
    if (name) worldobject.name = name;
    if (orientation) worldobject.orientation = orientation;
    if (parameters) worldobject.parameters = parameters;
    data = {
        world_uid: currentWorld,
        uid: worldobject.uid,
        position: [worldobject.x, worldobject.y],
        name: worldobject.name,
        orientation: worldobject.orientation,
        parameters: worldobject.parameters || {}
    };
    api.call('set_worldobject_properties', data, function (result) {
        if (result.status == 'success') {
            redrawObject(worldobject);
        }
    }, api.defaultErrorCallback);
}

function setAgentProperties(worldobject, x, y, name, orientation, parameters) {
    if (x) worldobject.x = x;
    if (y) worldobject.y = y;
    if (name) worldobject.name = name;
    if (orientation) worldobject.orientation = orientation;
    if (parameters) worldobject.parameters = parameters;
    data = {
        world_uid: currentWorld,
        uid: worldobject.uid,
        position: [worldobject.x, worldobject.y],
        name: worldobject.name,
        orientation: worldobject.orientation,
        parameters: worldobject.parameters || {}
    };
    api.call('set_worldagent_properties', data, function (result) {
        if (result.status == 'success') {
            redrawObject(worldobject);
        }
    }, api.defaultErrorCallback);
}
