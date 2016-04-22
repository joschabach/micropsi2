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

    agent_html = '';
    for (var key in data.agents) {
        agent_html += "<tr><td>"+data.agents[key].name+ ' ('+data.agents[key].type+')</td></tr>';
    }
    $('#world_agents_list table').html(agent_html);

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

    api.call('get_world_properties', {
        world_uid: currentWorld
    }, success = function (data) {
        refreshWorldView();
        $('#world').parent().html('<iframe src="http://blockworld.micropsi-industries.com/" id="world" width="100%" height="100%"></iframe>');
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