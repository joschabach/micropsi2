/*
 * Paperscript code, defines the rendering of the node net within its canvas
 *
 * Autor: joscha
 * Date: 03.05.2012
 */


// initialization ---------------------------------------------------------------------

var viewProperties = {
    zoomFactor: 0.8,
    frameWidth: 50,
    activeColor: new Color("#009900"),
    inhibitedColor: new Color("#ff0000"),
    selectionColor: new Color("#0099ff"),
    hoverColor: new Color("#089AC7"),
    linkColor: new Color("#000000"),
    nodeColor: new Color("#c2c2d6"),
    nodeForegroundColor: new Color ("#000000"),
    nodeFontColor: new Color ("#000000"),
    fontSize: 10,
    symbolSize: 14,
    nodeWidth: 84,
    compactNodeWidth: 32,
    cornerWidth: 6,
    padding: 5,
    slotWidth: 34,
    lineHeight: 15,
    compactNodes: false,
    outsideDummyDistance: 70,
    outsideDummySize: 15,
    outsideDummyColor: new Color("#cccccc"),
    groupOutsideLinksThreshold: 0,
    forceCompactBelowZoomFactor: 0.9,
    strokeWidth: 0.3,
    outlineWidth: 0.3,
    outlineWidthSelected: 2.0,
    highlightColor: new Color ("#ffffff"),
    shadowColor: new Color ("#000000"),
    shadowDisplacement: new Point(0.5,1.5),
    innerShadowDisplacement: new Point(0.2,0.7),
    linkTension: 50,
    arrowWidth: 6,
    arrowLength: 10,
    rasterize: true,
    yMax: 13500,
    xMax: 13500,
    copyPasteOffset: 50,
    snap_to_grid: false
};

var nodenetscope = paper;

var nodenet_loaded = false;

// hashes from uids to object definitions; we import these via json
nodes = {};
links = {};
selection = {};
gatefunctions = {};
monitors = {};

GATE_DEFAULTS = {
    "minimum": -1,
    "maximum": 1,
    "certainty": 1,
    "amplification": 1,
    "threshold": -1,
    "decay": 0,
    "rho": 0,
    "theta": 0
}

gridLayer = new Layer();
gridLayer.name = 'GridLayer';
linkLayer = new Layer();
linkLayer.name = 'LinkLayer';
nodeLayer = new Layer();
nodeLayer.name = 'NodeLayer';
prerenderLayer = new Layer();
prerenderLayer.name = 'PrerenderLayer';
prerenderLayer.visible = false;

viewProperties.zoomFactor = parseFloat($.cookie('zoom_factor')) || viewProperties.zoomFactor;

currentNodenet = $.cookie('selected_nodenet') || '';
currentNodeSpace = $.cookie('selected_nodespace') || '';

currentWorldadapter = null;
var rootNode = new Node("Root", 0, 0, 0, "Root", "Nodespace");

var currentSheaf = "default";

var selectionRectangle = new Rectangle(1,1,1,1);
selectionBox = new Path.Rectangle(selectionRectangle);
selectionBox.strokeWidth = 0.5;
selectionBox.strokeColor = 'black';
selectionBox.dashArray = [4,2];
selectionBox.name = "selectionBox";

nodetypes = {};
native_modules = {};
available_gatetypes = [];
nodespaces = {};
sorted_nodetypes = [];

initializeMenus();
initializeDialogs();
initializeControls();
initializeSidebarForms();

canvas_container = $('#nodenet').parent();
loaded_coordinates = {
    x: [0, canvas_container.width() * 2],
    y: [0, canvas_container.height() * 2]
};
max_coordinates = {};
canvas_container.on('scroll', refreshViewPortData);

var clipboard = {};

// hm. not really nice. but let's see if we got other pairs, or need them configurable:
var inverse_link_map = {'por':'ret', 'sub':'sur', 'cat':'exp'};
var inverse_link_targets = ['ret', 'sur', 'exp'];

if(currentNodenet){
    setCurrentNodenet(currentNodenet, currentNodeSpace);
} else {
    splash = new PointText(new Point(50, 50));
    splash.characterStyle = { fontSize: 20, fillColor: "#66666" };
    splash.content = 'Create a nodenet by selecting "New..." from the "Nodenet" menu.';
    nodeLayer.addChild(splash);
    toggleButtons(false);
}

worldadapters = {};
currentSimulationStep = 0;
nodenetRunning = false;

get_available_worlds();
refreshNodenetList();

registerResizeHandler();

globalDataSources = [];
globalDataTargets = [];

$(document).on('load_nodenet', function(event, uid){
    ns = 'Root';
    if(uid == currentNodenet){
        ns = currentNodeSpace;
    }
    setCurrentNodenet(uid, ns);
});

function toggleButtons(on){
    if(on)
        $('[data-nodenet-control]').removeAttr('disabled');
    else
        $('[data-nodenet-control]').attr('disabled', 'disabled');
}

function refreshNodenetList(){
    $("#nodenet_list").load("/nodenet_list/"+(currentNodenet || ''), function(data){
        $('#nodenet_list .nodenet_select').on('click', function(event){
            event.preventDefault();
            var el = $(event.target);
            var uid = el.attr('data');
            $(document).trigger('nodenet_changed', uid);
            setCurrentNodenet(uid, 'Root', true);
        });
    });
}
// make function available in global javascript scope
window.refreshNodenetList = function(){
    refreshNodenetList();
};

function get_available_worlds(){
    api.call('get_available_worlds', {}, success=function(data){
        var html = '<option value="">None</option>';
        for(var uid in data){
            html += '<option value="'+uid+'">'+data[uid].name+'</option>';
        }
        $('#nodenet_world').html(html);
    });
}

function get_available_worldadapters(world_uid, callback){
    worldadapters = {};
    if(world_uid){
        api.call("get_worldadapters", {world_uid: world_uid},
            success=function(data){
                worldadapters = data;
                currentWorld = world_uid;
                str = '';
                for (var name in worldadapters){
                    worldadapters[name].datasources = worldadapters[name].datasources.sort();
                    worldadapters[name].datatargets = worldadapters[name].datatargets.sort();
                    str += '<option>'+name+'</option>';
                }
                $('#nodenet_worldadapter').html(str);
                if(callback){
                    callback();
                }
        });
    } else {
        $('#nodenet_worldadapter').html('<option>&lt;No world selected&gt;</option>');
        if(callback){
            callback();
        }
    }
}

function setNodenetValues(data){
    $('#nodenet_world').val(data.world);
    $('#nodenet_uid').val(currentNodenet);
    $('#nodenet_name').val(data.name);
    $('#nodenet_snap').attr('checked', data.snap_to_grid);
    $('#nodenet_renderlinks').val(nodenet_data.settings['renderlinks']);
    if (!jQuery.isEmptyObject(worldadapters)) {
        var worldadapter_select = $('#nodenet_worldadapter');
        worldadapter_select.val(data.worldadapter);
        if(worldadapter_select.val() != data.worldadapter){
            dialogs.notification("The worldadapter of this nodenet is not compatible to the world. Please choose a worldadapter from the list", 'Error');
        }
    }
}

function setCurrentNodenet(uid, nodespace, changed){
    if(!nodespace){
        nodespace = "Root";
    }
    api.call('load_nodenet',
        {nodenet_uid: uid,
            nodespace: nodespace,
            coordinates: {
                x1: loaded_coordinates.x[0],
                x2: loaded_coordinates.x[1],
                y1: loaded_coordinates.y[0],
                y2: loaded_coordinates.y[1]
            }
        },
        function(data){
            nodenetscope.activate();
            toggleButtons(true);

            var nodenetChanged = changed || (uid != currentNodenet);
            var nodespaceChanged = changed || (nodespace != currentNodeSpace);

            if(nodenetChanged){
                $(document).trigger('nodenetChanged', uid);
                clipboard = {};
                selection = {};
            }

            nodenet_data = data;
            if(!nodenet_data.settings['renderlinks']){
                // default nodenet settings
                nodenet_data.settings['renderlinks'] = 'always';
            }
            nodenet_data['snap_to_grid'] = $.cookie('snap_to_grid') || viewProperties.snap_to_grid;

            showDefaultForm();
            currentNodeSpace = data['nodespace'];
            currentNodenet = uid;

            nodes = {};
            links = {};
            nodeLayer.removeChildren();
            addNode(rootNode);
            linkLayer.removeChildren();

            $.cookie('selected_nodenet', currentNodenet, { expires: 7, path: '/' });
            if(nodenetChanged || jQuery.isEmptyObject(nodetypes)){
                nodetypes = data.nodetypes;
                sorted_nodetypes = Object.keys(nodetypes);
                sorted_nodetypes.sort(function(a, b){
                    if(a < b) return -1;
                    if(a > b) return 1;
                    return 0;
                });
                native_modules = data.native_modules;
                for(var key in native_modules){
                    nodetypes[key] = native_modules[key];
                }
                available_gatetypes = [];
                for(var key in nodetypes){
                    $.merge(available_gatetypes, nodetypes[key].gatetypes || []);
                }
                available_gatetypes = $.unique(available_gatetypes);
                get_available_worldadapters(data.world, function(){
                    setNodenetValues(nodenet_data);
                    showDefaultForm();
                });
                setNodespaceData(data, true);
                getNodespaceList();
            } else {
                setNodespaceData(data, (nodespaceChanged));
            }
            refreshNodenetList();
            nodenet_loaded = true;
        },
        function(data) {
            if(data.status == 500 || data.status === 0){
                api.defaultErrorCallback(data);
            } else {
                currentNodenet = null;
                $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
                dialogs.notification(data.data, "Info");
            }
        });
}

function getNodespaceList(){
    api.call('get_nodespace_list', {nodenet_uid:currentNodenet}, function(nodespacedata){
        var sorted = Object.values(nodespacedata);
        sorted.sort(sortByName);
        html = '';
        for(var i=0; i < sorted.length; i++){
            nodespaces[sorted[i].uid] = sorted[i];
            html += '<li><a href="#" data-nodespace="'+sorted[i].uid+'">'+sorted[i].name+'</a></li>';
        }
        $('#nodespace_control ul').html(html);
        $("#current_nodespace_name").text(nodespaces[currentNodeSpace].name);
        updateNodespaceForm();
    });
}

// set visible nodes and links
function setNodespaceData(data, changed){
    nodenetscope.activate();
    if (data && !jQuery.isEmptyObject(data)){
        currentSimulationStep = data.current_step || 0;
        currentWorldadapter = data.worldadapter;
        nodenetRunning = data.is_active;

        if('max_coords' in data){
            max_coordinates = data['max_coords'];
        }
        if(!('selectionBox' in nodeLayer)){
            nodeLayer.addChild(selectionBox);
        }
        var uid;
        for(uid in nodes) {
            if(!(uid in data.nodes)){
                removeNode(nodes[uid]);
                if (uid in selection) delete selection[uid];
            }
        }
        for(uid in data.nodes){
            item = new Node(uid, data.nodes[uid]['position'][0], data.nodes[uid]['position'][1], data.nodes[uid].parent_nodespace, data.nodes[uid].name, data.nodes[uid].type, data.nodes[uid].sheaves, data.nodes[uid].state, data.nodes[uid].parameters, data.nodes[uid].gate_activations, data.nodes[uid].gate_parameters);
            if(uid in nodes){
                if(nodeRedrawNeeded(item)) {
                    nodes[uid].update(item);
                    redrawNode(nodes[uid], true);
                } else {
                    nodes[uid].update(item);
                }
            } else{
                addNode(item);
            }
        }
        for(uid in data.nodespaces){
            item = new Node(uid, data.nodespaces[uid]['position'][0], data.nodespaces[uid]['position'][1], data.nodespaces[uid].parent_nodespace, data.nodespaces[uid].name, "Nodespace", 0, data.nodespaces[uid].state);
            if(uid in nodes){
                redrawNode(item);
                nodes[uid].update(item);
            } else{
                addNode(item);
            }
        }
        var link, sourceId, targetId;
        var outsideLinks = [];

        for(var uid in links) {
            if(!(uid in data.links)) {
                removeLink(links[uid]);
            }
        }
        for(uid in data.links){
            sourceId = data.links[uid]['source_node_uid'];
            targetId = data.links[uid]['target_node_uid'];
            if (sourceId in nodes && targetId in nodes && nodes[sourceId].parent == nodes[targetId].parent){
                link = new Link(uid, sourceId, data.links[uid].source_gate_name, targetId, data.links[uid].target_slot_name, data.links[uid].weight, data.links[uid].certainty);
                if(uid in links){
                    redrawLink(link);
                } else {
                    addLink(link);
                }
            } else if(sourceId in nodes || targetId in nodes){
                link = new Link(uid, sourceId, data.links[uid].source_gate_name, targetId, data.links[uid].target_slot_name, data.links[uid].weight, data.links[uid].certainty);
                if(targetId in nodes && nodes[targetId].linksFromOutside.indexOf(link.uid) < 0)
                    nodes[targetId].linksFromOutside.push(link.uid);
                if(sourceId in nodes && nodes[sourceId].linksToOutside.indexOf(link.uid) < 0)
                    nodes[sourceId].linksToOutside.push(link.uid);
                outsideLinks.push(link);
            }
        }
        for(var index in outsideLinks){
            if(outsideLinks[index].uid in links){
                redrawLink(outsideLinks[index]);
            } else {
                addLink(outsideLinks[index]);
            }
        }
        updateModulators(data.modulators);

        if(data.monitors){
            monitors = data.monitors;
        }
        if(changed){
            updateNodespaceForm();
        }
        if(data.user_prompt){
            promptUser(data.user_prompt);
        }
    }
    drawGridLines(view.element);
    updateViewSize();
}

function get_nodenet_data(){
    return {
        'nodespace': currentNodeSpace,
        'step': currentSimulationStep - 1,
        'coordinates': {
            x1: loaded_coordinates.x[0],
            x2: loaded_coordinates.x[1],
            y1: loaded_coordinates.y[0],
            y2: loaded_coordinates.y[1]
        },
    }
}

register_stepping_function('nodenet', get_nodenet_data, setNodespaceData);

function refreshNodespace(nodespace, coordinates, step, callback){
    if(!nodespace) nodespace = currentNodeSpace;
    if(!currentNodenet || !nodespace){
        return;
    }
    if(coordinates)
        loaded_coordinates = coordinates;
    nodespace = nodespace || currentNodeSpace;
    params = {
        nodenet_uid: currentNodenet,
        nodespace: nodespace,
        step: currentSimulationStep
    };
    if (coordinates){
        // params.step = -1;
    } else {
        coordinates = loaded_coordinates;
    }
    if(step){
        params.step = step;
    }
    params.coordinates = {
        x1: parseInt(coordinates.x[0]),
        x2: parseInt(coordinates.x[1]),
        y1: parseInt(coordinates.y[0]),
        y2: parseInt(coordinates.y[1])
    };
    api.call('get_nodespace', params , success=function(data){
        var changed = nodespace != currentNodeSpace;
        if(changed){
            currentNodeSpace = nodespace;
            $.cookie('selected_nodespace', currentNodeSpace, { expires: 7, path: '/' });
            $("#current_nodespace_name").text(nodespaces[nodespace].name);
            nodeLayer.removeChildren();
            linkLayer.removeChildren();
        }
        loaded_coordinates = coordinates;
        nodenetRunning = data.is_active;

        if (linkCreationStart){
            renderLinkDuringCreation(clickPoint);
        }
        setNodespaceData(data, changed);

        if(callback){
            callback(data);
        }
    });
}


function refreshViewPortData(){
    var top = parseInt(canvas_container.scrollTop() / viewProperties.zoomFactor);
    var left = parseInt(canvas_container.scrollLeft() / viewProperties.zoomFactor);
    var width = parseInt(canvas_container.width() / viewProperties.zoomFactor);
    var height = parseInt(canvas_container.height() / viewProperties.zoomFactor);
    if(top + height > loaded_coordinates.y[1] ||
        left + width > loaded_coordinates.x[1] ||
        top < loaded_coordinates.y[0] ||
        left < loaded_coordinates.x[0]) {
        if(nodenet_loaded) refreshNodespace(currentNodeSpace, {
            x:[Math.max(0, left - width), left + 2*width],
            y:[Math.max(0, top-height), top + 2*height]
        }, currentSimulationStep - 1);
    }
}

function updateModulators(data){
    var table = $('table.modulators');
    html = '';
    var sorted = [];
    globalDataSources = [];
    globalDataTargets = [];

    for(key in data){
        sorted.push({'name': key, 'value': data[key]});
    }
    sorted.sort(sortByName);
    // display reversed to get emo_ before base_
    for(var i = sorted.length-1; i >=0; i--){
        html += '<tr><td>'+sorted[i].name+'</td><td>'+sorted[i].value.toFixed(2)+'</td><td><button class="btn btn-mini" data="'+sorted[i].name+'">monitor</button></td></tr>'
        if(sorted[i].name.substr(0, 3) == "emo"){
            globalDataSources.push(sorted[i].name);
        } else {
            globalDataTargets.push(sorted[i].name);
        }
    }
    table.html(html);
    $('button', table).each(function(idx, button){
        $(button).on('click', function(evt){
            evt.preventDefault();
            var mod = $(button).attr('data');
            api.call('add_modulator_monitor', {
                    nodenet_uid: currentNodenet,
                    modulator: mod,
                    name: mod
                }, function(data){
                    dialogs.notification('Monitor added', 'success');
                    $(document).trigger('monitorsChanged', data);
                }
            );
        });
    });
}

// data structures ----------------------------------------------------------------------


// data structure for net entities
function Node(uid, x, y, nodeSpaceUid, name, type, sheaves, state, parameters, gate_activations, gate_parameters) {
	this.uid = uid;
	this.x = x;
	this.y = y;
	this.sheaves = sheaves || {"default": {"uid": "default", "name": "default", "activation": 0}};
    this.state = state;
	this.name = name;
	this.type = type;
	this.symbol = "?";
	this.slots = {};
    this.gates = {};
    this.linksFromOutside = [];
    this.linksToOutside = [];
    this.placeholder = {};
    this.parent = nodeSpaceUid; // parent nodespace, default is root
    this.fillColor = null;
    this.parameters = parameters || {};
    this.bounds = null; // current bounding box (after scaling)
    this.slotIndexes = [];
    this.gateIndexes = [];
    this.gate_parameters = gate_parameters || {};
    this.gate_activations = gate_activations || {};
	if(type == "Nodespace") {
        this.symbol = "NS";
    } else {
        this.symbol = nodetypes[type].symbol || type.substr(0,1);
        var i;
        for(i in nodetypes[type].slottypes){
            this.slots[nodetypes[type].slottypes[i]] = new Slot(nodetypes[type].slottypes[i]);
        }
        for(i in nodetypes[type].gatetypes){
            parameters = {};
            sheaves = this.gate_activations[nodetypes[type].gatetypes[i]];
            if(!sheaves) {
                sheaves = {"default":{"uid":"default", "name":"default", "activation": 0}};
            }

            if(nodetypes[type].gate_defaults && nodetypes[type].gate_defaults[nodetypes[type].gatetypes[i]]) {
                parameters = nodetypes[type].gate_defaults[nodetypes[type].gatetypes[i]];
            } else {
                parameters = jQuery.extend({}, GATE_DEFAULTS);
            }
            for(var key in this.gate_parameters[nodetypes[type].gatetypes[i]]){
                parameters[key] = this.gate_parameters[nodetypes[type].gatetypes[i]][key];
            }
            this.gates[nodetypes[type].gatetypes[i]] = new Gate(nodetypes[type].gatetypes[i], i, sheaves, parameters);
        }
        this.slotIndexes = Object.keys(this.slots);
        this.gateIndexes = Object.keys(this.gates);
    }

    this.update = function(item){
        this.uid = item.uid;
        if(item.bounds) this.bounds = item.bounds;
        this.x = item.x;
        this.y = item.y;
        this.parent = item.parent;
        this.name = item.name;
        this.sheaves = item.sheaves;
        this.state = item.state;
        this.parameters = item.parameters;
        this.gate_parameters = item.gate_parameters;
        this.gate_activations = item.gate_activations;
        for(var i in nodetypes[type].gatetypes){
            this.gates[nodetypes[type].gatetypes[i]].parameters = this.gate_parameters[nodetypes[type].gatetypes[i]];
            this.gates[nodetypes[type].gatetypes[i]].sheaves = this.gate_activations[nodetypes[type].gatetypes[i]];
        }
    };

    this.gatechecksum = function(){
        var gatechecksum = "";
        for(var i in nodetypes[type].gatetypes){
            gatechecksum += "-" + this.gates[nodetypes[type].gatetypes[i]].sheaves[currentSheaf].activation;
        }
        return gatechecksum;
    };
}

// target for links, part of a net entity
function Slot(name) {
	this.name = name;
	this.incoming = {};
	this.sheaves = {"default": {"uid": "default", "name": "default", "activation": 0}};
}

// source for links, part of a net entity
function Gate(name, index, sheaves, parameters) {
	this.name = name;
    this.index = index;
	this.outgoing = {};
	this.sheaves = sheaves;
    if(parameters){
        this.parameters = parameters;
    } else {
        this.parameters = {
            "minimum": -1,
            "maximum": 1,
            "certainty": 1,
            "amplification": 1,
            "threshold": 0,
            "decay": 0
        };
    }
}

// link, connects two nodes, from a gate to a slot
function Link(uid, sourceNodeUid, gateName, targetNodeUid, slotName, weight, certainty){
    this.uid = uid;
    this.sourceNodeUid = sourceNodeUid;
    this.gateName = gateName;
    this.targetNodeUid = targetNodeUid;
    this.slotName = slotName;
    this.weight = weight;
    this.certainty = certainty;

    this.strokeColor = null;
    this.strokeWidth = null;
}

// data manipulation ----------------------------------------------------------------

// add or update link
function addLink(link) {
    // add link to source node and target node
    var sourceNode = nodes[link.sourceNodeUid] || {};
    var targetNode = nodes[link.targetNodeUid] || {};
    if (sourceNode.uid || targetNode.uid) {
        var gate,slot;
        if(sourceNode.uid && nodes[link.sourceNodeUid].gates[link.gateName]){
            nodes[link.sourceNodeUid].gates[link.gateName].outgoing[link.uid]=link;
            gate = true;
        }
        if(targetNode.uid && nodes[link.targetNodeUid].slots[link.slotName]){
            nodes[link.targetNodeUid].slots[link.slotName].incoming[link.uid]=link;
            slot = true;
        }
        if((sourceNode.uid && !gate) || (targetNode.uid && !slot)){
            console.error('Incompatible slots and gates');
            return;
        }
        // check if link is visible
        if (!(isOutsideNodespace(nodes[link.sourceNodeUid]) &&
            isOutsideNodespace(nodes[link.targetNodeUid]))) {
            renderLink(link);
        }
        links[link.uid] = link;
    } else {
        console.error("Error: Attempting to create link without establishing nodes first");
    }
}

function redrawLink(link, forceRedraw){
    var oldLink = links[link.uid];
    if (forceRedraw || !oldLink || !(link.uid in linkLayer.children) || oldLink.weight != link.weight ||
        oldLink.certainty != link.certainty ||
        nodes[oldLink.sourceNodeUid].gates[oldLink.gateName].sheaves[currentSheaf].activation !=
            nodes[link.sourceNodeUid].gates[link.gateName].sheaves[currentSheaf].activation) {
        if(link.uid in linkLayer.children){
            linkLayer.children[link.uid].remove();
        }
        renderLink(link);
        links[link.uid] = link;
    }
}

// delete a link from the array, and from the screen
function removeLink(link) {
    sourceNode = nodes[link.sourceNodeUid];
    targetNode = nodes[link.targetNodeUid];
    if(sourceNode.parent != targetNode.parent){
        sourceNode.linksToOutside.splice(sourceNode.linksToOutside.indexOf(link.uid), 1);
        targetNode.linksFromOutside.splice(targetNode.linksFromOutside.indexOf(link.uid), 1);
        redrawNodePlaceholder(sourceNode, 'out');
        redrawNodePlaceholder(targetNode, 'in');
    }
    delete links[link.uid];
    if (link.uid in linkLayer.children) linkLayer.children[link.uid].remove();
    delete sourceNode.gates[link.gateName].outgoing[link.uid];
    delete targetNode.slots[link.slotName].incoming[link.uid];
}

// add or update node, should usually be called from the JSON parser
function addNode(node) {
    // check if node already exists
    if (! (node.uid in nodes)) {
        if (node.parent == currentNodeSpace){
            renderNode(node);
        }
        nodes[node.uid] = node;
    } else {
        var oldNode = nodes[node.uid];

        // if node only updates position or activation, we may save some time
        // import all properties individually; check if we really need to redraw
    }
    view.viewSize.x = Math.max (view.viewSize.x, (node.x + viewProperties.frameWidth));
    view.viewSize.y = Math.max (view.viewSize.y, (node.y + viewProperties.frameWidth));
    return node;
}

// remove the node from hash, get rid of orphan links, and delete it from the screen
function removeNode(node) {
    var linkUid;
    for (var gateName in node.gates) {
        for (linkUid in node.gates[gateName].outgoing) {
            removeLink(links[linkUid]);
        }
    }
    for (var slotName in node.slots) {
        for (linkUid in node.slots[slotName].incoming) {
            removeLink(links[linkUid]);
        }
    }
    if (node.uid in nodeLayer.children) {
        nodeLayer.children[node.uid].remove();
    }
    delete nodes[node.uid];
}

// rendering ------------------------------------------------------------------------

// adapt the size of the current view to the contained nodes and the canvas size
updateViewSize = function() {
    var maxX = 0;
    var maxY = 0;
    var frameWidth = viewProperties.frameWidth*viewProperties.zoomFactor;
    var el = canvas_container;
    if(max_coordinates.x){
        prerenderLayer.removeChildren();
        maxX = (max_coordinates.x + 50) * viewProperties.zoomFactor;
        maxY = (max_coordinates.y + 200) * viewProperties.zoomFactor;
    } else {
        prerenderLayer.removeChildren();
        for (var nodeUid in nodeLayer.children) {
            if (nodeUid in nodes) {
                var node = nodes[nodeUid];
                // make sure no node gets lost to the top or left
                if (node.x < frameWidth || node.y < frameWidth) {
                    node.x = Math.max(node.x, viewProperties.frameWidth);
                    node.y = Math.max(node.y, viewProperties.frameWidth);
                    redrawNode(node);
                }
                maxX = Math.max(maxX, node.x);
                maxY = Math.max(maxY, node.y);
            }
        }
    }
    var newSize = new Size(
        Math.min(viewProperties.xMax, Math.max((maxX+viewProperties.frameWidth),
        el.width())),
        Math.min(viewProperties.yMax, Math.max(el.height(), maxY)));
    if(newSize.height && newSize.width){
        view.viewSize = newSize;
    }
    view.draw(true);
    for(var uid in nodes){
        redrawNode(nodes[uid]);
    }
};

// complete redraw of the current node space
function redrawNodeNet() {
    nodeLayer.removeChildren();
    nodeLayer.addChild(selectionBox);
    linkLayer.removeChildren();
    var i;
    for (i in nodes) {
        if (!isOutsideNodespace(nodes[i])) renderNode(nodes[i]);
    }
    for (i in links) {
        var sourceNode = nodes[links[i].sourceNodeUid];
        var targetNode = nodes[links[i].targetNodeUid];
        // check if the link is visible
        if (!(isOutsideNodespace(sourceNode) && isOutsideNodespace(targetNode))) {
            renderLink(links[i]);
        }
    }
    drawGridLines(view.element);
    updateViewSize();
}

// like activation change, only put the node elsewhere and redraw the links
function redrawNode(node, forceRedraw) {
    if(nodeRedrawNeeded(node) || forceRedraw){
        if(node.uid in nodeLayer.children){
            nodeLayer.children[node.uid].remove();
        }
        if(node.parent == currentNodeSpace){
            renderNode(node);
            redrawNodeLinks(node);
        }
    } else {
        if(node.parent != currentNodeSpace){
            nodeLayer.children[node.uid].remove();
        }
    }
}

function nodeRedrawNeeded(node){
    if(node.uid in nodeLayer.children){
        if(node.x == nodes[node.uid].x &&
            node.y == nodes[node.uid].y &&
            node.sheaves[currentSheaf].activation == nodes[node.uid].sheaves[currentSheaf].activation &&
            node.gatechecksum() == nodes[node.uid].gatechecksum() &&
            Object.keys(node.sheaves).length == Object.keys(nodes[node.uid].sheaves).length &&
            viewProperties.zoomFactor == nodes[node.uid].zoomFactor){
            return false;
        }
    }
    return true;
}

// redraw only the links that are connected to the given node
function redrawNodeLinks(node) {
    var linkUid;
    for(var dir in  node.placeholder){
        node.placeholder[dir].remove();
    }
    for (var gateName in node.gates) {
        for (linkUid in node.gates[gateName].outgoing) {
            if(linkUid in linkLayer.children) {
                linkLayer.children[linkUid].remove();
            }
            renderLink(links[linkUid]);
        }
    }
    for (var slotName in node.slots) {
        for (linkUid in node.slots[slotName].incoming) {
            if(linkUid in linkLayer.children) {
                linkLayer.children[linkUid].remove();
            }
            renderLink(links[linkUid]);
        }
    }
}

sourceBounds = {};
// determine the point where link leaves the node
function calculateLinkStart(sourceNode, targetNode, gateName) {
    var startPointIsPreliminary = false;
    // Depending on whether the node is drawn in compact or full shape, links may originate at odd positions.
    // This depends on the node type and the link type.
    // If a link does not have a preferred direction on a compact node, it will point directly from the source
    // node to the target node. However, this requires to know both points, so there must be a preliminary step.
    if(!isOutsideNodespace(sourceNode)){
        sourceBounds = sourceNode.bounds;
    } else {
        if(targetNode && targetNode.linksFromOutside.length > viewProperties.groupOutsideLinksThreshold){
            redrawNodePlaceholder(targetNode, 'in');
            sourceBounds = targetNode.placeholder['in'].bounds;
        }
    }
    var sourcePoints, startPoint, startAngle;
    if (!isOutsideNodespace(sourceNode) && isCompact(sourceNode)) {
        if (sourceNode.type=="Sensor" || sourceNode.type == "Actor") {
            if (sourceNode.type == "Sensor")
                startPoint = new Point(sourceBounds.x+sourceBounds.width*0.5,
                    sourceBounds.y);
            else
                startPoint = new Point(sourceBounds.x+sourceBounds.width*0.4,
                    sourceBounds.y);
            startAngle = 270;
        } else {
            switch (gateName){
                case "por":
                    startPoint = new Point(sourceBounds.x + sourceBounds.width,
                        sourceBounds.y + sourceBounds.height*0.4);
                    startAngle = 0;
                    break;
                case "ret":
                    startPoint = new Point(sourceBounds.x,
                        sourceBounds.y + sourceBounds.height*0.6);
                    startAngle = 180;
                    break;
                case "sub":
                    startPoint = new Point(sourceBounds.x + sourceBounds.width*0.6,
                        sourceBounds.y+ sourceBounds.height);
                    startAngle = 90;
                    break;
                case "sur":
                    startPoint = new Point(sourceBounds.x + sourceBounds.width*0.4,
                        sourceBounds.y);
                    startAngle = 270;
                    break;
                default:
                    startPoint = new Point(sourceBounds.x + sourceBounds.width*0.5,
                        sourceBounds.y + sourceBounds.height*0.5);
                    startPointIsPreliminary = true;
            }
        }
    } else {
        if(isOutsideNodespace(sourceNode)){
            startPoint = new Point(sourceBounds.x + viewProperties.outsideDummySize,
                sourceBounds.y+viewProperties.outsideDummySize/2);
        } else {
            var index = sourceNode.gateIndexes.indexOf(gateName);
            startPoint = new Point(sourceBounds.x+sourceBounds.width,
                sourceBounds.y+viewProperties.lineHeight*(index+2.5)*viewProperties.zoomFactor);
        }
        startAngle = 0;
    }
    return {
        "point": startPoint,
        "angle": startAngle,
        "isPreliminary": startPointIsPreliminary
    };
}

// determine the point where a link enters the node
function calculateLinkEnd(sourceNode, targetNode, slotName, linkType) {
    var endPointIsPreliminary = false;
    var endPoint, endAngle;
    var targetBounds;
    if(!isOutsideNodespace(targetNode)){
        targetBounds = targetNode.bounds;
    } else {
        if(sourceNode && sourceNode.linksToOutside.length > viewProperties.groupOutsideLinksThreshold){
            redrawNodePlaceholder(sourceNode, 'out');
            targetBounds = sourceNode.placeholder['out'].bounds;
        }
    }
    if (!isOutsideNodespace(targetNode) && isCompact(targetNode)) {
        if (targetNode.type=="Sensor" || targetNode.type == "Actor") {
            endPoint = new Point(targetBounds.x + targetBounds.width*0.6, targetBounds.y);
            endAngle = 270;
        } else {
            switch (linkType){
                case "por":
                    endPoint = new Point(targetBounds.x,
                        targetBounds.y + targetBounds.height*0.4);
                    endAngle = 180;
                    break;
                case "ret":
                    endPoint = new Point(targetBounds.x + targetBounds.width,
                        targetBounds.y + targetBounds.height*0.6);
                    endAngle = 0;
                    break;
                case "sub":
                    endPoint = new Point(targetBounds.x + targetBounds.width*0.6,
                        targetBounds.y);
                    endAngle = 270;
                    break;
                case "sur":
                    endPoint = new Point(targetBounds.x + targetBounds.width*0.4,
                        targetBounds.y + targetBounds.height);
                    endAngle = 90;
                    break;
                default:
                    endPoint = new Point(targetBounds.x + targetBounds.width*0.5,
                        targetBounds.y + targetBounds.height*0.5);
                    endPointIsPreliminary = true;
                    break;
            }
        }
    } else {
        if(isOutsideNodespace(targetNode)){
            endPoint = new Point(targetBounds.x,
                targetBounds.y+viewProperties.outsideDummySize/2);
        } else {
            var index = targetNode.slotIndexes.indexOf(slotName);
            endPoint = new Point(targetBounds.x,
                targetBounds.y+viewProperties.lineHeight*(index+2.5)*viewProperties.zoomFactor);
        }
        endAngle = 180;
    }
    return {
        "point": endPoint,
        "angle": endAngle,
        "isPreliminary": endPointIsPreliminary
    };
}

function redrawNodePlaceholder(node, direction){
    if(node.placeholder[direction]){
        node.placeholder[direction].remove();
    }
    if(node.bounds && (node.parent == currentNodeSpace && (direction == 'in' && node.linksFromOutside.length > 0) || (direction == 'out' && node.linksToOutside.length > 0))){
        node.placeholder[direction] = createPlaceholder(node, direction, calculatePlaceHolderPosition(node, direction, 0));
        linkLayer.addChild(node.placeholder[direction]);
    }
}

function calculatePlaceHolderPosition(node, direction, index){
    var point;
    if(direction == 'in'){
        point = new Point(node.bounds.x - viewProperties.outsideDummyDistance * viewProperties.zoomFactor,
            node.bounds.y + ((index*2 + 1) * viewProperties.outsideDummySize * viewProperties.zoomFactor));
    } else if(direction == 'out') {
        point = new Point(node.bounds.x + node.bounds.width + viewProperties.outsideDummyDistance * viewProperties.zoomFactor,
            node.bounds.y + ((index*2 + 1) * viewProperties.outsideDummySize * viewProperties.zoomFactor));
    } else {
        console.warn('unknown direction for placeholder: '+direction);
    }
    return point;
}

function createPlaceholder(node, direction, point){
    var count;
    if(direction == 'in'){
        count = node.linksFromOutside.length;
    } else if(direction == 'out') {
        count = node.linksToOutside.length;
    } else {
        console.warn('unknown direction for placeholder: '+direction);
    }
    var shape = new Path.Circle(point, viewProperties.outsideDummySize/2 * viewProperties.zoomFactor);
    shape.fillColor = viewProperties.outsideDummyColor;
    if(count > viewProperties.groupOutsideLinksThreshold){
        point.y += 3;
        var labelText = new PointText(new Point(point));
        labelText.content = count;
        labelText.characterStyle = {
            fontSize: viewProperties.fontSize * viewProperties.zoomFactor,
            fillColor: viewProperties.nodeFontColor
        };
        labelText.paragraphStyle.justification = 'center';
        shape = new Group([shape, labelText]);
    }
    return shape;
}

// draw link
function renderLink(link, force) {
    if(nodenet_data.settings.renderlinks == 'no' && !force){
        return;
    }
    if(nodenet_data.settings.renderlinks == 'hover' && !force){
        if(!hoverNode || (link.sourceNodeUid != hoverNode.uid && link.targetNodeUid != hoverNode.uid)){
            return;
        }
    }
    var sourceNode = nodes[link.sourceNodeUid];
    var targetNode = nodes[link.targetNodeUid];

    var linkStart = calculateLinkStart(sourceNode, targetNode, link.gateName);
    var linkEnd = calculateLinkEnd(sourceNode, targetNode, link.slotName, link.gateName);

    var correctionVector;
    if (linkStart.isPreliminary) { // start from boundary of a compact node
        correctionVector = new Point(sourceBounds.width/2, 0);
        linkStart.angle = (linkEnd.point - linkStart.point).angle;
        linkStart.point += correctionVector.rotate(linkStart.angle-10);
    }
    if (linkEnd.isPreliminary) { // end at boundary of a compact node
        correctionVector = new Point(sourceBounds.width/2, 0);
        linkEnd.angle = (linkStart.point-linkEnd.point).angle;
        linkEnd.point += correctionVector.rotate(linkEnd.angle+10);
    }

    link.strokeWidth = Math.max(0.1, Math.min(1.0, Math.abs(link.weight)))*viewProperties.zoomFactor;
    if(sourceNode){
        link.strokeColor = activationColor(sourceNode.gates[link.gateName].sheaves[currentSheaf].activation * link.weight, viewProperties.linkColor);
    } else {
        link.strokeColor = viewProperties.linkColor;
    }

    var startDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkStart.angle);
    var endDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkEnd.angle);

    var arrowPath = createArrow(linkEnd.point, endDirection.angle, link.strokeColor);
    var linkPath = createLink(linkStart.point, linkStart.angle, startDirection, linkEnd.point, linkEnd.angle, endDirection, link.strokeColor, link.strokeWidth, link.gatename);

    var linkItem = new Group([linkPath, arrowPath]);
    linkItem.name = "link";
    var linkContainer = new Group(linkItem);
    linkContainer.name = link.uid;

    linkLayer.addChild(linkContainer);
}

// draw the line part of the link
function createLink(startPoint, startAngle, startDirection, endPoint, endAngle, endDirection, linkColor, linkWidth, linkType) {
    var arrowEntry = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(endAngle)+endPoint;
    var nodeExit = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(startAngle)+startPoint;

    var linkPath = new Path([[startPoint],[nodeExit,new Point(0,0),startDirection],[arrowEntry,endDirection]]);
    linkPath.strokeColor = linkColor;
    linkPath.strokeWidth = viewProperties.zoomFactor * linkWidth;
    linkPath.name = "line";

    if (linkType=="cat" || linkType == "exp") linkPath.dashArray = [4*viewProperties.zoomFactor,
        3*viewProperties.zoomFactor];
    return linkPath;
}

// draw the arrow head of the link
function createArrow(endPoint, endAngle, arrowColor) {
    var arrowPath = new Path(endPoint);
    arrowPath.lineBy(new Point(viewProperties.arrowLength, viewProperties.arrowWidth/2));
    arrowPath.lineBy(new Point(0, -viewProperties.arrowWidth));
    arrowPath.closePath();
    arrowPath.scale(viewProperties.zoomFactor, endPoint);
    arrowPath.rotate(endAngle, endPoint);
    arrowPath.fillColor = arrowColor;
    arrowPath.name = "arrow";
    return arrowPath;
}

var templinks = [];

// draw link during creation
function renderLinkDuringCreation(endPoint) {
    if(templinks){
        $.each(templinks, function(idx, link){
            link.remove();
        });
    }
    for(var i=0; i < linkCreationStart.length; i++){
        var sourceNode = linkCreationStart[i].sourceNode;
        var gateIndex = linkCreationStart[i].gateIndex;

        var linkStart = calculateLinkStart(sourceNode, null, sourceNode.gateIndexes[gateIndex]);

        var correctionVector;
        if (linkStart.isPreliminary) { // start from boundary of a compact node
            correctionVector = new Point(sourceBounds.width/2, 0);
            linkStart.angle = (endPoint - linkStart.point).angle;
            linkStart.point += correctionVector.rotate(linkStart.angle-10);
        }

        var startDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkStart.angle);
        var endDirection = new Point(-viewProperties.linkTension*viewProperties.zoomFactor,0);

        var arrowPath = createArrow(endPoint, 180, viewProperties.selectionColor);
        var linkPath = createLink(linkStart.point, linkStart.angle, startDirection, endPoint, 180, endDirection,
            viewProperties.selectionColor, 2*viewProperties.zoomFactor);

        var tempLink = new Group([linkPath, arrowPath]);
        tempLink.name = "tempLink";

        nodeLayer.addChild(tempLink);
        templinks.push(tempLink);
    }
}

// draw net entity
function renderNode(node) {
    if (isCompact(node)){
        renderCompactNode(node);
    } else {
        renderFullNode(node);
    }
    setActivation(node);
    if(node.uid in selection){
        selectNode(node.uid);
    }
    node.zoomFactor = viewProperties.zoomFactor;
}

// draw net entity with slots and gates
function renderFullNode(node) {
    node.bounds = calculateNodeBounds(node);
    var nodeItem;
    if(node.type == 'Comment'){
        nodeItem = renderComment(node);
    } else {
        var skeleton = createFullNodeSkeleton(node);
        var activations = createFullNodeActivations(node);
        var titleBar = createFullNodeLabel(node);
        var sheavesAnnotation = createSheavesAnnotation(node);
        nodeItem = new Group([activations, skeleton, titleBar, sheavesAnnotation]);
    }
    nodeItem.name = node.uid;
    nodeItem.isCompact = false;
    nodeLayer.addChild(nodeItem);
}

function renderComment(node){
    var bounds = node.bounds;
    var commentGroup = new Group();
    commentText = new PointText(bounds.x + 10, bounds.y + viewProperties.lineHeight * viewProperties.zoomFactor);
    commentText.content = node.parameters.comment;
    commentText.name = "comment";
    commentText.fillColor = viewProperties.nodeFontColor;
    commentText.fontSize = viewProperties.fontSize * viewProperties.zoomFactor;
    commentText.paragraphStyle.justification = 'left';
    bounds.width = Math.max(commentText.bounds.width, bounds.width);
    bounds.height = Math.max(commentText.bounds.height, bounds.height);
    var commentBox = new Path.Rectangle(bounds.x, bounds.y, bounds.width+20, bounds.height+20);
    commentBox.fillColor = new Color('yellow');
    node.bounds = commentBox.bounds;
    var boxgroup = new Group([commentBox]);
    boxgroup.name = 'body';
    commentGroup.addChild(boxgroup);
    commentGroup.addChild(commentText);
    return commentGroup;
}

// render compact version of a net entity
function renderCompactNode(node) {
    node.bounds = calculateNodeBounds(node);
    var nodeItem;
    if(node.type == "Comment"){
        nodeItem = renderComment(node);
    } else {
        var skeleton = createCompactNodeSkeleton(node);
        var activations = createCompactNodeActivations(node);
        var label = createCompactNodeLabel(node);
        nodeItem = new Group([activations, skeleton]);
        if (label){
            nodeItem.addChild(label);
        }
    }
    nodeItem.name = node.uid;
    nodeItem.isCompact = true;
    nodeLayer.addChild(nodeItem);
}

// calculate the dimensions of a node in the current rendering
function calculateNodeBounds(node) {
    var width, height;
    if(node.type == 'Comment'){
        return new Rectangle(
            node.x * viewProperties.zoomFactor,
            node.y * viewProperties.zoomFactor,
            viewProperties.nodeWidth * viewProperties.zoomFactor,
            viewProperties.lineHeight * viewProperties.zoomFactor);
    }
    if (!isCompact(node)) {
        width = viewProperties.nodeWidth * viewProperties.zoomFactor;
        height = viewProperties.lineHeight*(Math.max(node.slotIndexes.length, node.gateIndexes.length)+2)*viewProperties.zoomFactor;
        if (node.type == "Nodespace"){
            height = Math.max(height, viewProperties.lineHeight*4*viewProperties.zoomFactor);
        }
    } else {
        width = height = viewProperties.compactNodeWidth * viewProperties.zoomFactor;
    }
    return new Rectangle(node.x*viewProperties.zoomFactor - width/2,
        node.y*viewProperties.zoomFactor - height/2, // center node on origin
        width, height);
}

// determine shape of a full node
function createFullNodeShape(node) {
    if (node.type == "Nodespace" || node.type == "Comment"){
        return new Path.Rectangle(node.bounds);
    } else {
        return new Path.RoundRectangle(node.bounds, viewProperties.cornerWidth*viewProperties.zoomFactor);
    }
}

// determine shape of a compact node
function createCompactNodeShape(node) {
    var bounds = node.bounds;
    var shape;
    switch (node.type) {
        case "Nodespace":
        case "Comment":
            shape = new Path.Rectangle(bounds);
            break;
        case "Sensor":
            shape = new Path();
            shape.add(bounds.bottomLeft);
            shape.cubicCurveTo(new Point(bounds.x, bounds.y-bounds.height * 0.3),
                new Point(bounds.right, bounds.y-bounds.height * 0.3), bounds.bottomRight);
            shape.closePath();
            break;
        case "Actor":
            shape = new Path([bounds.bottomRight,
                new Point(bounds.x+bounds.width * 0.65, bounds.y),
                new Point(bounds.x+bounds.width * 0.35, bounds.y),
                bounds.bottomLeft
            ]);
            shape.closePath();
            break;
        case "Trigger":
            shape = new Path()
            shape.add(bounds.bottomLeft)
            shape.add(new Point(bounds.x+bounds.width * 0.10, bounds.y))
            shape.add(new Point(bounds.x+bounds.width * 0.40, bounds.y))
            shape.add(new Point(bounds.x+bounds.width * 0.50, bounds.y + bounds.height * 0.25))
            shape.cubicCurveTo(new Point(bounds.x + bounds.width * 0.65, bounds.y-bounds.height * 0.2), new Point(bounds.right, bounds.y-bounds.height * 0.2), bounds.bottomRight);
            shape.closePath();
            break;
        case "Concept": // draw circle
        case "Pipe": // draw circle
        case "Script": // draw circle
        case "Register":
            shape = new Path.Circle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
            break;
        default:
            if (nodetypes[node.type] && nodetypes[node.type].shape){
                shape = nodetypes[node.type].shape;
            }
            if(shape == "Circle"){
                shape = new Path.Circle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
            } else {
                if(['Circle', 'Rectangle', 'RoundRectangle'].indexOf(shape) < 0){
                    shape = 'RoundRectangle';
                }
                shape = new Path[shape](bounds, viewProperties.cornerWidth*viewProperties.zoomFactor);
            }
    }
    return shape;
}

// draw title bar label of a full node
function createFullNodeLabel(node) {
    var bounds = node.bounds;
    var label = new Group();
    label.name = "titleBarLabel";
    // clipping rectangle, so text does not flow out of the node
    var clipper = new Path.Rectangle (bounds.x+viewProperties.padding*viewProperties.zoomFactor,
        bounds.y,
        bounds.width-2*viewProperties.padding*viewProperties.zoomFactor,
        viewProperties.lineHeight*viewProperties.zoomFactor);
    clipper.clipMask = true;
    label.addChild(clipper);
    var titleText = new PointText(new Point(bounds.x+viewProperties.padding*viewProperties.zoomFactor,
        bounds.y+viewProperties.lineHeight*0.8*viewProperties.zoomFactor));
    titleText.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize*viewProperties.zoomFactor
    };
    titleText.content = (node.name ? node.name : node.uid);
    titleText.name = "text";
    label.addChild(titleText);
    return label;
}

// draw the sheaves annotation of a full node -- this is rather hacky, we will want to find
// a better way of visualizing sheaves, including sheaf states
function createSheavesAnnotation(node) {
    var bounds = node.bounds;
    var label = new Group();
    label.name = "sheavesLabel";
    var titleText = new PointText(new Point(bounds.x+ 80*viewProperties.zoomFactor +viewProperties.padding*viewProperties.zoomFactor,
        bounds.y+viewProperties.lineHeight*0.8*viewProperties.zoomFactor));
    titleText.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize*viewProperties.zoomFactor
    };
    var sheavesText = "";
    for(uid in node.sheaves) {
        name = node.sheaves[uid].name;
        if(name != "default") {
            sheavesText += name + "\n";
        }
    }
    titleText.content = sheavesText;
    titleText.name = "text";
    label.addChild(titleText);
    return label;
}

// draw a line below the title bar
function createNodeTitleBarDelimiter (node) {
    var bounds = node.bounds;
    var upper = new Path.Rectangle(bounds.x+viewProperties.shadowDisplacement.x*viewProperties.zoomFactor,
        bounds.y + (viewProperties.lineHeight - viewProperties.strokeWidth)*viewProperties.zoomFactor,
        bounds.width - viewProperties.shadowDisplacement.x*viewProperties.zoomFactor,
        viewProperties.innerShadowDisplacement.y*viewProperties.zoomFactor);
    upper.fillColor = viewProperties.shadowColor;
    upper.fillColor.alpha = 0.3;
    var lower = upper.clone();
    lower.position += new Point(0, viewProperties.innerShadowDisplacement.y*viewProperties.zoomFactor);
    lower.fillColor = viewProperties.highlightColor;
    lower.fillColor.alpha = 0.3;
    titleBarDelimiter = new Group([upper, lower]);
    titleBarDelimiter.name = "titleBarDelimiter";
    return titleBarDelimiter;
}

// turn shape into shadowed outline
function createBorder(shape, displacement) {

    var highlight = shape.clone(false);
    highlight.fillColor = viewProperties.highlightColor;
    var highlightSubtract = highlight.clone(false);
    highlightSubtract.position += displacement;
    var highlightClipper = highlight.clone(false);
    highlightClipper.position -= new Point(0.5, 0.5);
    highlightClipper.clipMask = true;
    var upper = new Group([highlightClipper, highlight, highlightSubtract]);
    upper.opacity = 0.5;

    var shadowSubtract = shape;
    shadowSubtract.fillColor = viewProperties.shadowColor;
    var shadow = shadowSubtract.clone(false);
    shadow.position += displacement;
    var shadowClipper = shadow.clone(false);
    shadowClipper.position += new Point(0.5, 0.5);
    shadowClipper.clipMask = true;
    var lower = new Group([shadowClipper,shadow, shadowSubtract]);
    lower.opacity = 0.5;

    var border = new Group([lower, upper]);
    border.setName("border");
    return border;
}

// full node body text
function createFullNodeBodyLabel(node) {
    var bounds = node.bounds;
    var label = new Group();
    label.name = "bodyLabel";
    // clipping rectangle, so text does not flow out of the node
    var clipper = new Path.Rectangle (bounds.x+viewProperties.padding*viewProperties.zoomFactor, bounds.y,
        bounds.width-2*viewProperties.padding*viewProperties.zoomFactor, bounds.height);
    clipper.clipMask = true;
    label.addChild(clipper);
    var typeText = new PointText(new Point(bounds.x+bounds.width/2,
        bounds.y+viewProperties.lineHeight*1.8*viewProperties.zoomFactor));
    typeText.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize*viewProperties.zoomFactor
    };
    typeText.paragraphStyle.justification = 'center';
    typeText.content = node.type;
    label.addChild(typeText);
    return label;
}

// render the static part of a node
function createFullNodeSkeleton(node) {
    var skeleton;
    if (!(node.type in prerenderLayer.children)) {
        var shape = createFullNodeShape(node);
        var border = createBorder(shape, viewProperties.shadowDisplacement*viewProperties.zoomFactor);
        var typeLabel = createFullNodeBodyLabel(node);
        var titleBarDelimiter = createNodeTitleBarDelimiter(node);
        skeleton = new Group([border, titleBarDelimiter, typeLabel]);
        if (node.slots) {
            for (i = 0; i< node.slotIndexes.length; i++)
                skeleton.addChild(createPillsWithLabels(getSlotBounds(node, i), node.slotIndexes[i]));
        }
        if (node.gates) {
            for (i = 0; i< node.gateIndexes.length; i++)
                skeleton.addChild(createPillsWithLabels(getGateBounds(node, i), node.gateIndexes[i]));
        }
        if (viewProperties.rasterize) skeleton = skeleton.rasterize();
        skeleton.name = node.type;
        prerenderLayer.addChild(skeleton);
    }
    skeleton = prerenderLayer.children[node.type].clone(false);
    skeleton.position = node.bounds.center;
    return skeleton;
}

// render the activation part of a node
function createFullNodeActivations(node) {
    var name = "fullNodeActivation "+node.type;
    var activation;
    if (!(name in prerenderLayer.children)) {
        var body = createFullNodeShape(node);
        body.name = "body";
        body.fillColor = viewProperties.nodeColor;
        activation = new Group([body]);
        activation.name = "activation";
        var bounds, i;
        if (node.slotIndexes.length) {
            var slots = new Group();
            slots.name = "slots";
            for (i = 0; i< node.slotIndexes.length; i++) {
                bounds = getSlotBounds(node, i);
                slots.addChild(new Path.RoundRectangle(bounds, bounds.height/2));
            }
            activation.addChild(slots);
        }
        if (node.gateIndexes.length) {
            var gates = new Group();
            gates.name = "gates";
            for (i = 0; i< node.gateIndexes.length; i++) {
                bounds = getGateBounds(node, i);
                gates.addChild(new Path.RoundRectangle(bounds, bounds.height/2));
            }
            activation.addChild(gates);
        }
        var container = new Group([activation]);
        container.name = name;
        prerenderLayer.addChild(container);
    }
    activation = prerenderLayer.children[name].firstChild.clone(false);
    activation.position = node.bounds.center;
    return activation;
}

// render the static part of a compact node
function createCompactNodeSkeleton(node) {
    var shape = createCompactNodeShape(node);
    var border = createBorder(shape, viewProperties.shadowDisplacement*viewProperties.zoomFactor);
    var typeLabel = createCompactNodeBodyLabel(node);
    var skeleton = new Group([border, typeLabel]);
    return skeleton;
}

// render the symbol within the compact node body
function createCompactNodeBodyLabel(node) {
    var bounds = node.bounds;
    var symbolText = new PointText(new Point(bounds.x+bounds.width/2,
        bounds.y+bounds.height/2+viewProperties.symbolSize/2*viewProperties.zoomFactor));
    symbolText.fillColor = viewProperties.nodeForegroundColor;
    symbolText.content = node.symbol;
    symbolText.fontSize = viewProperties.symbolSize*viewProperties.zoomFactor;
    symbolText.paragraphStyle.justification = 'center';
    return symbolText;
}

// render the activation part of a compact node
function createCompactNodeActivations(node) {
    var body = createCompactNodeShape(node);
    body.fillColor = viewProperties.nodeColor;
    body.name = "body";
    var activation = new Group([body]);
    activation.name = "activation";
    return activation;
}

// create the border of slots and gates, and add the respective label
function createPillsWithLabels(bounds, labeltext) {
    var border;
    if (!("pillshape" in prerenderLayer.children)) {
        var shape = Path.RoundRectangle(bounds, bounds.height/2);
        border = createBorder(shape, viewProperties.innerShadowDisplacement);
        if (viewProperties.rasterize) border = border.rasterize();
        border.name = "pillshape";
        prerenderLayer.addChild(border);
    }
    border = prerenderLayer.children["pillshape"].clone(false);
    border.position = bounds.center;
    var label = new Group();
    // clipping rectangle, so text does not flow out of the node
    var clipper = new Path.Rectangle(bounds);
    clipper.clipMask = true;
    label.addChild(clipper);
    var text = new PointText(bounds.center+new Point(0, viewProperties.lineHeight *0.1));
    text.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize*viewProperties.zoomFactor
    };
    text.paragraphStyle.justification = 'center';
    text.content = labeltext;
    label.addChild(text);
    return new Group([border, label]);
}

// draw the label of a compact node
function createCompactNodeLabel(node) {
    if (node.name.length) { // only display a label for named nodes
        var labelText = new PointText(new Point(node.bounds.x + node.bounds.width/2,
            node.bounds.bottom+viewProperties.lineHeight));
        labelText.content = node.name ? node.name : node.uid;
        labelText.characterStyle = {
            fontSize: viewProperties.fontSize,
            fillColor: viewProperties.nodeForegroundColor
        };
        labelText.paragraphStyle.justification = 'center';
        labelText.name = "labelText";
        return labelText;
    }
    return null;
}

// update activation in node background, slots and gates
function setActivation(node) {
    if(node.type == 'Comment'){
        return;
    }
    if (node.uid in nodeLayer.children) {
        var nodeItem = nodeLayer.children[node.uid];
        node.fillColor = nodeItem.children["activation"].children["body"].fillColor =
            activationColor(node.sheaves[currentSheaf].activation, viewProperties.nodeColor);
        if (!isCompact(node) && (node.slotIndexes.length || node.gateIndexes.length)) {
            var i=0;
            var type;
            for (type in node.slots) {
                nodeItem.children["activation"].children["slots"].children[i++].fillColor =
                    activationColor(node.slots[type].sheaves[currentSheaf].activation,
                    viewProperties.nodeColor);
            }
            i=0;
            for (type in node.gates) {
                nodeItem.children["activation"].children["gates"].children[i++].fillColor =
                    activationColor(node.gates[type].sheaves[currentSheaf].activation,
                    viewProperties.nodeColor);
            }
        }
    } else console.warn ("node "+node.uid+" not found in current view");
}

// mark node as selected, and add it to the selected nodes
function selectNode(nodeUid) {
    if(!(nodeUid in nodes)) return;
    selection[nodeUid] = nodes[nodeUid];
    var outline;
    if(nodes[nodeUid].type == 'Comment'){
        outline = nodeLayer.children[nodeUid].children["body"];
    } else {
        outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
    }
    outline.strokeColor = viewProperties.selectionColor;
    outline.strokeWidth = viewProperties.outlineWidthSelected*viewProperties.zoomFactor;
}

// remove selection marking of node, and remove if from the set of selected nodes
function deselectNode(nodeUid) {
    if (nodeUid in selection) {
        delete selection[nodeUid];
        if(nodeUid in nodeLayer.children){
            var outline;
            if(nodes[nodeUid].type == 'Comment'){
                outline = nodeLayer.children[nodeUid].children["body"];
            } else {
                outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
            }
            outline.strokeColor = null;
            outline.strokeWidth = viewProperties.outlineWidth;
        }
    }
}

function deselectOtherNodes(nodeUid){
    for(var key in selection){
        if(key != nodeUid && nodeUid in nodes){
            deselectNode(key);
        }
    }
}


// mark node as selected, and add it to the selected nodes
function selectLink(linkUid) {
    selection[linkUid] = links[linkUid];
    if(!(linkUid in linkLayer.children)){
        renderLink(links[linkUid], true);
    }
    var linkShape = linkLayer.children[linkUid].children["link"];
    oldHoverColor = viewProperties.selectionColor;
    linkShape.children["line"].strokeColor = viewProperties.selectionColor;
    linkShape.children["line"].strokeWidth = viewProperties.outlineWidthSelected*viewProperties.zoomFactor;
    linkShape.children["arrow"].fillColor = viewProperties.selectionColor;
    linkShape.children["arrow"].strokeWidth = viewProperties.outlineWidthSelected*viewProperties.zoomFactor;
    linkShape.children["arrow"].strokeColor = viewProperties.selectionColor;
}

// remove selection marking of node, and remove if from the set of selected nodes
function deselectLink(linkUid) {
    if (linkUid in selection) {
        delete selection[linkUid];
        if(linkUid in linkLayer.children){
            var linkShape = linkLayer.children[linkUid].children["link"];
            if(nodenet_data.settings.renderlinks == 'no' || nodenet_data.settings.renderlinks == 'hover'){
                linkLayer.children[linkUid].remove();
            }
            linkShape.children["line"].strokeColor = links[linkUid].strokeColor;
            linkShape.children["line"].strokeWidth = links[linkUid].strokeWidth*viewProperties.zoomFactor;
            linkShape.children["arrow"].fillColor = links[linkUid].strokeColor;
            linkShape.children["arrow"].strokeWidth = 0;
            linkShape.children["arrow"].strokeColor = null;
        }
    }
}

// mark gate as selected
function selectGate(node, gate){
    var shape = nodeLayer.children[node.uid].children["activation"].children["gates"].children[gate.index];
    selection['gate'] = shape;
    shape.strokeColor = viewProperties.selectionColor;
    shape.strokeWidth = viewProperties.outlineWidthSelected*viewProperties.zoomFactor;
}

function deselectGate(){
    if('gate' in selection){
        var shape = selection['gate'];
        shape.strokeColor = null;
        shape.strokeWidth = 0;
        delete selection['gate'];
    }
}

// deselect all nodes and links
function deselectAll() {
    for (var uid in selection){
        if (uid in nodes) deselectNode(uid);
        if (uid in links) deselectLink(uid);
        if (uid == 'gate') deselectGate();
    }
}

// should we draw this node in compact style or full?
function isCompact(node) {
    if(node.renderCompact === false) return false;
    if(node.renderCompact === true) return true;
    if(viewProperties.zoomFactor < viewProperties.forceCompactBelowZoomFactor) return true;
    else return viewProperties.compactNodes;
}

function isOutsideNodespace(node) {
    return !(node && node.uid && node.uid in nodes && node.parent == currentNodeSpace);
}

// calculate the bounding rectangle of the slot with the given index
function getSlotBounds(node, index) {
    return new Rectangle(node.bounds.x + 2,
        node.bounds.y+(2+index)*viewProperties.lineHeight*viewProperties.zoomFactor,
        viewProperties.slotWidth*viewProperties.zoomFactor,
        viewProperties.lineHeight*viewProperties.zoomFactor*0.9
    );
}

// calculate the bounding rectangle of the gate with the given index
function getGateBounds(node, index) {
    return new Rectangle(node.bounds.right-
        (viewProperties.slotWidth+2)*viewProperties.zoomFactor,
        node.bounds.y+(2+index)*viewProperties.lineHeight*viewProperties.zoomFactor,
        viewProperties.slotWidth*viewProperties.zoomFactor,
        viewProperties.lineHeight*viewProperties.zoomFactor*0.9
    );
}

// helper function to interpolate between colors
function activationColor(activation, baseColor) {
	activation = Math.max(Math.min(activation, 1.0), -1.0);
	if (activation == 0) return baseColor;
	if (activation == 1) return viewProperties.activeColor;
	if (activation == -1) return viewProperties.inhibitedColor;

	var a = Math.abs(activation);
	var r = 1.0-a;
    var c;
	if (activation > 0) {
        c = viewProperties.activeColor;
	} else {
        c = viewProperties.inhibitedColor;
	}
	return new HSLColor(c.hue,
                        baseColor.saturation * r + c.saturation * a,
                        baseColor.lightness * r + c.lightness * a);
}

function getMonitor(node, target, type){
    for(var key in monitors){
        if(monitors[key]['node_uid'] == node.uid &&
            monitors[key]['target'] == target &&
            monitors[key]['type'] == type)
            return key;
    }
    return false;
}

// mouse and keyboard interaction -----------------------------------

var hitOptions = {
    segments: false,
    stroke: true,
    fill: true,
    tolerance: 3
};

var path, hoverPath;
var movePath = false;
var clickPoint = null;

var clickOriginUid = null;
var clickType = null;
var clickIndex = -1;

var selectionStart = null;
var dragMultiples = false;

function isRightClick(event){
    return event.modifiers.control || event.event.button == 2
}

function onMouseDown(event) {
    path = hoverPath = null;
    clickType = null;
    var p = event.point;
    clickPoint = p;
    var selected_node_count = 0;
    for (key in selection){
        if(key in nodes){
            selected_node_count ++;
        }
    }
    dragMultiples = selected_node_count > 1;
    var clickedSelected = false;
    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    for (var nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            var node = nodes[nodeUid];
            var bounds = node.bounds;
            if (bounds.contains(p)) {
                path = nodeLayer.children[nodeUid];
                clickOriginUid = nodeUid;
                nodeLayer.addChild(path); // bring to front
                clickedSelected = nodeUid in selection;
                if ( !clickedSelected && !event.modifiers.shift &&
                     !event.modifiers.command && !isRightClick(event)) {
                         deselectAll();
                }
                if (event.modifiers.command && nodeUid in selection){
                    deselectNode(nodeUid); // toggle
                }
                else if(clickedSelected && selected_node_count > 1 && isRightClick(event)){
                    openMultipleNodesContextMenu(event.event);
                    return;
                }
                else if (!linkCreationStart) {
                    selectNode(nodeUid);
                    if(nodes[nodeUid].type == "Native"){
                        showNativeModuleForm(nodeUid);
                    } else {
                        showNodeForm(nodeUid);
                    }
                }
                // check for slots and gates
                var i;
                if ((i = testSlots(node, p)) >-1) {
                    clickType = "slot";
                    clickIndex = i;
                    if (isRightClick(event)){
                        var monitor = getMonitor(node, node.slotIndexes[clickIndex], 'slot');
                        $('#slot_menu [data-add-monitor]').toggle(monitor == false);
                        $('#slot_menu [data-remove-monitor]').toggle(monitor != false);
                        openContextMenu("#slot_menu", event.event);
                    }
                    else if (linkCreationStart){
                        finalizeLinkHandler(nodeUid, clickIndex); // was slotIndex TODO: clickIndex?? linkcreationstart.gateIndex???
                    }
                    return;
                } else if ((i = testGates(node, p)) > -1) {
                    clickType = "gate";
                    clickIndex = i;
                    var gate = node.gates[node.gateIndexes[i]];
                    deselectAll();
                    selectNode(node.uid);
                    selectGate(node, gate);
                    showGateForm(node, gate);
                    if (isRightClick(event)) {
                        deselectOtherNodes(node.uid);
                        var monitor = getMonitor(node, node.gateIndexes[clickIndex], 'gate');
                        $('#gate_menu [data-add-monitor]').toggle(monitor == false);
                        $('#gate_menu [data-remove-monitor]').toggle(monitor != false);
                        openContextMenu("#gate_menu", event.event);
                    }
                    return;
                }
                clickType = "node";
                if (isRightClick(event)) {
                    deselectAll();
                    selectNode(nodeUid);
                    openNodeContextMenu("#node_menu", event.event, nodeUid);
                    return;
                }
                else if (linkCreationStart) {
                    finalizeLinkHandler(nodeUid);
                }
                else {
                    movePath = true;
                    clickPoint = p;
                    return;
                }
            }
        }
    }

    if (linkCreationStart) {
        // todo: open dialog to link into different nodespaces
        if(!(clickType == "node" && nodes[path.name].type == "Nodespace")){
            cancelLinkCreationHandler();
        }
        return;
    }

    var hitResult = linkLayer.hitTest(p, hitOptions);

    if (!hitResult) {
        movePath = false;
        deselectAll();
        clickOriginUid = null;
        clickType = null;
        clickIndex = -1;
        selectionStart = p;
        selectionRectangle.x = p.x;
        selectionRectangle.y = p.y;
        if (isRightClick(event)) openContextMenu("#create_node_menu", event.event);
        showDefaultForm();
    }
    else {
        path = hitResult.item;
        if (hitResult.type == 'stroke' || hitResult.type =="fill") {
            while(path!=project && path.name!="link" && path.parent) path = path.parent;

            if (path.name == "link") {
                path = path.parent;
                if (!event.modifiers.shift && !event.modifiers.command) deselectAll();
                if (event.modifiers.command && path.name in selection) deselectLink(path.name); // toggle
                else selectLink(path.name);
                clickType = "link";
                clickOriginUid = path.name;
                if (isRightClick(event)) openContextMenu("#link_menu", event.event);
                showLinkForm(path.name);
            }
        }
    }
}

var hover = null;
var hoverNode = null;
var hoverArrow = null;
var oldHoverColor = null;

function onMouseMove(event) {
    var p = event.point;
    if (linkCreationStart) renderLinkDuringCreation(p);
    // hovering
    if (hover) { // unhover
        if (hover.name == "line") {
            hover.strokeColor = oldHoverColor;
            hoverArrow.fillColor = oldHoverColor;
            oldHoverColor = null;
        } else {
            hover.fillColor = oldHoverColor;
        }
        hover = null;
    }

    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    for (var nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            var node = nodes[nodeUid];
            var bounds = node.bounds;
            if (bounds.contains(p)) {
                if(hoverNode && nodeUid != hoverNode.uid){
                    var oldHover = hoverNode.uid;
                    hoverNode = null;
                    nodes[oldHover].renderCompact = null;
                    redrawNode(nodes[oldHover], true);
                }
                if(node.type == 'Comment'){
                    hover = nodeLayer.children[nodeUid].children['body'];
                } else {
                    hover = nodeLayer.children[nodeUid].children["activation"].children["body"];
                    // check for slots and gates
                    if ((i = testSlots(node, p)) >-1) {
                        hover = nodeLayer.children[nodeUid].children["activation"].children["slots"].children[i];
                    } else if ((i = testGates(node, p)) > -1) {
                        hover = nodeLayer.children[nodeUid].children["activation"].children["gates"].children[i];
                    }
                }
                oldHoverColor = hover.fillColor;
                hover.fillColor = viewProperties.hoverColor;
                if(isCompact(nodes[nodeUid])){
                    hoverNode = nodes[nodeUid];
                    nodes[nodeUid].renderCompact = false;
                    redrawNode(nodes[nodeUid], true);
                }
                return;
            }
        }
    }
    if(hoverNode && hoverNode.uid in nodes){
        var oldHover = hoverNode.uid;
        hoverNode = null;
        nodes[oldHover].renderCompact = null;
        redrawNode(nodes[oldHover], true);
    }
    hoverNode = null;

    if (!hover) {
        // check for links
        var hitResult = linkLayer.hitTest(event.point, hitOptions);
        if (hitResult && hitResult.item && hitResult.item.name == "line") {
            hover = hitResult.item;
            oldHoverColor = hover.strokeColor;
            hover.strokeColor = viewProperties.hoverColor;
            hoverArrow = hover.parent.children["arrow"];
            hoverArrow.fillColor = viewProperties.hoverColor;
        }
    }
}

function onDoubleClick(event) {
    // node space
    var p = view.viewToProject(DomEvent.getOffset(event, view._canvas));
    for (var nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            var node = nodes[nodeUid];
            if ((node.type == "Nodespace") && node.bounds.contains(p)) {
                handleEnterNodespace(node.uid);
                return;
            }
        }
    }
}

// check of the point is within a boundaries of a slot within the given node
// return -1 if not, and the index of the slot otherwise
function testSlots(node, p) {
    if ((!isCompact(node)) && node.slots) {
        // x coordinate within range
        if (p.x < node.bounds.x + viewProperties.slotWidth*viewProperties.zoomFactor) {
            for (var slotIndex = 0; slotIndex < node.slotIndexes.length; slotIndex++) {
                if (getSlotBounds(node, slotIndex).contains(p)) return slotIndex;
            }
        }
    }
    return -1;
}

// check of the point is within a boundaries of a gate within the given node
// return -1 if not, and the index of the slot otherwise
function testGates(node, p) {
    if (!isCompact(node) && node.gates) {
        // x coordinate within range
        if (p.x > node.bounds.x+node.bounds.width+
            (viewProperties.lineHeight/2-viewProperties.slotWidth)*viewProperties.zoomFactor) {
            for (var gateIndex = 0; gateIndex < node.gateIndexes.length; gateIndex++) {
                if (getGateBounds(node, gateIndex).contains(p)) return gateIndex;
            }
        }
    }
    return -1;
}

function onMouseDrag(event) {
    // move current node
    if(selectionStart){
        updateSelection(event);
    }
    function moveNode(uid, snap){
        var canvas = $('#nodenet');
        var pos = canvas.offset();
        var rounded = {
            'x': Math.round(event.event.layerX / 10) * 10,
            'y': Math.round(event.event.layerY / 10) * 10
        };
        if(event.event.clientX < pos.left || event.event.clientY < pos.top) return false;
        if(!snap){
            nodeLayer.children[uid].position += event.delta;
        }
        nodeLayer.children[uid].nodeMoved = true;
        var node = nodes[uid];
        if(snap){
            node.x = rounded.x / viewProperties.zoomFactor;
            node.y = rounded.y / viewProperties.zoomFactor;
        } else {
            node.x += event.delta.x/viewProperties.zoomFactor;
            node.y += event.delta.y/viewProperties.zoomFactor;
        }
        if(node.type == 'Comment'){
            node.bounds.x = node.x;
            node.bounds.y = node.y;
            redrawNode(node, true);
        } else {
            node.bounds = calculateNodeBounds(node);
            if(snap){
                redrawNode(node, true);
            }
            redrawNodeLinks(node);
        }
    }
    if (movePath) {
        if(dragMultiples){
            for(var uid in selection){
                if(uid in nodes){
                    moveNode(uid);
                }
            }
        } else {
            moveNode(path.name, nodenet_data.snap_to_grid);
        }
    }
}

function onMouseUp(event) {
    if (movePath && path) {
        if(path.nodeMoved && nodes[path.name]){
            // update position on server
            path.nodeMoved = false;
            if(dragMultiples){
                for(var uid in selection){
                    if(uid in nodes){
                        moveNode(uid, nodes[uid].x, nodes[uid].y);
                        if(max_coordinates.x && nodes[uid].x > max_coordinates.x) max_coordinates.x = nodes[uid].x;
                        if(max_coordinates.y && nodes[uid].y > max_coordinates.y) max_coordinates.y = nodes[uid].y;
                    }
                }
            } else {
                moveNode(path.name, nodes[path.name].x, nodes[path.name].y);
                if(max_coordinates.x && nodes[path.name].x > max_coordinates.x) max_coordinates.x = nodes[path.name].x;
                if(max_coordinates.y && nodes[path.name].y > max_coordinates.y) max_coordinates.y = nodes[path.name].y;
            }

            movePath = false;
            updateViewSize();
        } else if(!event.modifiers.shift && !event.modifiers.control && !event.modifiers.command && event.event.button != 2){
            if(path.name in nodes){
                deselectAll();
                selectNode(path.name);
            }
        }
    }
    if(selectionStart){
        selectionStart = null;
        selectionRectangle.x = selectionRectangle.y = 1;
        selectionRectangle.width = selectionRectangle.height = 1;
        selectionBox.setBounds(selectionRectangle);
    }

}

function onKeyDown(event) {
    // support zooming via view.zoom using characters + and -
    var modifier_key = /macintosh/.test(navigator.userAgent.toLowerCase()) ? event.modifiers.command : event.modifiers.control;
    switch(event.key){
        case "+":
            if(event.event.target.tagName == "BODY"){
                zoomIn(event);
            }
            break;
        case "-":
            if(event.event.target.tagName == "BODY"){
                zoomOut(event);
            }
            break;
        case "backspace":
        case "delete":
            if (event.event.target.tagName == "BODY") {
                event.preventDefault(); // browser-back
                deleteNodeHandler();
                deleteLinkHandler();
            }
            break;
        case "escape":
            if (linkCreationStart){
                cancelLinkCreationHandler();
            }
            break;
    }
}

function zoomIn(event){
    event.preventDefault();
    viewProperties.zoomFactor += 0.1;
    $.cookie('zoom_factor', viewProperties.zoomFactor, { expires: 7, path: '/' });
    redrawNodeNet(currentNodeSpace);
}

function zoomOut(event){
    event.preventDefault();
    if (viewProperties.zoomFactor > 0.2) viewProperties.zoomFactor -= 0.1;
    $.cookie('zoom_factor', viewProperties.zoomFactor, { expires: 7, path: '/' });
    redrawNodeNet(currentNodeSpace);
}

function onResize(event) {
    refreshViewPortData();
    updateViewSize();
}

function updateSelection(event){
    var pos = event.point;
    if(Math.abs(pos.x - selectionStart.x) > 5 && Math.abs(pos.y - selectionStart.y) > 5){
        selectionRectangle.x = Math.min(pos.x, selectionStart.x);
        selectionRectangle.y = Math.min(pos.y, selectionStart.y);
        selectionRectangle.width = Math.abs(event.point.x - selectionStart.x);
        selectionRectangle.height = Math.abs(event.point.y - selectionStart.y);
        selectionBox.setBounds(selectionRectangle);
        var scaledRectangle = new Rectangle(selectionRectangle.x/viewProperties.zoomFactor,selectionRectangle.y/viewProperties.zoomFactor, selectionRectangle.width/viewProperties.zoomFactor, selectionRectangle.height / viewProperties.zoomFactor);
        for(var uid in nodes){
            if(uid in nodeLayer.children){
                if(scaledRectangle.contains(nodes[uid])){
                    selectNode(uid);
                } else {
                    deselectNode(uid);
                }
            }
        }
    }
}

// menus -----------------------------------------------------------------------------


function initializeMenus() {
    $(".nodenet_menu").on('click', handleContextMenu);
    $("#rename_node_modal .btn-primary").on('click', handleEditNode);
    $('#rename_node_modal form').on('submit', handleEditNode);
    $("#select_datasource_modal .btn-primary").on('click', handleSelectDatasourceModal);
    $('#select_datasource_modal form').on('submit', handleSelectDatasourceModal);
    $("#select_datatarget_modal .btn-primary").on('click', handleSelectDatatargetModal);
    $('#select_datatarget_modal form').on('submit', handleSelectDatatargetModal);
    $('#edit_native_modal .btn-primary').on('click', createNativeModuleHandler);
    $('#edit_native_modal form').on('submit', createNativeModuleHandler);
    $("#edit_link_modal .btn-primary").on('click', handleEditLink);
    $("#edit_link_modal form").on('submit', handleEditLink);
    $("#nodenet").on('dblclick', onDoubleClick);
    $("#nodespace_up").on('click', handleNodespaceUp);
    gate_form_trigger = $('.gate_additional_trigger');
    gate_params = $('.gate_additional');
    gate_form_trigger.on('click', function(){
        if(gate_params.hasClass('hide')){
            gate_form_trigger.text("Hide additional parameters");
            gate_params.removeClass('hide');
        } else {
            gate_form_trigger.text("Show additional parameters");
            gate_params.addClass('hide');
        }
    });
}

function initializeControls(){
    $('#zoomOut').on('click', zoomOut);
    $('#zoomIn').on('click', zoomIn);
    $('#nodespace_control').on('click', ['data-nodespace'] ,function(event){
        event.preventDefault();
        var nodespace = $(event.target).attr('data-nodespace');
        if(nodespace != currentNodeSpace){
            refreshNodespace(nodespace, {
                x: [0, canvas_container.width() * 2],
                y: [0, canvas_container.height() * 2]
            }, -1);
        }
    });
}

function initializeDialogs(){
    var source_gate = $("#link_source_gate");
    var target_nodespace = $("#link_target_nodespace");
    var target_node = $("#link_target_node");
    var target_slot = $('#link_target_slot');
    target_nodespace.on('change', function(event){
        var ns = nodespaces[target_nodespace.val()];
        if(ns){
            var html = '';
            var nodes = Object.values(ns.nodes);
            nodes.sort(sortByName);
            for(var i in nodes){
                html += '<option value="'+nodes[i].uid+'">'+nodes[i].name + '('+nodes[i].type+')</option>';
            }
            target_node.html(html);
            target_node.trigger('change');
        }
    });
    target_node.on('change', function(event){
        var node = nodespaces[target_nodespace.val()].nodes[target_node.val()];
        if(node){
            var slots = nodetypes[node.type].slottypes;
            var html = '';
            for(var i in slots){
                html += '<option value="'+slots[i]+'">'+slots[i]+'</option>';
            }
            target_slot.html(html);
        }
    });
    $('#create_link_modal .btn-primary').on('click', function(event){
        event.preventDefault();
        createLinkFromDialog(path.name, source_gate.val(), target_node.val(), target_slot.val());
        $("#create_link_modal").modal("hide");
    });
    $('#create_link_modal select:last').on('change', function(){
        $('#create_link_modal .btn-primary').focus();
    });
    $('#datatarget_select').on('change', function(){
        $("#select_datatarget_modal .btn-primary").focus();
    });
    $('#datasource_select').on('change', function(){
        $("#select_datasource_modal .btn-primary").focus();
    });
    $('#nodenet_user_prompt .btn-primary').on('click', function(event){
        event.preventDefault();
        var form = $('#nodenet_user_prompt form');
        values = {};
        var startnet = false;
        var fields = form.serializeArray();
        for(var idx in fields){
            if(fields[idx].name == 'run_nodenet'){
                startnet = true;
            } else {
                values[fields[idx].name] = fields[idx].value;
            }
        }
        api.call('user_prompt_response', {
            nodenet_uid: currentNodenet,
            node_uid: $('#user_prompt_node_uid').val(),
            values: values,
            resume_nodenet: startnet
        }, function(data){
            currentSimulationStep -= 1;
            refreshNodespace();
        });
        $('#nodenet_user_prompt').modal('hide');
    });

    $('#paste_mode_selection_modal .btn-primary').on('click', function(event){
        event.preventDefault();
        var form = $('#paste_mode_selection_modal form');
        handlePasteNodes(form.serializeArray()[0].value);
        $('#paste_mode_selection_modal').modal('hide');
    });
}

var clickPosition = null;

function openContextMenu(menu_id, event) {
    event.cancelBubble = true;
    if(!currentNodenet){
        return;
    }
    clickPosition = new Point(event.layerX, event.layerY);
    $(menu_id).css({
        position: "absolute",
        zIndex: 500,
        marginLeft: -5, marginTop: -5,
        top: event.pageY, left: event.pageX });
    if(menu_id == '#create_node_menu'){
        var list = $('[data-nodetype-entries]');
        html = '';
        for(var idx in sorted_nodetypes){
            if(!(sorted_nodetypes[idx] in native_modules))
                html += '<li><a data-create-node="' + sorted_nodetypes[idx] + '">Create ' + sorted_nodetypes[idx] +'</a></li>';
        }
        if(Object.keys(native_modules).length){
            if(Object.keys(native_modules).length > 6 ){
                html += '<li class="divider"></li><li><a  data-create-node="Native">Create Native Module</a></i></li>';
            } else {
                html += '<li class="divider"></li><li><a>Create Native Module<i class="icon-chevron-right"></i></a>';
                html += '<ul class="sub-menu dropdown-menu">';
                for(var key in native_modules){
                    html += '<li><a data-create-node="' + key + '">Create '+ key +' Node</a></li>';
                }
                html += '</ul></li>';
            }
        }
        html += '<li class="divider"></li><li><a data-auto-align="true">Autoalign Nodes</a></li>';
        html += '<li class="divider"></li><li data-paste-nodes';
        if(Object.keys(clipboard).length === 0){
            html += ' class="disabled"';
        }
        html += '><a href="#">Paste nodes</a></li>';
        list.html(html);
    }
    $(menu_id+" .dropdown-toggle").dropdown("toggle");
}

function openMultipleNodesContextMenu(event){
    var typecheck = null;
    var sametype = true;
    var node = null;
    for(var uid in selection){
        if(typecheck == null || typecheck == nodes[uid].type){
            typecheck = nodes[uid].type;
            node = nodes[uid];
        } else {
            sametype = false;
            break;
        }
    }
    var menu = $('#multi_node_menu .nodenet_menu');
    var html = '<li data-copy-nodes><a href="#">Copy nodes</a></li>'+
        '<li data-paste-nodes><a href="#">Paste nodes</a></li>'+
        '<li><a href="#">Delete nodes</a></li>';
    if(sametype){
        html += '<li class="divider"></li>' + getNodeLinkageContextMenuHTML(node);
    }
    menu.html(html);
    if(Object.keys(clipboard).length === 0){
        $('#multi_node_menu li[data-paste-nodes]').addClass('disabled');
    } else {
        $('#multi_node_menu li[data-paste-nodes]').removeClass('disabled');
    }
    openContextMenu('#multi_node_menu', event);
}

function getNodeLinkageContextMenuHTML(node){
    var html = '';
    if (node.gateIndexes.length) {
        for (var gateName in node.gates) {
            if(gateName in inverse_link_map){
                var compound = gateName+'/'+inverse_link_map[gateName];
                html += ('<li><a data-link-type="'+compound+'">Draw '+compound+' link</a></li>');
            } else if(inverse_link_targets.indexOf(gateName) == -1){
                html += ('<li><a href="#" data-link-type="'+gateName+'">Draw '+gateName+' link</a></li>');
            }
        }
        html += ('<li><a href="#" data-link-type="">Create link</a></li>');
        html += ('<li class="divider"></li>');
    }
    return html;
}

// build the node menu
function openNodeContextMenu(menu_id, event, nodeUid) {
    var menu = $(menu_id+" .dropdown-menu");
    menu.off('click', 'li');
    menu.empty();
    var node = nodes[nodeUid];
    menu.html(getNodeLinkageContextMenuHTML(node));
    if(node.type == "Sensor"){
        menu.append('<li><a href="#">Select datasource</li>');
    }
    if(node.type == "Actor"){
        menu.append('<li><a href="#">Select datatarget</li>');
    }
    menu.append('<li><a href="#">Rename node</a></li>');
    menu.append('<li><a href="#">Delete node</a></li>');
    menu.append('<li data-copy-nodes><a href="#">Copy node</a></li>');
    openContextMenu(menu_id, event);
}

// universal handler for all context menu events. You can get the origin path from the variable clickTarget.
function handleContextMenu(event) {
    event.preventDefault();
    var menuText = event.target.text;
    $el = $(event.target);
    if($el.parent().hasClass('disabled')){
        return false;
    }
    if($el.parent().attr('data-copy-nodes') === ""){
        copyNodes();
        $el.parentsUntil('.dropdown-menu').dropdown('toggle');
        return;
    } else if($el.parent().attr('data-paste-nodes') === ""){
        pasteNodes(clickPosition);
        $el.parentsUntil('.dropdown-menu').dropdown('toggle');
        return;
    }
    switch (clickType) {
        case null: // create nodes
            var type = $el.attr("data-create-node");
            var autoalign = $el.attr("data-auto-align");
            if(!type && !autoalign){
                if(menuText == "Delete nodes"){
                    deleteNodeHandler(clickOriginUid);
                    return;
                } else if($(event.target).attr('data-link-type') != undefined) {
                    // multi node menu
                    var linktype = $(event.target).attr('data-link-type');
                    if (linktype) {
                        var forwardlinktype = linktype;
                        if(forwardlinktype.indexOf('/')){
                            forwardlinktype = forwardlinktype.split('/')[0];
                        }
                        for(var uid in selection){
                            clickIndex = nodes[uid].gateIndexes.indexOf(forwardlinktype);
                            createLinkHandler(uid, clickIndex, linktype);
                        }
                    } else {
                        openLinkCreationDialog(path.name)
                    }
                    $el.parentsUntil('.dropdown-menu').dropdown('toggle');
                } else {
                    return false;
                }
            }
            var callback = function(data){
                dialogs.notification('Node created', 'success');
            };

            switch (type) {
                case "Sensor":
                    callback = function(data){
                        clickOriginUid = data;
                        dialogs.notification('Please Select a datasource for this sensor');
                        var source_select = $('#select_datasource_modal select');
                        source_select.html('');
                        $("#select_datasource_modal").modal("show");
                        var html = get_datasource_options(currentWorldadapter);
                        source_select.html(html);
                        source_select.val(nodes[clickOriginUid].parameters['datasource']).select().focus();
                    };
                    break;
                case "Actor":
                    callback = function(data){
                        clickOriginUid = data;
                        dialogs.notification('Please Select a datatarget for this actor');
                        var target_select = $('#select_datatarget_modal select');
                        target_select.html('');
                        $("#select_datatarget_modal").modal("show");
                        var html = get_datatarget_options(currentWorldadapter);
                        target_select.html(html);
                        target_select.val(nodes[clickOriginUid].parameters['datatarget']).select().focus();
                    };
                    break;
            }
            if(autoalign){
                autoalignmentHandler();
            } else if(type) {
                if (type == "Native"){
                    createNativeModuleHandler();
                }
                else {
                    if(nodenet_data.snap_to_grid){
                        var xpos = Math.round(clickPosition.x / 10) * 10;
                        var ypos = Math.round(clickPosition.y / 10) * 10;
                    } else {
                        var xpos = clickPosition.x;
                        var ypos = clickPosition.y;
                    }
                    createNodeHandler(xpos/viewProperties.zoomFactor,
                        ypos/viewProperties.zoomFactor,
                        "", type, null, callback);
                }
            } else{
                return false;
            }
            break;
        case "node":
            switch (menuText) {
                case "Rename node":
                    var nodeUid = clickOriginUid;
                    if (nodeUid in nodes) {
                        var input = $('#rename_node_input');
                        $("#rename_node_modal").modal("show");
                        input.val(nodes[nodeUid].name).select().focus();
                    }
                    break;
                case "Delete node":
                    deleteNodeHandler(clickOriginUid);
                    break;
                case "Select datasource":
                    var source_select = $('#select_datasource_modal select');
                    source_select.html('');
                    $("#select_datasource_modal").modal("show");
                    var html = get_datasource_options(currentWorldadapter);
                    source_select.html(html);
                    source_select.val(nodes[clickOriginUid].parameters['datasource']).select().focus();
                    break;
                case "Select datatarget":
                    var target_select = $('#select_datatarget_modal select');
                    $("#select_datatarget_modal").modal("show");
                    target_select.html('');
                    var html = get_datatarget_options(currentWorldadapter);
                    target_select.html(html);
                    target_select.val(nodes[clickOriginUid].parameters['datatarget']).select().focus();
                    break;
                default:
                    // link creation
                    var linktype = $(event.target).attr('data-link-type');
                    if (linktype) {
                        var forwardlinktype = linktype;
                        if(forwardlinktype.indexOf('/')){
                            forwardlinktype = forwardlinktype.split('/')[0];
                        }
                        clickIndex = nodes[clickOriginUid].gateIndexes.indexOf(forwardlinktype);
                        createLinkHandler(clickOriginUid, clickIndex, linktype);
                    } else {
                        openLinkCreationDialog(path.name);
                    }
            }
            break;
        case "slot":
            switch (menuText) {
                case "Add monitor to slot":
                    addSlotMonitor(nodes[clickOriginUid], clickIndex);
                    break;
                case "Remove monitor from slot":
                    removeMonitor(nodes[clickOriginUid], nodes[clickOriginUid].slotIndexes[clickIndex], 'slot');
                    break;
            }
            break;
        case "gate":
            switch (menuText) {
                case "Draw link":
                    createLinkHandler(clickOriginUid, clickIndex);
                    break;
                case "Add monitor to gate":
                    addGateMonitor(nodes[clickOriginUid], clickIndex);
                    break;
                case "Remove monitor from gate":
                    removeMonitor(nodes[clickOriginUid], nodes[clickOriginUid].gateIndexes[clickIndex], 'gate');
                    break;
            }
            break;
        case "link":
            switch (menuText) {
                case "Add link-weight monitor":
                    addLinkMonitor(clickOriginUid);
                    break;
                case "Delete link":
                    deleteLinkHandler(clickOriginUid);
                    break;
                case "Edit link":
                    var linkUid = clickOriginUid;
                    if (linkUid in links) {
                        $("#link_weight_input").val(links[linkUid].weight);
                        $("#link_certainty_input").val(links[linkUid].certainty);
                        $("#link_weight_input").focus();
                    }
                    break;
            }
    }
    view.draw();
}

function openLinkCreationDialog(nodeUid){
    $("#link_target_node").html('');
    $('#link_target_slot').html('');
    var html = '';
    var sorted_ns = Object.values(nodespaces);
    sorted_ns.sort(sortByName);
    for(var i in sorted_ns){
        html += '<option value="'+sorted_ns[i].uid+'">'+sorted_ns[i].name+'</option>';
    }
    $('#link_target_nodespace').html(html);
    html = '';
    for(var g in nodes[nodeUid].gates){
        html += '<option value="'+g+'">'+g+'</option>';
    }
    $("#link_source_gate").html(html);
    $('#link_target_nodespace').trigger('change');
    $("#create_link_modal").modal("show");
}

function get_datasource_options(worldadapter, value){
    var sources = worldadapters[worldadapter].datasources;
    html = '<optgroup label="Datasources">';
    for(var i in sources){
        html += '<option value="'+sources[i]+'"'+ ((value && value==sources[i]) ? ' selected="selected"':'') +'>'+sources[i]+'</option>';
    }
    html += '</optgroup>';
    html += '<optgroup label="Nodenet Globals">';
    for(var i in globalDataSources){
        html += '<option value="'+globalDataSources[i]+'"'+ ((value && value==globalDataSources[i]) ? ' selected="selected"':'') +'>'+globalDataSources[i]+'</option>';
    }
    html += '</optgroup>';
    return html;
}

function get_datatarget_options(worldadapter, value){
    var targets = worldadapters[worldadapter].datatargets;
    html = '<optgroup label="Datatargets">';
    for(var i in targets){
        html += '<option value="'+targets[i]+'"'+ ((value && value==targets[i]) ? ' selected="selected"':'') +'>'+targets[i]+'</option>';
    }
    html += '</optgroup>';
    html += '<optgroup label="Nodenet Globals">';
    for(var i in globalDataTargets){
        html += '<option value="'+globalDataTargets[i]+'"'+ ((value && value==globalDataTargets[i]) ? ' selected="selected"':'') +'>'+globalDataTargets[i]+'</option>';
    }
    html += '</optgroup>';
    return html;
}

// rearrange nodes in the current nodespace
function autoalignmentHandler() {
    api.call("align_nodes", {
            nodenet_uid: currentNodenet,
            nodespace: currentNodeSpace
        },
        function(data){
            setCurrentNodenet(currentNodenet, currentNodeSpace);
        });
}

// let user create a new node
function createNodeHandler(x, y, name, type, parameters, callback) {
    params = {};
    if (!parameters) parameters = {};
    if (nodetypes[type]){
        for (var i in nodetypes[type].parameters){
            params[nodetypes[type].parameters[i]] = parameters[nodetypes[type].parameters[i]] || "";
        }
    }
    api.call("add_node", {
        nodenet_uid: currentNodenet,
        type: type,
        position: [x,y],
        nodespace: currentNodeSpace,
        name: name,
        parameters: params },
        success=function(uid){
            addNode(new Node(uid, x, y, currentNodeSpace, name, type, null, null, params));
            view.draw();
            selectNode(uid);
            if(callback) callback(uid);
            showNodeForm(uid);
            getNodespaceList();
        });
}


function createNativeModuleHandler(event){
    var modal = $("#edit_native_modal");
    if(event){
        event.preventDefault();
        createNodeHandler(clickPosition.x/viewProperties.zoomFactor,
                        clickPosition.y/viewProperties.zoomFactor,
                        $('#native_module_name').val(),
                        $('#native_module_type').val(),
                        {}, null);
        modal.modal("hide");
    } else {
        var html = '';
        for(var idx in sorted_nodetypes){
            if(sorted_nodetypes[idx] in native_modules){
                html += '<option>'+ sorted_nodetypes[idx] +'</option>';
            }
        }
        $('[data-native-module-type]', modal).html(html);
        $('#native_module_name').val('');
        modal.modal("show");
    }
}

copyPosition = null;
function copyNodes(event){
    copyPosition = {'x': nodes[clickOriginUid].x, 'y': nodes[clickOriginUid].y};
    clipboard = {};
    for(var uid in selection){
        if(uid in nodes){
            clipboard[uid] = nodes[uid];
            copyPosition.x = Math.min(nodes[uid].x, copyPosition.x);
            copyPosition.y = Math.min(nodes[uid].y, copyPosition.y);
        }
    }
}

function pasteNodes(clickPos){
    $('#paste_mode_selection_modal').modal('show');
}

function handlePasteNodes(pastemode){
    // none;
    var offset = [viewProperties.copyPasteOffset, viewProperties.copyPasteOffset];
    if(clickPosition && copyPosition){
        offset = [(clickPosition.x / viewProperties.zoomFactor) - (copyPosition.x), (clickPosition.y / viewProperties.zoomFactor) - (copyPosition.y)];
    }
    copy_ids = Object.keys(clipboard);
    api.call('clone_nodes', {
        nodenet_uid: currentNodenet,
        node_uids: copy_ids,
        clone_mode: pastemode,
        nodespace: currentNodeSpace,
        offset: offset
    }, success = function(data){
        deselectAll();
        for(var i = 0; i < data.nodes.length; i++){
            var n = data.nodes[i];
            addNode(new Node(n.uid, n.position[0], n.position[1], n.parent_nodespace, n.name, n.type, null, null, n.parameters));
            selectNode(n.uid);
        }
        for(i = 0; i < data.links.length; i++){
            var l = data.links[i];
            addLink(new Link(l.uid, l.source_node_uid, l.source_gate_name, l.target_node_uid, l.target_slot_name, l.weight, l.certainty));
        }
        view.draw();
    });
}

// let user delete the current node, or all selected nodes
function deleteNodeHandler(nodeUid) {
    function deleteNodeOnServer(node_uid){
        api.call("delete_node",
            {nodenet_uid:currentNodenet, node_uid: node_uid},
            success=function(data){
                dialogs.notification('node deleted', 'success');
                getNodespaceList();
            }
        );
    }
    var deletedNodes = [];
    if (nodeUid in nodes) {
        deletedNodes.push(nodeUid);
        removeNode(nodes[nodeUid]);
        if (nodeUid in selection) delete selection[nodeUid];
    }
    for (var selected in selection) {
        if(selection[selected].constructor == Node){
            deletedNodes.push(selected);
            removeNode(nodes[selected]);
            delete selection[selected];
        }
    }
    for(var i in deletedNodes){
        deleteNodeOnServer(deletedNodes[i]);
    }
    showDefaultForm();
}

// let user delete the current link, or all selected links
function deleteLinkHandler(linkUid) {
    function removeLinkOnServer(linkUid){
        api.call("delete_link",
            {   nodenet_uid:currentNodenet,
                source_node_uid: links[linkUid].sourceNodeUid,
                gate_type: links[linkUid].gateName,
                target_node_uid: links[linkUid].targetNodeUid,
                slot_type: links[linkUid].slotName
            },
            success= function(data){
                dialogs.notification('Link removed', 'success');
            }
        );
    }
    if (linkUid in links) {
        removeLinkOnServer(linkUid);
        removeLink(links[linkUid]);
        if (linkUid in selection) delete selection[linkUid];
    }
    for (var selected in selection) {
        if(selection[selected].constructor == Link){
            removeLinkOnServer(selected);
            removeLink(links[selected]);
            delete selection[selected];
        }
    }
    showDefaultForm();
}

function handleEditLink(event){
    event.preventDefault();
    var form = event.target.form;
    var linkUid = clickOriginUid;
    var weight = parseFloat($('input[name="link_weight"]', form).val());
    var certainty = parseFloat($('input[name="link_certainty"]', form).val());
    links[linkUid].weight = weight;
    links[linkUid].certainty = certainty;
    redrawLink(links[linkUid], true);
    view.draw();
    api.call("set_link_weight", {
        nodenet_uid:currentNodenet,
        source_node_uid: links[linkUid].sourceNodeUid,
        gate_type: links[linkUid].gateName,
        target_node_uid: links[linkUid].targetNodeUid,
        slot_type: links[linkUid].slotName,
        weight: weight,
        certainty: certainty
    });
}

function handleDeleteLink(event){
    event.preventDefault();
    deleteLinkHandler(clickOriginUid);
}

linkCreationStart = null;

// start the creation of a new link
function createLinkHandler(nodeUid, gateIndex, creationType) {
    if ((nodeUid in nodes) && (nodes[nodeUid].gateIndexes.length > gateIndex)){
        gateIndex = Math.max(gateIndex,0); // if no gate give, assume gen gate
        switch (creationType) {
            case "por/ret":
                gateIndex = 1;
                break;
            case "sub/sur":
                gateIndex = 3;
                break;
            case "cat/exp":
                gateIndex = 5;
                break;
            case "gen":
                gateIndex = 0;
                break;
        }
        if(!linkCreationStart){
            linkCreationStart = [];
        }
        linkCreationStart.push({
            sourceNode: nodes[nodeUid],
            gateIndex: gateIndex, // if no gate give, assume gen gate
            creationType: creationType
        });
    }
}

function createLinkFromDialog(sourceUid, sourceGate, targetUid, targetSlot){
    var uids = [];
    for(var uid in selection){
        if(uid in nodes){
            uids.push(uid);
        }
    }
    if(!uids.length){
        uids = [sourceNodeUid];
    }
    for(var i=0; i < uids.length; i++){
        sourceUid = uids[i];
        if ((sourceUid in nodes)) {
            if(!(targetUid in nodes)){
                api.call('get_node', {
                    'nodenet_uid': currentNodenet,
                    'node_uid': targetUid
                }, function(data){
                    nodes[targetUid] = new Node(data.uid, data.position[0], data.position[1], data.parent_nodespace, data.name, data.type, data.sheaves, data.state, data.parameters, data.gate_activations, data.gate_parameters);
                    createLinkFromDialog(sourceUid, sourceGate, targetUid, targetSlot);
                });
            } else {
                // TODO: also write backwards link??
                api.call("add_link", {
                    nodenet_uid: currentNodenet,
                    source_node_uid: sourceUid,
                    gate_type: sourceGate,
                    target_node_uid: targetUid,
                    slot_type: targetSlot,
                    weight: 1
                }, function(uid){
                    if(!(targetUid in nodes)){
                        api.call('get_node', {
                            'nodenet_uid': currentNodenet,
                            'node_uid': targetUid
                        }, function(data){
                            nodes[targetUid] = data;
                            nodes[targetUid].linksFromOutside.push(uid);
                        });
                    } else if(nodes[targetUid].parent != currentNodeSpace){
                        nodes[sourceUid].linksToOutside.push(uid);
                        nodes[targetUid].linksFromOutside.push(uid);
                    }
                    addLink(new Link(uid, sourceUid, sourceGate, targetUid, targetSlot, 1, 1));
                });
            }
        }
    }
}


// establish the created link
function finalizeLinkHandler(nodeUid, slotIndex) {
    var targetNode = nodes[nodeUid];
    var targetUid = nodeUid;
    for(var i=0; i < linkCreationStart.length; i++){
        var sourceNode = linkCreationStart[i].sourceNode;
        var sourceUid = linkCreationStart[i].sourceNode.uid;
        var gateIndex = linkCreationStart[i].gateIndex;

        if (!slotIndex || slotIndex < 0) slotIndex = 0;

        if ((targetUid in nodes) &&
            nodes[targetUid].slots && (nodes[targetUid].slotIndexes.length > slotIndex)) {

            var targetGates = nodes[targetUid].gates ? nodes[targetUid].gateIndexes.length : 0;
            var targetSlots = nodes[targetUid].slots ? nodes[targetUid].slotIndexes.length : 0;
            var sourceSlots = sourceNode.slots ? sourceNode.slotIndexes.length : 0;

            var newlinks = [];

            switch (linkCreationStart[i].creationType) {
                case "por/ret":
                    // the por link
                    if (targetSlots > 2) {
                        newlinks.push(createLinkIfNotExists(sourceNode, "por", targetNode, "por", 1, 1));
                    } else {
                        newlinks.push(createLinkIfNotExists(sourceNode, "por", targetNode, "gen", 1, 1));
                    }
                    // the ret link
                    if (targetGates > 2) {
                        if(sourceSlots > 2) {
                            newlinks.push(createLinkIfNotExists(targetNode, "ret", sourceNode, "ret", 1, 1));
                        } else {
                            newlinks.push(createLinkIfNotExists(targetNode, "ret", sourceNode, "gen", 1, 1));
                        }
                    }
                    break;
                case "sub/sur":
                    // the sub link
                    if (targetSlots > 4 || nodes[targetUid].type == "Trigger") {
                        newlinks.push(createLinkIfNotExists(sourceNode, "sub", targetNode, "sub", 1, 1));
                    } else {
                        newlinks.push(createLinkIfNotExists(sourceNode, "sub", targetNode, "gen", 1, 1));
                    }
                    // the sur link
                    if (targetGates > 4 || nodes[targetUid].type == "Trigger") {
                        if(sourceSlots > 4 || nodes[targetUid].type == "Trigger") {
                            newlinks.push(createLinkIfNotExists(targetNode, "sur", sourceNode, "sur", 1, 1));
                        } else {
                            newlinks.push(createLinkIfNotExists(targetNode, "sur", sourceNode, "gen", 1, 1));
                        }
                    }
                    break;
                case "cat/exp":
                    // the cat link
                    if (targetSlots > 6) {
                        newlinks.push(createLinkIfNotExists(sourceNode, "cat", targetNode, "cat", 1, 1));
                    } else {
                        newlinks.push(createLinkIfNotExists(sourceNode, "cat", targetNode, "gen", 1, 1));
                    }
                    // the exp link
                    if (targetGates > 6) {
                        if(sourceSlots > 6) {
                            newlinks.push(createLinkIfNotExists(targetNode, "exp", sourceNode, "exp", 1, 1));
                        } else {
                            newlinks.push(createLinkIfNotExists(targetNode, "exp", sourceNode, "gen", 1, 1));
                        }
                    }
                    break;
                default:
                    newlinks.push(createLinkIfNotExists(sourceNode, sourceNode.gateIndexes[gateIndex], targetNode, targetNode.slotIndexes[slotIndex], 1, 1));
            }

            $.each(newlinks, function(idx, link){
                if(link){
                    api.call("add_link", {
                        nodenet_uid: currentNodenet,
                        source_node_uid: link.sourceNodeUid,
                        gate_type: link.gateName,
                        target_node_uid: link.targetNodeUid,
                        slot_type: link.slotName,
                        weight: link.weight
                    }, function(uid){
                        link.uid = uid;
                        if(!(link.sourceUid in nodes) || nodes[link.sourceNodeUid].parent != currentNodeSpace){
                            if(link.targetNodeUid in nodes) nodes[link.targetNodeUid].linksFromOutside.push(link.uid);
                            if(link.sourceNodeUid in nodes) nodes[link.sourceNodeUid].linksToOutside.push(link.uid);
                        }
                        addLink(link);
                    });
                }
            });
        }
    }
    cancelLinkCreationHandler();
}

function createLinkIfNotExists(sourceNode, sourceGate, targetNode, targetSlot, weight, certainty){
    for(var uid in sourceNode.gates[sourceGate].outgoing){
        var link = sourceNode.gates[sourceGate].outgoing[uid];
        if(link.targetNodeUid == targetNode.uid && link.slotName == targetSlot){
            return false;
        }
    }
    var newlink = new Link('tmp', sourceNode.uid, sourceGate, targetNode.uid, targetSlot, weight || 1, certainty || 1);
    return newlink;
}

// cancel link creation
function cancelLinkCreationHandler() {
    if(templinks){
        $.each(templinks, function(idx, link){
            link.remove();
        });
    }
    linkCreationStart = null;
}

function addLinkMonitor(clickOriginUid){
    var link = links[clickOriginUid];
    event.preventDefault();
    $('#monitor_name_input').val('');
    $('#monitor_modal .custom_monitor').hide();
    $('#monitor_modal').modal('show');
    $('#monitor_modal .btn-primary').on('click', function(event){
        api.call('add_link_monitor', {
            nodenet_uid: currentNodenet,
            source_node_uid: link.sourceNodeUid,
            gate_type: link.gateName,
            target_node_uid: link.targetNodeUid,
            slot_type: link.slotName,
            name: $('#monitor_name_input').val(),
            property:'weight'
        }, function(data){
            dialogs.notification("monitor saved");
            $(document).trigger('monitorsChanged', data);
            $('#monitor_modal .btn-primary').off();
            $('#monitor_modal').modal('hide');
        }, function(data){
            api.defaultErrorCallback(data);
            $('#monitor_modal .btn-primary').off();
            $('#monitor_modal').modal('hide');
        });
    });
}

function moveNode(nodeUid, x, y){
    api.call("set_node_position", {
        nodenet_uid: currentNodenet,
        node_uid: nodeUid,
        position: [x,y]});
}

function handleEditNode(event){
    event.preventDefault();
    ApplyLineBreaks('node_comment_input');
    form = $(event.target);
    var nodeUid = $('#node_uid_input').val();
    if($(".modal")) $(".modal").modal("hide");
    var parameters = {};
    var fields = form.serializeArray();
    var name = null;
    var state = {};
    var activation = null;
    for (var i in fields){
        if(nodetypes[nodes[nodeUid].type] &&
            (nodetypes[nodes[nodeUid].type].parameters || []).indexOf(fields[i].name) > -1 &&
            nodes[nodeUid].parameters[fields[i].name] != fields[i].value){
                parameters[fields[i].name] = fields[i].value;
        }
        switch(fields[i].name){
            case "node_name":
                name = fields[i].value;
                break;
            case "node_state":
                state = fields[i].value;
                break;
            case "node_activation":
                activation = fields[i].value;
                break;
            case "node_comment":
                if(nodes[nodeUid].type == 'Comment')
                    parameters['comment'] = fields[i].value;
        }
    }
    if(name && nodes[nodeUid].name != name){
        renameNode(nodeUid, name);
    }
    if(!jQuery.isEmptyObject(parameters) && nodes[nodeUid].type != 'Nodespace'){
        updateNodeParameters(nodeUid, parameters);
    }
    if(nodes[nodeUid].state != state  && nodes[nodeUid].type != 'Nodespace'){
        setNodeState(nodeUid, state);
    }
    if(nodes[nodeUid].sheaves[currentSheaf].activation != activation && nodes[nodeUid].type != 'Nodespace'){
        setNodeActivation(nodeUid, activation);
    }
    redrawNode(nodes[nodeUid], true);
    view.draw(true);
}

function handleEditGate(event){
    event.preventDefault();
    var node, gate;
    if(clickType == 'gate'){
        node = nodes[clickOriginUid];
        gate = node.gates[node.gateIndexes[clickIndex]];
    }
    var form = $(event.target);
    var data = form.serializeArray();
    var params = {};
    var old_params = gate.parameters;
    for(var i in data){
        if(!data[i].value && data[i].name in GATE_DEFAULTS){
            data[i].value = GATE_DEFAULTS[data[i].name];
        }
        params[data[i].name] = parseFloat(data[i].value);
    }
    api.call('set_gate_parameters', {
        nodenet_uid: currentNodenet,
        node_uid: node.uid,
        gate_type: gate.name,
        parameters: params
    }, api.defaultSuccessCallback, function(err){
        api.defaultErrorCallback(err);
        gate.parameters = old_params;
        if(form.css('display') == 'block'){
            showGateForm(node, gate);
        }
    });
    gate.parameters = params;
}

function setNodeActivation(nodeUid, activation){
    activation = activation || 0;
    nodes[nodeUid].sheaves[currentSheaf].activation = activation;
    //TODO not sure this is generic enough, should probably just take the 0th
    if(nodes[nodeUid].gates["gen"]) {
        nodes[nodeUid].gates["gen"].sheaves[currentSheaf].activation = activation;
    }
    api.call('set_node_activation', {
        'nodenet_uid': currentNodenet,
        'node_uid': nodeUid,
        'activation': activation
    });
}

function setNodeState(nodeUid, state){
    nodes[nodeUid].state = state;
    api.call('set_node_state', {
        'nodenet_uid': currentNodenet,
        'node_uid': nodeUid,
        'state': state
    });
}

function updateNodeParameters(nodeUid, parameters){
    for(var key in parameters){
        if(!key.length){
            delete parameters[key];
        }
    }
    nodes[nodeUid].parameters = parameters;
    api.call("set_node_parameters", {
        nodenet_uid: currentNodenet,
        node_uid: nodeUid,
        parameters: parameters
    }, api.defaultSuccessCallback, api.defaultErrorCallback, "post");
}

// handler for renaming the node
function renameNode(nodeUid, name) {
    if(nodes[nodeUid]) {
        nodes[nodeUid].name = name;
    }
    api.call("set_node_name", {
        nodenet_uid: currentNodenet,
        node_uid: nodeUid,
        name: name
    }, success=function(){
        getNodespaceList();
    });
}

function handleSelectDatasourceModal(event){
    var nodeUid = clickOriginUid;
    var value = $('#select_datasource_modal select').val();
    $("#select_datasource_modal").modal("hide");
    nodes[clickOriginUid].parameters['datasource'] = value;
    showNodeForm(nodeUid);
    api.call("bind_datasource_to_sensor", {
        nodenet_uid: currentNodenet,
        sensor_uid: nodeUid,
        datasource: value
    });
}

function handleSelectDatatargetModal(event){
    var nodeUid = clickOriginUid;
    var value = $('#select_datatarget_modal select').val();
    $("#select_datatarget_modal").modal("hide");
    nodes[clickOriginUid].parameters['datatarget'] = value;
    showNodeForm(nodeUid);
    api.call("bind_datatarget_to_actor", {
        nodenet_uid: currentNodenet,
        actor_uid: nodeUid,
        datatarget: value
    });
}

// handler for entering a nodespace
function handleEnterNodespace(nodespaceUid) {
    if (nodespaceUid in nodes) {
        deselectAll();
        refreshNodespace(nodespaceUid, {
            x: [0, canvas_container.width() * 2],
            y: [0, canvas_container.height() * 2]
        }, -1);
    }
}

// handler for entering parent nodespace
function handleNodespaceUp() {
    deselectAll();
    if (nodespaces[currentNodeSpace].parent) { // not yet root nodespace
        refreshNodespace(nodespaces[currentNodeSpace].parent, {
            x: [0, canvas_container.width() * 2],
            y: [0, canvas_container.height() * 2]
        }, -1);
    }
}

function handleEditNodenet(event){
    event.preventDefault();
    var form = event.target;
    var reload = false;
    var params = {
        nodenet_uid: currentNodenet,
        nodenet_name: $('#nodenet_name', form).val()
    };
    var nodenet_world = $('#nodenet_world', form).val();
    if(nodenet_world){
        params.world_uid = nodenet_world;
    }
    if(nodenet_world != nodenet_data.world){
        if(nodenet_data.world == currentWorld || nodenet_world == currentWorld){
            reload = true;
        }
    }
    var worldadapter = $('#nodenet_worldadapter', form).val();
    if(worldadapter){
        params.worldadapter = worldadapter;
    }
    nodenet_data.settings['renderlinks'] = $('#nodenet_renderlinks').val();
    params.settings = nodenet_data.settings;
    $.cookie('snap_to_grid', $('#nodenet_snap').attr('checked') || '', {path: '/', expires: 7})
    api.call("set_nodenet_properties", params,
        success=function(data){
            dialogs.notification('Nodenet data saved', 'success');
            if(reload){
                window.location.reload();
            } else {
                setCurrentNodenet(currentNodenet, currentNodeSpace);
            }
        }
    );
}

function handleEditNodespace(event){
    event.preventDefault();
    var name = $('#nodespace_name').val();
    if(name != nodespaces[currentNodeSpace].name){
        renameNode(currentNodeSpace, name);
    }
    var nodetype = $('#nodespace_gatefunction_nodetype').val();
    var gatename = $('#nodespace_gatefunction_gate').val();
    var gatefunc = $('#nodespace_gatefunction').val();
    if(gatefunc && (!(nodetype in nodespaces[currentNodeSpace].gatefunctions) || nodespaces[currentNodeSpace].gatefunctions[nodetype][gatename] != gatefunc)){
        if(!(nodetype in nodespaces[currentNodeSpace].gatefunctions)){
            nodespaces[currentNodeSpace].gatefunctions[nodetype] = {};
        }
        nodespaces[currentNodeSpace].gatefunctions[nodetype][gatename] = gatefunc;
        api.call('set_gate_function', {
            nodenet_uid: currentNodenet,
            nodespace: currentNodeSpace,
            node_type: nodetype,
            gate_type: gatename,
            gate_function: gatefunc
        }, api.defaultSuccessCallback, api.defaultErrorCallback, method="POST");
    }

}

function addSlotMonitor(node, index){
    api.call('add_slot_monitor', {
        nodenet_uid: currentNodenet,
        node_uid: node.uid,
        slot: node.slotIndexes[index]
    }, function(data){
        $(document).trigger('monitorsChanged', data);
        monitors[data] = {};
        setMonitorData(data);
    });
}

function addGateMonitor(node, index){
    api.call('add_gate_monitor', {
        nodenet_uid: currentNodenet,
        node_uid: node.uid,
        gate: node.gateIndexes[index]
    }, function(data){
        $(document).trigger('monitorsChanged', data);
        monitors[data] = {};
        setMonitorData(data);
    });
}

function setMonitorData(uid){
    api.call('export_monitor_data', params={
        'nodenet_uid': currentNodenet,
        'monitor_uid': uid
    }, function(data){
        monitors[uid] = data;
    })
}

function removeMonitor(node, target, type){
    monitor = getMonitor(node, target, type);
    api.call('remove_monitor', {
        nodenet_uid: currentNodenet,
        monitor_uid: monitor
    }, function(data){
        $(document).trigger('monitorsChanged');
        delete monitors[monitor];
    });
}


function followlink(event){
    event.preventDefault();
    var id = $(event.target).attr('data');
    deselectAll();
    selectLink(id);
    view.draw();
    clickOriginUid = id;
    showLinkForm(id);
}

function follownode(event){
    event.preventDefault();
    var id = $(event.target).attr('data');
    scrollToNode(nodes[id], true);
}

function scrollToNode(node, doShowNodeForm){
    var width = canvas_container.width();
    var height = canvas_container.height();
    var x = Math.max(0, node.x*viewProperties.zoomFactor-width/2);
    var y = Math.max(0, node.y*viewProperties.zoomFactor-height/2);
    if(isOutsideNodespace(node)){
        refreshNodespace(node.parent, {
            x: [0, canvas_container.width() * 2],
            y: [0, canvas_container.height() * 2]
        }, -1, function(){
            deselectAll();
            canvas_container.scrollTop(y);
            canvas_container.scrollLeft(x);
            selectNode(node.uid);
            view.draw();
            if(node.uid in nodes && doShowNodeForm) showNodeForm(node.uid);
        });
    } else {
        deselectAll();
        selectNode(node.uid);
        if(node.y*viewProperties.zoomFactor < canvas_container.scrollTop() ||
            node.y*viewProperties.zoomFactor > canvas_container.scrollTop() + height ||
            node.x*viewProperties.zoomFactor < canvas_container.scrollLeft() ||
            node.x*viewProperties.zoomFactor > canvas_container.scrollLeft() + width) {
            canvas_container.scrollTop(y);
            canvas_container.scrollLeft(x);
        }
        view.draw();
        if(doShowNodeForm) showNodeForm(node.uid);
    }
}

// function followslot(event){
//     event.preventDefault();
//     var slot = $(event.target).attr('data');
//     deselectAll();
//     selectLink(slot);
//     view.draw();
//     showLinkForm(id);
// }
function followgate(event){
    event.preventDefault();
    var node = nodes[$(event.target).attr('data-node')];
    var gate = node.gates[$(event.target).attr('data-gate')];
    deselectAll();
    if(!isCompact(node)){
        selectGate(node, gate);
        view.draw();
    } else {
        selectNode(node.uid);
    }
    scrollToNode(node, false)
    showGateForm(node, gate);
}

// sidebar editor forms ---------------------------------------------------------------

function initializeSidebarForms(){
    $('#edit_link_form').submit(handleEditLink);
    $('#edit_link_form .deleteLink').on('click', handleDeleteLink);
    $('#edit_node_form').submit(handleEditNode);
    $('#edit_gate_form').submit(handleEditGate);
    $('#edit_nodenet_form').submit(handleEditNodenet);
    $('#edit_nodespace_form').submit(handleEditNodespace);
    $('#native_module_form').submit(createNativeModuleHandler);
    $('#native_add_param').click(function(){
        $('#native_parameters').append('<tr><td><input name="param_name" type="text" class="inplace"/></td><td><input name="param_value" type="text"  class="inplace" /></td></tr>');
    });
    var world_selector = $("#nodenet_world");
    world_selector.on('change', function(){
        get_available_worldadapters(world_selector.val(), function(){
            $('#nodenet_worldadapter').val(nodenet_data.worldadapter);
        });
    });
    var nodespace_gatefunction_gate = $('#nodespace_gatefunction_gate');
    var nodespace_gatefunction_nodetype = $('#nodespace_gatefunction_nodetype');
    var nodespace_gatefunction = $('#nodespace_gatefunction');
    nodespace_gatefunction_gate.on('change', function(event){
        var value = '';
        var node = nodespace_gatefunction_nodetype.val();
        if(node in nodespaces[currentNodeSpace].gatefunctions){
            var gate = nodespace_gatefunction_gate.val();
            if(nodespaces[currentNodeSpace].gatefunctions[node][gate]){
                value = nodespaces[currentNodeSpace].gatefunctions[node][gate];
            }
        }
        nodespace_gatefunction.val(value);
    });
    nodespace_gatefunction_nodetype.on('change', function(event){
        var gatehtml = '';
        for(var idx in nodetypes[nodespace_gatefunction_nodetype.val()].gatetypes){
            gatehtml += '<option>' + nodetypes[nodespace_gatefunction_nodetype.val()].gatetypes[idx] + '</option>';
        }
        $('#nodespace_gatefunction_gate').html(gatehtml);
        nodespace_gatefunction_gate.trigger('change');
    });
}

function showLinkForm(linkUid){
    $('#nodenet_forms .form-horizontal').hide();
    $('#edit_link_form').show();
    $('#link_weight_input').val(links[linkUid].weight);
    $('#link_certainty_input').val(links[linkUid].certainty);
    $('.link_source_node').html(
        '<a href="#follownode" class="follownode" data="'+links[linkUid].sourceNodeUid+'">'+(nodes[links[linkUid].sourceNodeUid].name || nodes[links[linkUid].sourceNodeUid].uid.substr(0,8))+'</a> : ' +
        '<a href="#followgate" class="followgate" data-node="'+links[linkUid].sourceNodeUid+'" data-gate="'+links[linkUid].gateName+'">'+links[linkUid].gateName+'</a>'
    );
    $('.link_target_node').html(
        '<a href="#follownode" class="follownode" data="'+links[linkUid].targetNodeUid+'">'+(nodes[links[linkUid].targetNodeUid].name || nodes[links[linkUid].targetNodeUid].uid.substr(0,8))+'</a> : ' +
        links[linkUid].slotName
    );
    $('a.follownode').on('click', follownode);
    $('a.followgate').on('click', followgate);
}

function showNodeForm(nodeUid){
    $('#nodenet_forms .form-horizontal').hide();
    var form = $('#edit_node_form');
    form.show();
    $('#node_name_input', form).val(nodes[nodeUid].name);
    $('#node_uid_input', form).val(nodeUid);
    $('#node_type_input', form).val(nodes[nodeUid].type);
    if(nodes[nodeUid].type == 'Nodespace'){
        $('tr.node', form).hide();
        $('tr.comment', form).hide();
    } else if(nodes[nodeUid].type == "Comment"){
        $('tr.comment', form).show();
        $('tr.node', form).hide();
        $('#node_comment_input').val(nodes[nodeUid].parameters.comment || '');
    } else {
        $('tr.node', form).show();
        $('tr.comment', form).hide();
        $('#node_activation_input').val(nodes[nodeUid].sheaves[currentSheaf].activation);
        $('#node_parameters').html(getNodeParameterHTML(nodes[nodeUid].parameters, nodetypes[nodes[nodeUid].type].parameter_values));
        $('#node_datatarget').val(nodes[nodeUid].parameters['datatarget']);
        $('#node_datasource').val(nodes[nodeUid].parameters['datasource']);
        var states = '';
        if(!jQuery.isEmptyObject(nodetypes) && nodetypes[nodes[nodeUid].type].states){
            for(var i in nodetypes[nodes[nodeUid].type].states){
                states += '<option>'+nodetypes[nodes[nodeUid].type].states[i]+'</option>';
            }
        }
        var state_group = $('tr.state');
        if (states){
            states = '<option value="">None</option>' + states;
            $('#node_state_input').html(states).val(nodes[nodeUid].state);
            state_group.show();
        } else {
            state_group.hide();
        }
        var content = "", gates="", id, name, key;
        var link_list = "";
        var inlink_types = {};
        if(nodes[nodeUid].slotIndexes.length){
            for(key in nodes[nodeUid].slots){
                link_list += "<tr><td>" + key + "</td><td><ul>";
                for(id in nodes[nodeUid].slots[key].incoming){
                    link_list += '<li><a href="#followlink" data="'+id+'" class="followlink">&lt;-</a> &nbsp;<a href="#followNode" data="'+links[id].sourceNodeUid+'" class="follownode">'+(nodes[links[id].sourceNodeUid].name || nodes[links[id].sourceNodeUid].uid.substr(0,8)+'&hellip;')+':'+links[id].gateName+'</a></li>';
                }
            }
        }
        $('#node_slots').html(link_list || "<tr><td>None</td></tr>");
        content = "";
        for(name in nodes[nodeUid].gates){
            link_list = "";
            for(id in nodes[nodeUid].gates[name].outgoing){
                link_list += '<li><a href="#followlink" data="'+id+'" class="followlink">-&gt;</a> &nbsp;<a href="#followNode" data="'+links[id].targetNodeUid+'" class="follownode">'+(nodes[links[id].targetNodeUid].name || nodes[links[id].targetNodeUid].uid.substr(0,8)+'&hellip;')+'</a></li>';
            }
            content += '<tr><td><a href="#followgate" class="followgate" data-node="'+nodeUid+'" data-gate="'+name+'">'+name+'</td>';
            if(link_list){
                content += "<td><ul>"+link_list+"<ul></td>";
            }
            content += "</tr>";
        }
        $('#node_gates').html(content || "<tr><td>None</td></tr>");
        $('a.followlink').on('click', followlink);
        $('a.follownode').on('click', follownode);
        //$('a.followslot').on('click', followslot);
        $('a.followgate').on('click', followgate);
    }
}

function getNodeParameterHTML(parameters, parameter_values){
    var html = '<tr><td>None</td></tr>';
    var input='';
    var is_array = jQuery.isArray(parameters);
    if(parameters && !jQuery.isEmptyObject(parameters)) {
        html = '';
        for(var param in parameters){
            input = '';
            var name = (is_array) ? parameters[param] : param;
            var value = (is_array) ? '' : parameters[param];
            var i;
            switch(name){
                case "datatarget":
                    if(currentWorldadapter in worldadapters){
                        var opts = get_datatarget_options(currentWorldadapter, value);
                        input = "<select name=\"datatarget\" class=\"inplace\" id=\"node_datatarget\">"+opts+"</select>";
                    }
                    break;
                case "datasource":
                    if(currentWorldadapter in worldadapters){
                        var opts = get_datasource_options(currentWorldadapter, value);
                        input = "<select name=\"datasource\" class=\"inplace\" id=\"node_datasource\">"+opts+"</select>";
                    }
                    break;
                default:
                    if(parameter_values && parameter_values[name]){
                        input += '<option value="">None</option>';
                        for(i in parameter_values[name]){
                            input += "<option"+ (value == parameter_values[name][i] ? " selected=selected" : "") +">"+parameter_values[name][i]+"</option>";
                        }
                        input = "<select name=\""+name+"\" class=\"inplace\" id=\"node_"+name+"\">"+input+"</select>";
                    } else {
                        if(value == null) value = '';
                        input = "<input name=\""+name+"\" class=\"inplace\" value=\""+value+"\"/>";
                    }
            }
            html += "<tr><td>"+name+"</td><td>"+input+"</td></tr>";
        }
    }
    return html;
}

function showNativeModuleForm(nodeUid){
    $('#nodenet_forms .form-horizontal').hide();
    var form = $('#native_module_form');
    $('#nodenet_forms').append(form);
    form.show();
    //setNativeModuleFormValues(form, nodeUid);
}

function showDefaultForm(){
    $('#nodenet_forms .form-horizontal').hide();
    $('#nodenet_forms .default_form').show();
}

function showGateForm(node, gate){
    $('#nodenet_forms .form-horizontal').hide();
    var form = $('#edit_gate_form');
    $('.gate_nodetype', form).html('<strong>'+ node.type +'</strong>');
    $('.gate_gatetype', form).html('<strong>'+ gate.name +'</strong>');
    $.each($('input, select, textarea', form), function(index, el){
        el.value = '';
        if(el.name in gate.parameters){
            el.value = gate.parameters[el.name];
        } else if(el.name == 'gatefunction'){
            if(nodespaces[currentNodeSpace].gatefunctions && nodespaces[currentNodeSpace].gatefunctions[node.type]){
                el.value = nodespaces[currentNodeSpace].gatefunctions[node.type][gate.name] || '';
            }
        } else if(el.name == 'activation'){
            el.value = gate.sheaves[currentSheaf].activation || '0';
        } else if(nodetypes[node.type].gate_defaults && el.name in nodetypes[node.type].gate_defaults[gate.name]){
            el.value = nodetypes[node.type].gate_defaults[gate.name][el.name];
        }
    });
    form.show();
}

function updateNodespaceForm(){
    if(Object.keys(nodespaces).length){
        $('#nodespace_uid').val(currentNodeSpace);
        $('#nodespace_name').val(nodespaces[currentNodeSpace].name);
        if(currentNodeSpace == 'Root'){
            $('#nodespace_name').attr('disabled', 'disabled');
        } else {
            $('#nodespace_name').removeAttr('disabled');
        }
        var nodetypehtml = '';
        for(var idx in sorted_nodetypes){
            if(nodetypes[sorted_nodetypes[idx]].gatetypes && nodetypes[sorted_nodetypes[idx]].gatetypes.length > 0){
                nodetypehtml += '<option>' + sorted_nodetypes[idx] + '</option>';
            }
        }
        $('#nodespace_gatefunction_nodetype').html(nodetypehtml).trigger('change');
    }
}

function registerResizeHandler(){
    // resize handler for nodenet viewer:
    var isDragging = false;
    var container = $('.section.nodenet .editor_field');
    if($.cookie('nodenet_editor_height')){
        container.height($.cookie('nodenet_editor_height'));
        try{
            updateViewSize();
        } catch(err){}
    }
    var startHeight, startPos, newHeight;
    $("a#nodenetSizeHandle").mousedown(function(event) {
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
            $.cookie('nodenet_editor_height', container.height(), {expires:7, path:'/'});
        }
        isDragging = false;
        $(window).unbind("mousemove");
    });
}

function promptUser(data){
    var html = '';
    html += '<p>Nodenet interrupted by Node ' + (data.node.name || data.node.uid) +' with message:</p>';
    html += "<p>" + data.msg +"</p>";
    html += '<form class="well form-horizontal">';
    if (data.options){
        for(var idx in data.options){
            var item = data.options[idx];
            html += '<div class="control-group"><label class="control-label">' + item.label + '</label>';
            if(item.values && typeof item.values == 'object'){
                html += '<div class="controls"><select name="'+item.key+'">';
                for(var val in item.values){
                    if(item.values instanceof Array){
                        html += '<option>'+item.values[val]+'</option>';
                    } else {
                        html += '<option value="'+val+'">'+item.values[val]+'</option>';
                    }
                }
                html += '</select></div></div>';
            } else {
                html += '<div class="controls"><input name="'+item.key+'" value="'+(item.values || '')+'" /></div></div>';
            }
        }
    }
    html += '<div class="control-group"><label class="control-label">Continue running nodenet?</label>';
    html += '<div class="controls"><input type="checkbox" name="run_nodenet"/></div></div>';
    html += '<input class="hidden" id="user_prompt_node_uid" value="'+data.node.uid+'" />';
    html += '</form>';
    $('#nodenet_user_prompt .modal-body').html(html);
    $('#nodenet_user_prompt').modal("show");
}


// hack. credits: http://stackoverflow.com/a/19743610
// this is a workaround, until paper.js supports AreaText
// (--> see https://groups.google.com/forum/#!topic/paperjs/PvvRV0hkC94)
function ApplyLineBreaks(strTextAreaId) {
    var oTextarea = document.getElementById(strTextAreaId);
    if (oTextarea.wrap) {
        oTextarea.setAttribute("wrap", "off");
    }
    else {
        oTextarea.setAttribute("wrap", "off");
        var newArea = oTextarea.cloneNode(true);
        newArea.value = oTextarea.value;
        oTextarea.parentNode.replaceChild(newArea, oTextarea);
        oTextarea = newArea;
    }

    var strRawValue = oTextarea.value;
    oTextarea.value = "";
    var nEmptyWidth = oTextarea.scrollWidth;

    function testBreak(strTest) {
        oTextarea.value = strTest;
        return oTextarea.scrollWidth > nEmptyWidth;
    }
    function findNextBreakLength(strSource, nLeft, nRight) {
        var nCurrent;
        if(typeof(nLeft) == 'undefined') {
            nLeft = 0;
            nRight = -1;
            nCurrent = 64;
        }
        else {
            if (nRight == -1)
                nCurrent = nLeft * 2;
            else if (nRight - nLeft <= 1)
                return Math.max(2, nRight);
            else
                nCurrent = nLeft + (nRight - nLeft) / 2;
        }
        var strTest = strSource.substr(0, nCurrent);
        var bLonger = testBreak(strTest);
        if(bLonger)
            nRight = nCurrent;
        else
        {
            if(nCurrent >= strSource.length)
                return null;
            nLeft = nCurrent;
        }
        return findNextBreakLength(strSource, nLeft, nRight);
    }

    var i = 0, j;
    var strNewValue = "";
    while (i < strRawValue.length) {
        var breakOffset = findNextBreakLength(strRawValue.substr(i));
        if (breakOffset === null) {
            strNewValue += strRawValue.substr(i);
            break;
        }
        var nLineLength = breakOffset - 1;
        for (j = nLineLength - 1; j >= 0; j--) {
            var curChar = strRawValue.charAt(i + j);
            if (curChar == ' ' || curChar == '-' || curChar == '+') {
                nLineLength = j + 1;
                break;
            }
        }
        strNewValue += strRawValue.substr(i, nLineLength) + "\n";
        i += nLineLength;
    }
    oTextarea.value = strNewValue;
    oTextarea.setAttribute("wrap", "");
}

var drawGridLines = function(element) {
    gridLayer.removeChildren();
    if(nodenet_data.snap_to_grid){
        var size = 20 //* viewProperties.zoomFactor; //boundingRect.width / num_rectangles_wide;
        for (var i = 0; i <= element.width/size; i++) {
            var xPos = i * size;
            var topPoint = new paper.Point(xPos, 0);
            var bottomPoint = new paper.Point(xPos, element.height);
            var aLine = new paper.Path.Line(topPoint, bottomPoint);
            aLine.strokeColor = 'black';
            aLine.strokeWidth = 0.1;
            aLine.opacity = 0.3;
            gridLayer.addChild(aLine);
        }
        for (var i = 0; i <= element.height/size; i++) {
            var yPos = i * size;
            var leftPoint = new paper.Point(0, yPos);
            var rightPoint = new paper.Point(element.width, yPos);
            var aLine = new paper.Path.Line(leftPoint, rightPoint);
            aLine.strokeColor = 'black';
            aLine.strokeWidth = 0.1;
            aLine.opacity = 0.3;
            gridLayer.addChild(aLine);
        }
    }
}


/* todo:

 - get diffs
 - handle connection problems
 - multiple viewports
 - exporting and importing with own dialogs
 - edit native modules
 */
