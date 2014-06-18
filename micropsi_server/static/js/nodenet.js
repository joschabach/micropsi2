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
    xMax: 13500
};

var nodenetscope = paper;

// hashes from uids to object definitions; we import these via json
nodes = {};
links = {};
selection = {};
gatefunctions = {};
monitors = {};

linkLayer = new Layer();
linkLayer.name = 'LinkLayer';
nodeLayer = new Layer();
nodeLayer.name = 'NodeLayer';
prerenderLayer = new Layer();
prerenderLayer.name = 'PrerenderLayer';
prerenderLayer.visible = false;

viewProperties.zoomFactor = parseFloat($.cookie('zoom_factor')) || viewProperties.zoomFactor;

currentNodenet = $.cookie('selected_nodenet') || null;
currentNodeSpace = $.cookie('current_nodespace') || 'Root';

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
            setCurrentNodenet(uid);
        });
    });
}

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
    if (!jQuery.isEmptyObject(worldadapters)) {
        var worldadapter_select = $('#nodenet_worldadapter');
        worldadapter_select.val(data.worldadapter);
        if(worldadapter_select.val() != data.worldadapter){
            dialogs.notification("The worldadapter of this nodenet is not compatible to the world. Please choose a worldadapter from the list", 'Error');
        }
    }
}

function setCurrentNodenet(uid, nodespace){
    if(!nodespace){
        nodespace = "Root";
    }
    api.call('load_nodenet',
        {nodenet_uid: uid,
            nodespace: nodespace,
            x1: loaded_coordinates.x[0],
            x2: loaded_coordinates.x[1],
            y1: loaded_coordinates.y[0],
            y2: loaded_coordinates.y[1]},
        function(data){
            nodenetscope.activate();
            toggleButtons(true);

            var nodenetChanged = (uid != currentNodenet);
            var nodespaceChanged = (nodespace != currentNodeSpace);

            nodenet_data = data;

            showDefaultForm();
            $('#nodenet_step').val(data.step);
            currentNodeSpace = data['nodespace'];
            currentNodenet = uid;

            nodes = {};
            links = {};
            nodeLayer.removeChildren();
            addNode(rootNode);
            linkLayer.removeChildren();

            $.cookie('selected_nodenet', uid, { expires: 7, path: '/' });
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
        },
        function(data) {
            currentNodenet = null;
            $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
            dialogs.notification(data.Error, "Error");
        });
}

function getNodespaceList(){
    api.call('get_nodespace_list', {nodenet_uid:currentNodenet}, function(nodespacedata){
        nodespaces = nodespacedata;
        html = '';
        for(var uid in nodespaces){
            html += '<li><a href="#" data-nodespace="'+uid+'">'+nodespaces[uid].name+'</a></li>';
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
        currentSimulationStep = data.step || 0;
        $('#nodenet_step').val(currentSimulationStep);
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

        if(data.monitors){
            monitors = data.monitors;
        }
        updateMonitorList();
        updateMonitorGraphs();
        if(changed){
            updateNodespaceForm();
        }
    }
    updateViewSize();
}

function refreshNodespace(nodespace, coordinates, step, callback){
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
    params.x1 = parseInt(coordinates.x[0]);
    params.x2 = parseInt(coordinates.x[1]);
    params.y1 = parseInt(coordinates.y[0]);
    params.y2 = parseInt(coordinates.y[1]);
    api.call('get_nodespace', params , success=function(data){
        var changed = nodespace != currentNodeSpace;
        if(changed){
            currentNodeSpace = nodespace;
            $.cookie('current_nodespace', nodespace, { expires: 7, path: '/' });
            $("#current_nodespace_name").text(nodespaces[nodespace].name);
            nodeLayer.removeChildren();
            linkLayer.removeChildren();
        }
        loaded_coordinates = coordinates;
        if(jQuery.isEmptyObject(data)){
            if(nodenetRunning) setTimeout(refreshNodespace, 100);
            return null;
        } else {
            nodenetRunning = data.is_active
        }
        setNodespaceData(data, changed);
        if(callback){
            callback(data);
        }
        if(nodenetRunning){
            refreshNodespace();
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
        refreshNodespace(currentNodeSpace, {
            x:[Math.max(0, left - width), left + 2*width],
            y:[Math.max(0, top-height), top + 2*height]
        }, currentSimulationStep - 1);
    }
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

            if(nodetypes[type].gate_defaults) {
                parameters = nodetypes[type].gate_defaults[nodetypes[type].gatetypes[i]];
            } else {
                // mh. evil. where should this be defined?
                parameters = {
                    "minimum": -1,
                    "maximum": 1,
                    "certainty": 1,
                    "amplification": 1,
                    "threshold": 0,
                    "decay": 0
                };
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
        if(!gate || !slot){
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
}

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
    if(node.parent == currentNodeSpace && (direction == 'in' && node.linksFromOutside.length > 0) || (direction == 'out' && node.linksToOutside.length > 0)){
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
function renderLink(link) {
    var sourceNode = nodes[link.sourceNodeUid];
    var targetNode = nodes[link.targetNodeUid];
    var gate;
    if(sourceNode){
        gate = sourceNode.gates[link.gateName];
    } else {
        gate = {
            activation: link.weight,
            name: link.gateName
        };
    }

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
    link.strokeColor = activationColor(gate.sheaves[currentSheaf].activation * link.weight, viewProperties.linkColor);

    var startDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkStart.angle);
    var endDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkEnd.angle);

    var arrowPath = createArrow(linkEnd.point, endDirection.angle, link.strokeColor);
    var linkPath = createLink(linkStart.point, linkStart.angle, startDirection, linkEnd.point, linkEnd.angle, endDirection, link.strokeColor, link.strokeWidth, gate.name);

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

// draw link during creation
function renderLinkDuringCreation(endPoint) {
    var sourceNode = linkCreationStart.sourceNode;
    var gateIndex = linkCreationStart.gateIndex;

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

    if ("tempLink" in nodeLayer.children) nodeLayer.children["tempLink"].remove();
    nodeLayer.addChild(tempLink);
}

// draw net entity
function renderNode(node) {
    if (isCompact(node)) renderCompactNode(node);
    else renderFullNode(node);
    setActivation(node);
    if(node.uid in selection){
        selectNode(node.uid);
    }
    node.zoomFactor = viewProperties.zoomFactor;
}

// draw net entity with slots and gates
function renderFullNode(node) {
    node.bounds = calculateNodeBounds(node);
    var skeleton = createFullNodeSkeleton(node);
    var activations = createFullNodeActivations(node);
    var titleBar = createFullNodeLabel(node);
    var sheavesAnnotation = createSheavesAnnotation(node);
    var nodeItem = new Group([activations, skeleton, titleBar, sheavesAnnotation]);
    nodeItem.name = node.uid;
    nodeItem.isCompact = false;
    nodeLayer.addChild(nodeItem);
}

// render compact version of a net entity
function renderCompactNode(node) {
    node.bounds = calculateNodeBounds(node);
    var skeleton = createCompactNodeSkeleton(node);
    var activations = createCompactNodeActivations(node);
    var label = createCompactNodeLabel(node);
    var nodeItem = new Group([activations, skeleton]);
    if (label) nodeItem.addChild(label);
    nodeItem.name = node.uid;
    nodeItem.isCompact = true;
    nodeLayer.addChild(nodeItem);
}

// calculate the dimensions of a node in the current rendering
function calculateNodeBounds(node) {
    var width, height;
    if (!isCompact(node)) {
        width = viewProperties.nodeWidth * viewProperties.zoomFactor;
        height = viewProperties.lineHeight*(Math.max(node.slotIndexes.length, node.gateIndexes.length)+2)*viewProperties.zoomFactor;
        if (node.type == "Nodespace") height = Math.max(height, viewProperties.lineHeight*4*viewProperties.zoomFactor);
    } else {
        width = height = viewProperties.compactNodeWidth * viewProperties.zoomFactor;
    }
    return new Rectangle(node.x*viewProperties.zoomFactor - width/2,
        node.y*viewProperties.zoomFactor - height/2, // center node on origin
        width, height);
}

// determine shape of a full node
function createFullNodeShape(node) {
    if (node.type == "Nodespace") return new Path.Rectangle(node.bounds);
    else return new Path.RoundRectangle(node.bounds, viewProperties.cornerWidth*viewProperties.zoomFactor);
}

// determine shape of a compact node
function createCompactNodeShape(node) {
    var bounds = node.bounds;
    var shape;
    switch (node.type) {
        case "Nodespace":
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
                new Point(bounds.x+bounds.width * 0.35, bounds.y),
                bounds.bottomLeft
            ]);
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
    } else console.log ("node "+node.uid+" not found in current view");
}

// mark node as selected, and add it to the selected nodes
function selectNode(nodeUid) {
    selection[nodeUid] = nodes[nodeUid];
    var outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
    outline.strokeColor = viewProperties.selectionColor;
    outline.strokeWidth = viewProperties.outlineWidthSelected*viewProperties.zoomFactor;
}

// remove selection marking of node, and remove if from the set of selected nodes
function deselectNode(nodeUid) {
    if (nodeUid in selection) {
        delete selection[nodeUid];
        if(nodeUid in nodeLayer.children){
            var outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
            outline.strokeColor = null;
            outline.strokeWidth = viewProperties.outlineWidth;
        }
    }
}

// mark node as selected, and add it to the selected nodes
function selectLink(linkUid) {
    selection[linkUid] = links[linkUid];
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
        var linkShape = linkLayer.children[linkUid].children["link"];
        linkShape.children["line"].strokeColor = links[linkUid].strokeColor;
        linkShape.children["line"].strokeWidth = links[linkUid].strokeWidth*viewProperties.zoomFactor;
        linkShape.children["arrow"].fillColor = links[linkUid].strokeColor;
        linkShape.children["arrow"].strokeWidth = 0;
        linkShape.children["arrow"].strokeColor = null;
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

function onMouseDown(event) {
    path = hoverPath = null;
    var p = event.point;
    dragMultiples = Object.keys(selection).length > 1;
    var clickedSelected = false;
    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    function deselectOtherNodes(nodeUid){
        for(var key in selection){
            if(key != node.uid && selection[key].constructor == Node){
                deselectNode(key);
            }
        }
    }
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
                     !event.modifiers.control && !event.modifiers.command && event.event.button != 2) {
                         deselectAll();
                }
                if (event.modifiers.command && nodeUid in selection){
                    deselectNode(nodeUid); // toggle
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
                    if (event.modifiers.control || event.event.button == 2){
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
                    deselectGate();
                    selectGate(node, gate);
                    showGateForm(node, gate);
                    if (event.modifiers.control || event.event.button == 2) {
                        deselectOtherNodes(node.uid);
                        var monitor = getMonitor(node, node.gateIndexes[clickIndex], 'gate');
                        $('#gate_menu [data-add-monitor]').toggle(monitor == false);
                        $('#gate_menu [data-remove-monitor]').toggle(monitor != false);
                        openContextMenu("#gate_menu", event.event);
                    }
                    return;
                }
                clickType = "node";
                if (event.modifiers.control || event.event.button == 2) {
                    deselectOtherNodes(nodeUid);
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
        cancelLinkCreationHandler();
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
        if (event.modifiers.control || event.event.button == 2) openContextMenu("#create_node_menu", event.event);
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
                if (event.modifiers.control || event.event.button == 2) openContextMenu("#link_menu", event.event);
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
                    hoverNode.renderCompact = null;
                    redrawNode(hoverNode, true);
                }
                hover = nodeLayer.children[nodeUid].children["activation"].children["body"];
                // check for slots and gates
                if ((i = testSlots(node, p)) >-1) {
                    hover = nodeLayer.children[nodeUid].children["activation"].children["slots"].children[i];
                } else if ((i = testGates(node, p)) > -1) {
                    hover = nodeLayer.children[nodeUid].children["activation"].children["gates"].children[i];
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
        hoverNode.renderCompact = null;
        redrawNode(hoverNode, true);
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
    function moveNode(uid){
        var canvas = $('#nodenet');
        var pos = canvas.offset();
        if(event.event.clientX < pos.left || event.event.clientY < pos.top) return false;
        nodeLayer.children[uid].position += event.delta;
        nodeLayer.children[uid].nodeMoved = true;
        var node = nodes[uid];
        node.x += event.delta.x/viewProperties.zoomFactor;
        node.y += event.delta.y/viewProperties.zoomFactor;
        node.bounds = calculateNodeBounds(node);
        redrawNodeLinks(node);
    }
    if (movePath) {
        if(dragMultiples){
            for(var uid in selection){
                if(uid in nodes){
                    moveNode(uid);
                }
            }
        } else {
            moveNode(path.name);
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
    if (event.character == "+" && event.event.target.tagName == "BODY") {
        zoomIn(event);
    }
    else if (event.character == "-" && event.event.target.tagName == "BODY") {
        zoomOut(event);
    }
    // delete nodes and links
    else if (event.key == "backspace" || event.key == "delete") {
        if (event.event.target.tagName == "BODY") {
            event.preventDefault(); // browser-back
            deleteNodeHandler();
            deleteLinkHandler();
        }
    }
    else if (event.key == "escape") {
        if (linkCreationStart) cancelLinkCreationHandler();
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
    $('#nodenet_start').on('click', startNodenetrunner);
    $('#nodenet_stop').on('click', stopNodenetrunner);
    $('#nodenet_reset').on('click', resetNodenet);
    $('#nodenet_step_forward').on('click', stepNodenet);
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
            for(var nid in ns.nodes){
                html += '<option value="'+nid+'">'+ns.nodes[nid].name + '('+ns.nodes[nid].type+')</option>';
            }
            target_node.html(html);
            target_node.trigger('change');
        }
    });
    target_node.on('change', function(event){
        var node = nodespaces[target_nodespace.val()].nodes[target_node.val()];
        if(node){
            var html = '';
            for(var i in node.slots){
                html += '<option value="'+node.slots[i]+'">'+node.slots[i]+'</option>';
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
}

function stepNodenet(event){
    event.preventDefault();
    if(nodenetRunning){
        stopNodenetrunner(event);
    }
    if(currentNodenet){
        api.call("step_nodenet",
            {nodenet_uid: currentNodenet, nodespace:currentNodeSpace},
            success=function(data){
                refreshNodespace();
                dialogs.notification("Nodenet stepped", "success");
            });
    } else {
        dialogs.notification('No nodenet selected', 'error');
    }
}

function startNodenetrunner(event){
    event.preventDefault();
    nodenetRunning = true;
    if(currentNodenet){
        api.call('start_nodenetrunner', {nodenet_uid: currentNodenet}, function(){
            refreshNodespace();
        });
    } else {
        dialogs.notification('No nodenet selected', 'error');
    }
}
function stopNodenetrunner(event){
    event.preventDefault();
    api.call('stop_nodenetrunner', {nodenet_uid: currentNodenet}, function(){ nodenetRunning = false; });
}

function resetNodenet(event){
    event.preventDefault();
    nodenetRunning = false;
    if(currentNodenet){
        api.call(
            'revert_nodenet',
            {nodenet_uid: currentNodenet},
            function(){
                setCurrentNodenet(currentNodenet);
            }
        );
    } else {
        dialogs.notification('No nodenet selected', 'error');
    }
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
                for(key in native_modules){
                    html += '<li><a data-create-node="' + key + '">Create '+ key +' Node</a></li>';
                }
                html += '</ul></li>';
            }
        }
        html += '<li class="divider"></li><li><a data-auto-align="true">Autoalign Nodes</a></li>';
        list.html(html);
    }
    $(menu_id+" .dropdown-toggle").dropdown("toggle");
}

// build the node menu
function openNodeContextMenu(menu_id, event, nodeUid) {
    var menu = $(menu_id+" .dropdown-menu");
    menu.off('click', 'li');
    menu.empty();
    var node = nodes[nodeUid];
    menu.append('<li class="divider"></li>');
    if (node.gateIndexes.length) {
        for (var gateName in node.gates) {
            if(gateName in inverse_link_map){
                var compound = gateName+'/'+inverse_link_map[gateName];
                menu.append('<li><a data-link-type="'+compound+'">Draw '+compound+' link</a></li>');
            } else if(inverse_link_targets.indexOf(gateName) == -1){
                menu.append('<li><a href="#" data-link-type="'+gateName+'">Draw '+gateName+' link</a></li>');
            }
        }
        menu.append('<li><a href="#" data-link-type="">Create link</a></li>');
        menu.append('<li class="divider"></li>');
    }
    if(node.type == "Sensor"){
        menu.append('<li><a href="#">Select datasource</li>');
    }
    if(node.type == "Actor"){
        menu.append('<li><a href="#">Select datatarget</li>');
    }
    menu.append('<li><a href="#">Rename node</a></li>');
    menu.append('<li><a href="#">Delete node</a></li>');
    menu.on('click', 'li', handleContextMenu);
    openContextMenu(menu_id, event);
}

// universal handler for all context menu events. You can get the origin path from the variable clickTarget.
function handleContextMenu(event) {
    event.preventDefault();
    var menuText = event.target.text;
    $el = $(event.target);
    switch (clickType) {
        case null: // create nodes
            var type = $el.attr("data-create-node");
            var autoalign = $el.attr("data-auto-align");
            if(!type && !autoalign){
                return false;
            }
            var callback = function(data){
                dialogs.notification('Node created', 'success');
            };

            switch (type) {
                case "Sensor":
                    callback = function(data){
                        clickOriginUid = data.uid;
                        dialogs.notification('Please Select a datasource for this sensor');
                        var source_select = $('#select_datasource_modal select');
                        source_select.html('');
                        $("#select_datasource_modal").modal("show");
                        var sources = worldadapters[currentWorldadapter].datasources;
                        for(var i in sources){
                            source_select.append($('<option>', {value:sources[i]}).text(sources[i]));
                        }
                        source_select.val(nodes[clickOriginUid].parameters['datasource']).select().focus();
                    };
                    break;
                case "Actor":
                    callback = function(data){
                        clickOriginUid = data.uid;
                        dialogs.notification('Please Select a datatarget for this actor');
                        var target_select = $('#select_datatarget_modal select');
                        target_select.html('');
                        $("#select_datatarget_modal").modal("show");
                        var targets = worldadapters[currentWorldadapter].datatargets;
                        for(var i in targets){
                            target_select.append($('<option>', {value:targets[i]}).text(targets[i]));
                        }
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
                    createNodeHandler(clickPosition.x/viewProperties.zoomFactor,
                        clickPosition.y/viewProperties.zoomFactor,
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
                    var sources = worldadapters[currentWorldadapter].datasources;
                    for(var i in sources){
                        source_select.append($('<option>', {value:sources[i]}).text(sources[i]));
                    }
                    source_select.val(nodes[clickOriginUid].parameters['datasource']).select().focus();
                    break;
                case "Select datatarget":
                    var target_select = $('#select_datatarget_modal select');
                    $("#select_datatarget_modal").modal("show");
                    target_select.html('');
                    var datatargets = worldadapters[currentWorldadapter].datatargets;
                    for(var j in datatargets){
                        target_select.append($('<option>', {value:datatargets[j]}).text(datatargets[j]));
                    }
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
                        $("#link_target_node").html('');
                        $('#link_target_slot').html('');
                        var html = '';
                        for(var key in nodespaces){
                            html += '<option value="'+key+'">'+nodespaces[key].name+'</option>';
                        }
                        $('#link_target_nodespace').html(html);
                        html = '';
                        for(var g in nodes[path.name].gates){
                            html += '<option value="'+g+'">'+g+'</option>';
                        }
                        $("#link_source_gate").html(html);
                        $('#link_target_nodespace').trigger('change');
                        $("#create_link_modal").modal("show");
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
    var uid = makeUuid();
    params = {};
    if (!parameters) parameters = {};
    if (nodetypes[type]){
        for (var i in nodetypes[type].parameters){
            params[nodetypes[type].parameters[i]] = parameters[nodetypes[type].parameters[i]] || "";
        }
    }
    addNode(new Node(uid, x, y, currentNodeSpace, name, type, null, null, params));
    view.draw();
    selectNode(uid);
    api.call("add_node", {
        nodenet_uid: currentNodenet,
        type: type,
        pos: [x,y],
        nodespace: currentNodeSpace,
        uid: uid,
        name: name,
        parameters: params },
        success=function(data){
            if(callback) callback(data);
            showNodeForm(uid);
            getNodespaceList();
        });
    return uid;
}


function createNativeModuleHandler(event){

    var modal = $("#edit_native_modal");
    if(event){
        createNodeHandler(clickPosition.x/viewProperties.zoomFactor,
                        clickPosition.y/viewProperties.zoomFactor,
                        $('#native_module_name').val(),
                        $('#native_module_type').val(),
                        {}, null);
        modal.modal("hide");
    } else {
        var html = '';
        for(var key in native_modules){
            html += '<option>'+ key +'</option>';
        }
        $('[data-native-module-type]', modal).html(html);
        $('#native_module_name').val('');
        modal.modal("show");
    }
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
            {nodenet_uid:currentNodenet, link_uid:linkUid},
            success= function(data){
                dialogs.notification('Link removed', 'success');
            }
        );
    }
    if (linkUid in links) {
        removeLink(links[linkUid]);
        if (linkUid in selection) delete selection[linkUid];
        removeLinkOnServer(linkUid);
    }
    for (var selected in selection) {
        if(selection[selected].constructor == Link){
            removeLink(links[selected]);
            delete selection[selected];
            removeLinkOnServer(selected);
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
        link_uid: linkUid,
        weight: weight,
        certainty: certainty
    });
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
        linkCreationStart = {
            sourceNode: nodes[nodeUid],
            gateIndex: gateIndex, // if no gate give, assume gen gate
            creationType: creationType
        };
    }
}

function createLinkFromDialog(sourceUid, sourceGate, targetUid, targetSlot){
    if ((sourceUid in nodes)) {

        var uuid = makeUuid();
        if(!(targetUid in nodes)){
            nodes[sourceUid].linksToOutside.push(uuid);
        } else if(nodes[targetUid].parent != currentNodeSpace){
            nodes[sourceUid].linksToOutside.push(uuid);
            nodes[targetUid].linksFromOutside.push(uuid);
        }
        addLink(new Link(uuid, sourceUid, sourceGate, targetUid, targetSlot, 1, 1));
        // TODO: also write backwards link??
        api.call("add_link", {
            nodenet_uid: currentNodenet,
            source_node_uid: sourceUid,
            gate_type: sourceGate,
            target_node_uid: targetUid,
            slot_type: targetSlot,
            weight: 1,
            uid: uuid
        });
    }
}


// establish the created link
function finalizeLinkHandler(nodeUid, slotIndex) {
    var sourceUid = linkCreationStart.sourceNode.uid;
    var targetUid = nodeUid;
    var gateIndex = linkCreationStart.gateIndex;

    if (!slotIndex || slotIndex < 0) slotIndex = 0;

    if ((targetUid in nodes) &&
        nodes[targetUid].slots && (nodes[targetUid].slotIndexes.length > slotIndex)) {

        var targetGates = nodes[targetUid].gates ? nodes[targetUid].gateIndexes.length : 0;
        var targetSlots = nodes[targetUid].slots ? nodes[targetUid].slotIndexes.length : 0;
        var sourceSlots = nodes[sourceUid].slots ? nodes[sourceUid].slotIndexes.length : 0;

        var newlinks = [];

        switch (linkCreationStart.creationType) {
            case "por/ret":
                // the por link
                if (targetSlots > 2) {
                    newlinks.push(createLinkIfNotExists(sourceUid, "por", targetUid, "por", 1, 1));
                } else {
                    newlinks.push(createLinkIfNotExists(sourceUid, "por", targetUid, "gen", 1, 1));
                }
                // the ret link
                if (targetGates > 2) {
                    if(sourceSlots > 2) {
                        newlinks.push(createLinkIfNotExists(targetUid, "ret", sourceUid, "ret", 1, 1));
                    } else {
                        newlinks.push(createLinkIfNotExists(targetUid, "ret", sourceUid, "gen", 1, 1));
                    }
                }
                break;
            case "sub/sur":
                // the sub link
                if (targetSlots > 4) {
                    newlinks.push(createLinkIfNotExists(sourceUid, "sub", targetUid, "sub", 1, 1));
                } else {
                    newlinks.push(createLinkIfNotExists(sourceUid, "sub", targetUid, "gen", 1, 1));
                }
                // the sur link
                if (targetGates > 4) {
                    if(sourceSlots > 4) {
                        newlinks.push(createLinkIfNotExists(targetUid, "sur", sourceUid, "sur", 1, 1));
                    } else {
                        newlinks.push(createLinkIfNotExists(targetUid, "sur", sourceUid, "gen", 1, 1));
                    }
                }
                break;
            case "cat/exp":
                // the cat link
                if (targetSlots > 6) {
                    newlinks.push(createLinkIfNotExists(sourceUid, "cat", targetUid, "cat", 1, 1));
                } else {
                    newlinks.push(createLinkIfNotExists(sourceUid, "cat", targetUid, "gen", 1, 1));
                }
                // the exp link
                if (targetGates > 6) {
                    if(sourceSlots > 6) {
                        newlinks.push(createLinkIfNotExists(targetUid, "cat", sourceUid, "cat", 1, 1));
                    } else {
                        newlinks.push(createLinkIfNotExists(targetUid, "exp", sourceUid, "gen", 1, 1));
                    }
                }
                break;
            default:
                newlinks.push(createLinkIfNotExists(sourceUid, nodes[sourceUid].gateIndexes[gateIndex], targetUid, nodes[targetUid].slotIndexes[slotIndex], 1, 1));
        }

        for (i=0;i<newlinks.length;i++) {

            var link = newlinks[i];
            if(link){
                addLink(link);
                if(nodes[link.sourceNodeUid].parent != currentNodeSpace){
                    nodes[link.targetNodeUid].linksFromOutside.push(link.uid);
                    nodes[link.sourceNodeUid].linksToOutside.push(link.uid);
                }

                api.call("add_link", {
                    nodenet_uid: currentNodenet,
                    source_node_uid: link.sourceNodeUid,
                    gate_type: link.gateName,
                    target_node_uid: link.targetNodeUid,
                    slot_type: link.slotName,
                    weight: link.weight,
                    uid: link.uid
                });
            }
        }

        cancelLinkCreationHandler();
    }
}

function createLinkIfNotExists(sourceUid, sourceGate, targetUid, targetSlot, weight, certainty){
    for(var uid in nodes[sourceUid].gates[sourceGate].outgoing){
        var link = nodes[sourceUid].gates[sourceGate].outgoing[uid];
        if(link.targetNodeUid == targetUid && link.slotName == targetSlot){
            return false;
        }
    }
    var newlink = new Link(makeUuid(), sourceUid, sourceGate, targetUid, targetSlot, weight || 1, certainty || 1);
    return newlink;
}

// cancel link creation
function cancelLinkCreationHandler() {
    if ("tempLink" in nodeLayer.children) nodeLayer.children["tempLink"].remove();
    linkCreationStart = null;
}

function moveNode(nodeUid, x, y){
    api.call("set_node_position", {
        nodenet_uid: currentNodenet,
        node_uid: nodeUid,
        pos: [x,y]});
}

function handleEditNode(event){
    event.preventDefault();
    form = $(event.target);
    var nodeUid = $('#node_uid_input').val();
    if($(".modal")) $(".modal").modal("hide");
    var parameters = {};
    var fields = form.serializeArray();
    var name = null;
    var state = null;
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
        }
    }
    if(name && nodes[nodeUid].name != name){
        renameNode(nodeUid, name);
    }
    if(!jQuery.isEmptyObject(parameters)){
        updateNodeParameters(nodeUid, parameters);
    }
    if(nodes[nodeUid].state != state){
        setNodeState(nodeUid, state);
    }
    if(nodes[nodeUid].sheaves[currentSheaf].activation != activation){
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
    var data = $(event.target).serializeArray();
    var params = {};
    for(var i in data){
        params[data[i].name] = parseFloat(data[i].value);
    }
    api.call('set_gate_parameters', {
        nodenet_uid: currentNodenet,
        node_uid: node.uid,
        gate_type: gate.name,
        parameters: params
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
    });
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
    var params = {
        nodenet_uid: currentNodenet,
        nodenet_name: $('#nodenet_name', form).val()
    };
    var nodenet_world = $('#nodenet_world', form).val();
    if(nodenet_world){
        params.world_uid = nodenet_world;
    }
    var worldadapter = $('#nodenet_worldadapter', form).val();
    if(worldadapter){
        params.worldadapter = worldadapter;
    }
    api.call("set_nodenet_properties", params,
        success=function(data){
            dialogs.notification('Nodenet data saved', 'success');
            setCurrentNodenet(currentNodenet);
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
    if(gatefunc && (!(nodetype in nodespaces.gatefunctions) || nodespaces.gatefunctions[nodetype][gatename] != gatefunc)){
        if(!(nodetype in nodespaces.gatefunctions)){
            nodespaces.gatefunctions[nodetype] = {};
        }
        nodespaces.gatefunctions[nodetype][gatename] = gatefunc;
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
        monitors[data.uid] = data;
        updateMonitorList();
    });
}

function addGateMonitor(node, index){
    api.call('add_gate_monitor', {
        nodenet_uid: currentNodenet,
        node_uid: node.uid,
        gate: node.gateIndexes[index]
    }, function(data){
        monitors[data.uid] = data;
        updateMonitorList();
    });
}

function removeMonitor(node, target, type){
    monitor = getMonitor(node, target, type);
    api.call('remove_monitor', {
        nodenet_uid: currentNodenet,
        monitor_uid: monitor
    }, function(data){
        delete monitors[monitor];
        updateMonitorList();
    });
}

function makeUuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    }); // todo: replace with a uuid fetched from server
}


function followlink(event){
    event.preventDefault();
    var id = $(event.target).attr('data');
    deselectAll();
    selectLink(id);
    view.draw();
    showLinkForm(id);
}

function follownode(event){
    event.preventDefault();
    var id = $(event.target).attr('data');
    var width = canvas_container.width();
    var height = canvas_container.height();
    var x = Math.max(0, nodes[id].x*viewProperties.zoomFactor-width/2);
    var y = Math.max(0, nodes[id].y*viewProperties.zoomFactor-height/2);
    if(isOutsideNodespace(nodes[id])){
        refreshNodespace(nodes[id].parent, {
            x: [0, canvas_container.width() * 2],
            y: [0, canvas_container.height() * 2]
        }, -1, function(){
            deselectAll();
            canvas_container.scrollTop(y);
            canvas_container.scrollLeft(x);
            selectNode(id);
            view.draw();
            showNodeForm(id);
        });
    } else {
        deselectAll();
        selectNode(id);
        if(nodes[id].y*viewProperties.zoomFactor < canvas_container.scrollTop() ||
            nodes[id].y*viewProperties.zoomFactor > canvas_container.scrollTop() + height ||
            nodes[id].x*viewProperties.zoomFactor < canvas_container.scrollLeft() ||
            nodes[id].x*viewProperties.zoomFactor > canvas_container.scrollLeft() + width) {
            canvas_container.scrollTop(y);
            canvas_container.scrollLeft(x);
        }
        view.draw();
        showNodeForm(id);
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
    selectGate(node, gate);
    view.draw();
    showGateForm(node, gate);
}

// sidebar editor forms ---------------------------------------------------------------

function initializeSidebarForms(){
    $('#edit_link_form').submit(handleEditLink);
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
        if(node in nodespaces.gatefunctions){
            var gate = nodespace_gatefunction_gate.val();
            if(nodespaces.gatefunctions[node][gate]){
                value = nodespaces.gatefunctions[node][gate];
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
    })
}

function showLinkForm(linkUid){
    $('#nodenet_forms .form-horizontal').hide();
    $('#edit_link_form').show();
    $('#link_weight_input').val(links[linkUid].weight);
    $('#link_certainty_input').val(links[linkUid].certainty);
    $('.link_source_node').html('<a href="#follownode" class="follownode" data="'+links[linkUid].sourceNodeUid+'">'+(nodes[links[linkUid].sourceNodeUid].name || nodes[links[linkUid].sourceNodeUid].uid.substr(0,8))+'</a>');
    $('.link_target_node').html('<a href="#follownode" class="follownode" data="'+links[linkUid].targetNodeUid+'">'+(nodes[links[linkUid].targetNodeUid].name || nodes[links[linkUid].targetNodeUid].uid.substr(0,8))+'</a>');
    $('a.follownode').on('click', follownode);
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
    } else {
        $('tr.node', form).show();
        $('#node_activation_input').val(nodes[nodeUid].sheaves[currentSheaf].activation);
        $('#node_function_input').val("Todo");
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
                for(id in nodes[nodeUid].slots[key].incoming){
                    if(!(links[id].gateName in inlink_types)){
                        inlink_types[links[id].gateName] = [];
                    }
                    inlink_types[links[id].gateName].push('<li><a href="#followlink" data="'+id+'" class="followlink">&lt;-</a> &nbsp;<a href="#followNode" data="'+links[id].sourceNodeUid+'" class="follownode">'+(nodes[links[id].sourceNodeUid].name || nodes[links[id].sourceNodeUid].uid.substr(0,8)+'&hellip;')+'</a></li>');
                }
            }
        }
        for(key in inlink_types){
            link_list += '<tr><td>';
            //link_list += '<a href="#followslot" class="followslots" data="'+available_gatetypes[j]+'">'+available_gatetypes[j]+"</a>";
            link_list += key + '</td><td>';
            link_list += "<ul>"+inlink_types[key].join(' ')+"</ul></td></tr>";
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
                        for(i in worldadapters[currentWorldadapter].datatargets){
                            input += "<option"+ (value == worldadapters[currentWorldadapter].datatargets[i] ? " selected=selected" : "") +">"+worldadapters[currentWorldadapter].datatargets[i]+"</option>";
                        }
                        input = "<select name=\"datatarget\" class=\"inplace\" id=\"node_datatarget\">"+input+"</select>";
                    }
                    break;
                case "datasource":
                    if(currentWorldadapter in worldadapters){
                        for(i in worldadapters[currentWorldadapter].datasources){
                            input += "<option"+ (value == worldadapters[currentWorldadapter].datasources[i] ? " selected=selected" : "") +">"+worldadapters[currentWorldadapter].datasources[i]+"</option>";
                        }
                        input = "<select name=\"datasource\" class=\"inplace\" id=\"node_datasource\">"+input+"</select>";
                    }
                    break;
                default:
                    if(parameter_values && parameter_values[name]){
                        for(i in parameter_values[name]){
                            input += "<option"+ (value == parameter_values[name][i] ? " selected=selected" : "") +">"+parameter_values[name][i]+"</option>";
                        }
                        input = "<select name=\""+name+"\" class=\"inplace\" id=\"node_"+name+"\">"+input+"</select>";
                    } else {
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
            if(nodespaces.gatefunctions && nodespaces.gatefunctions[node.type]){
                el.value = nodespaces.gatefunctions[node.type][gate.name] || '';
            }
        } else if(el.name == 'activation'){
            el.value = gate.sheaves[currentSheaf].activation || '0';
        } else if(el.name in nodetypes[node.type].gate_defaults[gate.name]){
            el.value = nodetypes[node.type].gate_defaults[gate.name][el.name];
        }
    });
    form.show();
}

function updateMonitorList(){
    var el = $('#monitor_list');
    var html = '<table class="table-striped table-condensed">';
    for(var uid in monitors){
        html += '<tr><td><input type="checkbox" class="monitor_checkbox" value="'+uid+'" id="'+uid+'"';
        if(currentMonitors.indexOf(uid) > -1){
            html += ' checked="checked"';
        }
        html += ' /> <label for="'+uid+'" style="display:inline;color:#'+uid.substr(2,6)+'"><strong>' + monitors[uid].type + ' ' + monitors[uid].target + '</strong> @ Node ' + (monitors[uid].node_name || monitors[uid].node_uid) + '</label></td></tr>';
    }
    html += '</table>';
    el.html(html);
    $('.monitor_checkbox', el).on('change', updateMonitorSelection);
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


/* todo:

 - get diffs
 - handle connection problems
 - multiple viewports
 - exporting and importing with own dialogs
 - edit native modules
 */
