/*
 * viewer for the world.
 */


worldscope = paper;

var side_relation = 700/500;
var HEIGHT = 10; // it starts to look super weird with values over 20 and I have no idea why
var WIDTH = Math.round(side_relation * HEIGHT);

var firstLayer ;
var secondLayer;

var current_layer = 1;

currentWorld = $.cookie('selected_world') || null;

objectLayer = new Layer();
objectLayer.name = 'ObjectLayer';

currentWorldSimulationStep = -1;

if (currentWorld) {
    setCurrentWorld(currentWorld);
}

worldRunning = false;

function get_world_data(){
    return {step: currentWorldSimulationStep};
}
function set_world_data(data){
    currentWorldSimulationStep = data.current_step;
    for (var key in data.agents) {
        if (data.agents[key].minecraft_vision_pixel) {

            if (current_layer == 1) {
                console.log("activating second layer ...");
                secondLayer.activate();
            }
            else{
                console.log("activating first layer ...");
                firstLayer.activate();
            }

            var minecraft_pixel = data.agents[key].minecraft_vision_pixel;
            for (var x = 0; x < WIDTH; x++) {
                for (var y = 0; y < HEIGHT; y++) {

                    var raster = new Raster('mc_block_img_' + minecraft_pixel[(y + x * HEIGHT) * 2]);
                    raster.position = new Point(world.width / WIDTH * x, world.height / HEIGHT * y);
                    var distance = minecraft_pixel[(y + x * HEIGHT) * 2 + 1];
                    raster.scale((world.width / WIDTH) / 64 * (1 / Math.pow(distance, 1 / 5)), (world.height / HEIGHT) / 64 * (1 / Math.pow(distance, 1 / 5)));
                }
            }
            if (current_layer == 1) {
                console.log("removing frist layer children ...");
                firstLayer.removeChildren();
                current_layer = 0;
            }
            else{
                console.log("removing frist layer children ...");
                secondLayer.removeChildren();
                current_layer = 1;
            }
            break;
        }
    }

    updateViewSize();
    if (worldRunning) {
        refreshWorldView();
    }
}

register_stepping_function('world', get_world_data, set_world_data);


refreshWorldView = function () {
    worldscope.activate();
    api.call(
        'get_world_view',
        {world_uid: currentWorld, step: currentWorldSimulationStep},
        success=set_world_data,
        error=function (data, outcome, type) {
            $.cookie('selected_world', '', {
                expires: -1,
                path: '/'
            });
            worldRunning = false;
            api.defaultErrorCallback(data, outcome, type)
        }
    );
}

function addAgent(worldobject) {
    if (!(worldobject.uid in objects)) {
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    } else {
        redrawObject(objects[worldobject.uid]);
    }
    objects[worldobject.uid] = worldobject;
    agentsList.html(agentsList.html() + '<tr><td><a href="#" data="' + worldobject.uid + '" class="world_agent">' + worldobject.name + ' (' + worldobject.type + ')</a></td></tr>');
    return worldobject;
}

function setCurrentWorld(uid) {
    currentWorld = uid;
    $.cookie('selected_world', currentWorld, {
        expires: 7,
        path: '/'
    });
    loadWorldInfo();
}

function loadWorldInfo() {

    var all_images = ""

    var editor_div = $("#world_forms");

    $.getScript('/static/minecraft/minecraft_struct.js', function () {
        for (var i = -1; i < 173; i++) {

            var block_name = block_names["" + i];
            all_images = all_images + '<img id="mc_block_img_' + block_name + '" src="/static/minecraft/block_textures/' + block_name + '.png">';

            editor_div.html('<div style="height:0; overflow: hidden">' + all_images + '</div>');
        }
    });

    editor_div.html('<div style="height:0; overflow: hidden">' + all_images + '</div>');

    firstLayer = project.activeLayer;
    secondLayer = new Layer();
    firstLayer.activate();

    api.call('get_world_properties', {
        world_uid: currentWorld
    }, success = function (data) {
        refreshWorldView();
    }, error = function (data) {
        $.cookie('selected_world', '', {
            expires: -1,
            path: '/'
        });
        dialogs.notification(data.Error, 'error');
    });
};

function updateViewSize() {
    view.draw(true);
}