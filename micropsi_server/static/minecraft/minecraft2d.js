/*
 * Viewer for Minecraft 2D projection.
 */

worldscope = paper;

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

    worldscope.activate();
    currentWorldSimulationStep = data.current_step;

    if (data.projection) {

        if (current_layer == 1) {
            console.log("activating second layer ...");
            secondLayer.activate();
        }
        else {
            console.log("activating first layer ...");
            firstLayer.activate();
        }

        var height = data.assets.height;
        var width = data.assets.width;
        var num_pix = 20  // 64 for jonas' textures, 25 for gamepedia

        for (var x = 0; x < width; x++) {
            for (var y = 0; y < height; y++) {
                var raster = new Raster('mc_block_img_' + data.projection[(y + x * height) * 2]);
                // is there a problem if x or y are 0 !? how does js or paper.js handle this ??
                raster.position = new Point(world.width / width * x, world.height / height * y);
                var distance = data.projection[(y + x * height) * 2 + 1];
                // texture images are num_pix pixels long; 1/5 is a heuristic
                // consider defining a different distance function that allows for
                // better distinction of small distances
                raster.scale(
                    (world.width / width) / num_pix * (1 / Math.pow(distance, 1/5)),
                    (world.height / height) / num_pix * (1 / Math.pow(distance, 1/5))
                );
            }
        }

        if (current_layer == 1) {
            console.log("removing frist layer children ...");
            firstLayer.removeChildren();
            current_layer = 0;
        }
        else {
            console.log("removing frist layer children ...");
            secondLayer.removeChildren();
            current_layer = 1;
        }
        // break;
    }

    updateViewSize();
}

register_stepping_function('world', get_world_data, set_world_data);

refreshWorldView = function () {
    api.call('get_world_properties', 
        { world_uid: currentWorld },
        success=set_world_data,
        error = function (data) {
            $.cookie('selected_world', '', {
                expires: -1,
                path: '/'
            });
            dialogs.notification(data.Error, 'error');
        }
    );
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
        for (var key in block_names) {
            var block_name = block_names[key];
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

