/*
 * Paperscript code, defines the rendering of the node net within its canvas
 *
 * Autor: joscha
 * Date: 03.05.2012
 */


// initialization ---------------------------------------------------------------------

var viewProperties = {
    zoomFactor: 1,
    frameWidth: 50,
    activeColor: new Color("#009900"),
    inhibitedColor: new Color("#ff0000"),
    selectionColor: new Color("#0099ff"),
    hoverColor: new Color("#089AC7"),
    linkColor: new Color("#000000"),
    bgColor: new Color("#ffffff"),
    nodeColor: new Color("#c2c2d6"),
    nodeLabelColor: new Color ("#94c2f5"),
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
    compactModules: false,
    outsideDummyDistance: 70,
    outsideDummySize: 15,
    outsideDummyColor: new Color("#cccccc"),
    groupOutsideLinksThreshold: 0,
    forceCompactBelowZoomFactor: 0.9,
    strokeWidth: 0.3,
    outlineColor: null,
    outlineWidth: 0.3,
    outlineWidthSelected: 2.0,
    highlightColor: new Color ("#ffffff"),
    gateShadowColor: new Color("#888888"),
    shadowColor: new Color ("#000000"),
    shadowStrokeWidth: 0,
    shadowDisplacement: new Point(0.5,1.5),
    innerShadowDisplacement: new Point(0.2,0.7),
    linkTension: 50,
    linkRadius: 30,
    arrowWidth: 6,
    arrowLength: 10,
    rasterize: true,
    yMax: 13500,
    xMax: 13500
};

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

currentNodenet = $.cookie('selected_nodenet') || null;
currentNodeSpace = 'Root';   // cookie
currentWorldadapter = null;
var rootNode = new Node("Root", 0, 0, 0, "Root", "Nodespace");

var selectionRectangle = new Rectangle(1,1,1,1);
selectionBox = new Path.Rectangle(selectionRectangle);
selectionBox.strokeWidth = 0.5;
selectionBox.strokeColor = 'black';
selectionBox.dashArray = [4,2];
selectionBox.name = "selectionBox";

STANDARD_NODETYPES = ["Concept", "Register", "Actor", "Activator", "Sensor", "Event", "Label"];
nodetypes = {};
available_gatetypes = [];

initializeMenus();
initializeControls();
initializeSidebarForms();

canvas_container = $('#nodenet').parent();
loaded_coordinates = {
    x: [0, canvas_container.width() * 2],
    y: [0, canvas_container.height() * 2]
};
max_coordinates = {};
canvas_container.on('scroll', refreshViewPortData);

if(currentNodenet){
    setCurrentNodenet(currentNodenet);
} else {
    splash = new PointText(new Point(50, 50));
    splash.characterStyle = { fontSize: 20, fillColor: "#66666" };
    splash.content = 'Create a nodenet by selecting “New...” from the “Nodenet” menu.';
    nodeLayer.addChild(splash);
}

worldadapters = {};
currentSimulationStep = 0;
nodenetRunning = false;

refreshNodenetList();
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

function get_available_worldadapters(world_uid){
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
                setNodenetValues(nodenet_data);
                showDefaultForm();
        });
    } else {
        $('#nodenet_worldadapter').html('<option>&lt;No world selected&gt;</option>');
        setNodenetValues(nodenet_data);
        showDefaultForm();
    }
}

function setNodenetValues(data){
    $('#nodenet_uid').val(currentNodenet);
    $('#nodenet_name').val(data.name);
    setNodeTypes();
    if (!jQuery.isEmptyObject(worldadapters)) {
        var worldadapter_select = $('#nodenet_worldadapter');
        worldadapter_select.val(data.worldadapter);
        if(worldadapter_select.val() != data.worldadapter){
            dialogs.notification("The worldadapter of this nodenet is not compatible to the world. Please choose a worldadapter from the list", 'Error');
        }
    }
    showDataSourcesTargetsForWorldadapter(data.worldadapter);
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

            var nodenetChanged = (uid != currentNodenet);

            nodenet_data = data;

            showDefaultForm();
            $('#nodenet_step').val(data.step);

            currentNodeSpace = nodespace;
            currentNodenet = uid;

            nodes = {};
            links = {};
            nodeLayer.removeChildren();
            addNode(rootNode);
            linkLayer.removeChildren();

            $.cookie('selected_nodenet', uid, { expires: 7, path: '/' });
            if(nodenetChanged || jQuery.isEmptyObject(nodetypes)){
                api.call('get_available_node_types', {nodenet_uid:uid}, function(nodetypedata){
                    nodetypes = nodetypedata;
                    available_gatetypes = [];
                    for(var key in nodetypes){
                        if(nodetypes[key].gatetypes && nodetypes[key].gatetypes.length > available_gatetypes.length){
                            available_gatetypes = nodetypes[key].gatetypes;
                        }
                    }
                    get_available_worldadapters(data.world);
                    setNodespaceData(data);
                });
            } else {
                setNodespaceData(data);
            }
            refreshNodenetList();
        },
        function(data) {
            currentNodenet = null;
            $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
            dialogs.notification(data.Error, "error");
        });
}

// set visible nodes and links
function setNodespaceData(data){
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
        for(uid in data.nodes){
            item = new Node(uid, data.nodes[uid]['position'][0], data.nodes[uid]['position'][1], data.nodes[uid].parent_nodespace, data.nodes[uid].name, data.nodes[uid].type, data.nodes[uid].activation, data.nodes[uid].state, data.nodes[uid].parameters, data.nodes[uid].gate_parameters);
            if(uid in nodes){
                redrawNode(item);
                nodes[uid].update(item);
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
        for(uid in data.links){
            sourceId = data.links[uid]['source_node_uid'];
            targetId = data.links[uid]['target_node_uid'];
            if (sourceId in nodes && targetId in nodes && nodes[sourceId].parent == nodes[targetId].parent){
                link = new Link(uid, sourceId, data.links[uid].source_gate_name, targetId, data.links[uid].target_slot_name, data.links[uid].weight, data.links[uid].certainty);
                addLink(link);
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
            addLink(outsideLinks[index]);
        }

        if(data.monitors){
            monitors = data.monitors;
        }
        updateMonitorList();
        updateMonitorGraphs();
    }
    updateViewSize();
}

function refreshNodespace(nodespace, coordinates, step, callback){
    method = "get_nodespace";
    nodespace = nodespace || currentNodeSpace;
    params = {
        nodenet_uid: currentNodenet,
        nodespace: nodespace,
        step: currentSimulationStep
    };
    if (coordinates){
        params.step = -1;
    } else {
        coordinates = loaded_coordinates;
        if(step){
            params.step = step;
        }
    }
    params.x1 = parseInt(coordinates.x[0]);
    params.x2 = parseInt(coordinates.x[1]);
    params.y1 = parseInt(coordinates.y[0]);
    params.y2 = parseInt(coordinates.y[1]);
    api.call('get_nodespace', params , success=function(data){
        if(nodespace != currentNodeSpace){
            currentNodeSpace = nodespace;
            $("#nodespace_name").val(nodespace in nodes && nodes[nodespace].name ? nodes[nodespace].name : nodespace);
            nodeLayer.removeChildren();
            linkLayer.removeChildren();
        }
        loaded_coordinates = coordinates;
        if(jQuery.isEmptyObject(data)){
            if(nodenetRunning) setTimeout(refreshNodespace, 100);
            return null;
        }
        setNodespaceData(data);
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
        });
    }
}


function setNodeTypes(){
    var str = '';
    for (var key in nodetypes){
        if(STANDARD_NODETYPES.indexOf(key) >= 0){
            str += '<tr><td>' + key + '</td></tr>';
        } else {
            str += '<tr><td>' + key + '<a class="delete_nodetype close label" data="'+key+'">x</a></td></tr>';
        }
    }
    $('#nodenet_nodetypes').html(str);
    $('.delete_nodetype').on('click', delete_nodetype);
}

// data structures ----------------------------------------------------------------------


// data structure for net entities
function Node(uid, x, y, nodeSpaceUid, name, type, activation, state, parameters, gate_parameters) {
	this.uid = uid;
	this.x = x;
	this.y = y;
	this.activation = activation;
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
	if(type == "Nodespace") {
        this.symbol = "NS";
    } else {
        if (STANDARD_NODETYPES.indexOf(type) >= 0){
            this.symbol = type.substr(0,1);
        } else {
            this.symbol = "Na";
        }
        var i;
        for(i in nodetypes[type].slottypes){
            this.slots[nodetypes[type].slottypes[i]] = new Slot(nodetypes[type].slottypes[i]);
        }
        for(i in nodetypes[type].gatetypes){
            this.gates[nodetypes[type].gatetypes[i]] = new Gate(nodetypes[type].gatetypes[i], i, this.gate_parameters[nodetypes[type].gatetypes[i]]);
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
        this.activation = item.activation;
        this.state = item.state;
        this.parameters = item.parameters;
        this.gate_parameters = item.gate_parameters;
    };
}

// target for links, part of a net entity
function Slot(name) {
	this.name = name;
	this.incoming = {};
	this.activation = 0;
}

// source for links, part of a net entity
function Gate(name, index, parameters) {
	this.name = name;
    this.index = index;
	this.outgoing = {};
	this.activation = 0;
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
        if(sourceNode.uid) nodes[link.sourceNodeUid].gates[link.gateName].outgoing[link.uid]=link;
        if(targetNode.uid) nodes[link.targetNodeUid].slots[link.slotName].incoming[link.uid]=link;
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
    if (forceRedraw || !(link.uid in linkLayer.children) || (oldLink.weight != link.weight ||
        oldLink.certainty != link.certainty ||
        nodes[oldLink.sourceNodeUid].gates[oldLink.gateName].activation !=
            nodes[link.sourceNodeUid].gates[link.gateName].activation)) {
        if(link.uid in linkLayer.children){
            linkLayer.children[link.uid].remove();
        }
        renderLink(link);
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
function updateViewSize() {
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
            node.activation == nodes[node.uid].activation &&
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
    link.strokeColor = activationColor(gate.activation * link.weight, viewProperties.linkColor);

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
    node.zoomFactor = viewProperties.zoomFactor;
}

// draw net entity with slots and gates
function renderFullNode(node) {
    node.bounds = calculateNodeBounds(node);
    var skeleton = createFullNodeSkeleton(node);
    var activations = createFullNodeActivations(node);
    var titleBar = createFullNodeLabel(node);
    var nodeItem = new Group([activations, skeleton, titleBar]);
    nodeItem.name = node.uid;
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
        case "Register":
            shape = new Path.Circle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
            break;
        default:
            shape = new Path.RoundRectangle(bounds, viewProperties.cornerWidth*viewProperties.zoomFactor);
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
    label.opacity = 0.99; // clipping workaround to bug in paper.js
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
    var highlight = shape.clone();
    highlight.fillColor = viewProperties.highlightColor;
    var highlightSubtract = highlight.clone();
    highlightSubtract.position += displacement;
    var highlightClipper = highlight.clone();
    highlightClipper.position -= new Point(0.5, 0.5);
    highlightClipper.clipMask = true;
    var upper = new Group([highlightClipper, new CompoundPath([highlight, highlightSubtract])]);
    upper.opacity = 0.5;

    var shadowSubtract = shape;
    shadowSubtract.fillColor = viewProperties.shadowColor;
    var shadow = shadowSubtract.clone();
    shadow.position += displacement;
    var shadowClipper = shadow.clone();
    shadowClipper.position += new Point(0.5, 0.5);
    shadowClipper.clipMask = true;
    var lower = new Group([shadowClipper, new CompoundPath([shadow, shadowSubtract])]);
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
    label.opacity = 0.99; // clipping workaround to bug in paper.js
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
    skeleton = prerenderLayer.children[node.type].clone();
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
    activation = prerenderLayer.children[name].firstChild.clone();
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
    border = prerenderLayer.children["pillshape"].clone();
    border.position = bounds.center;
    var label = new Group();
    // clipping rectangle, so text does not flow out of the node
    var clipper = new Path.Rectangle(bounds);
    clipper.clipMask = true;
    label.addChild(clipper);
    label.opacity = 0.99; // clipping workaround to bug in paper.js
    var text = new PointText(bounds.center+new Point(0, viewProperties.lineHeight *0.3));
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
            activationColor(node.activation, viewProperties.nodeColor);
        if (!isCompact(node) && (node.slotIndexes.length || node.gateIndexes.length)) {
            var i=0;
            var type;
            for (type in node.slots) {
                nodeItem.children["activation"].children["slots"].children[i++].fillColor =
                    activationColor(node.slots[type].activation,
                    viewProperties.nodeColor);
            }
            i=0;
            for (type in node.gates) {
                nodeItem.children["activation"].children["gates"].children[i++].fillColor =
                    activationColor(node.gates[type].activation,
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
            outline.strokeColor = viewProperties.outlineColor;
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
    if (viewProperties.zoomFactor < viewProperties.forceCompactBelowZoomFactor) return true;
    if (node.type == "Native" || node.type=="Nodespace") return viewProperties.compactModules;
    if (/^Concept|Register|Sensor|Actor/.test(node.type)) return viewProperties.compactNodes;
    return false; // we don't know how to render this in compact form
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
	var col = new Color();
    var c;
	if (activation >0) c = viewProperties.activeColor; else c = viewProperties.inhibitedColor;
	var a = Math.abs(activation);
	var r = 1.0-a;
	return new HSLColor(c.hue,
                        baseColor.saturation * r + c.saturation * a,
                        baseColor.lightness * r + c.lightness * a);
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

function onMouseDown(event) {
    path = hoverPath = null;
    var p = event.point;
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
                if (!event.modifiers.shift &&
                    !event.modifiers.control && !event.modifiers.command && event.event.button != 2) deselectAll();
                if (event.modifiers.command && nodeUid in selection) deselectNode(nodeUid); // toggle
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
                    if (event.modifiers.control || event.event.button == 2) openContextMenu("#slot_menu", event.event);
                    else if (linkCreationStart) finalizeLinkHandler(nodeUid, clickIndex); // was slotIndex TODO: clickIndex?? linkcreationstart.gateIndex???
                    return;
                } else if ((i = testGates(node, p)) > -1) {
                    clickType = "gate";
                    clickIndex = i;
                    var gate = node.gates[node.gateIndexes[i]];
                    deselectGate();
                    selectGate(node, gate);
                    showGateForm(node, gate);
                    if (event.modifiers.control || event.event.button == 2) openContextMenu("#gate_menu", event.event);
                    return;
                }
                clickType = "node";
                if (event.modifiers.control || event.event.button == 2) openNodeContextMenu("#node_menu", event.event, nodeUid);
                else if (linkCreationStart) finalizeLinkHandler(nodeUid);
                else {
                    movePath = true;
                    clickPoint = p;
                }
                return;
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
        } else hover.fillColor = oldHoverColor;
        hover = null;
    }
    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    for (var nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            var node = nodes[nodeUid];
            var bounds = node.bounds;
            if (bounds.contains(p)) {
                hover = nodeLayer.children[nodeUid].children["activation"].children["body"];
                // check for slots and gates
                if ((i = testSlots(node, p)) >-1) {
                    hover = nodeLayer.children[nodeUid].children["activation"].children["slots"].children[i];
                } else if ((i = testGates(node, p)) > -1) {
                    hover = nodeLayer.children[nodeUid].children["activation"].children["gates"].children[i];
                }
                oldHoverColor = hover.fillColor;
                hover.fillColor = viewProperties.hoverColor;
                return;
            }
        }
    }
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
    if (movePath) {
        path.nodeMoved = true;
        path.position += event.delta;
        var node = nodes[path.name];
        node.x += event.delta.x/viewProperties.zoomFactor;
        node.y += event.delta.y/viewProperties.zoomFactor;
        node.bounds = calculateNodeBounds(node);
        redrawNodeLinks(node);
    }
}

function onMouseUp(event) {
    if (movePath) {
        if(path.nodeMoved && nodes[path.name]){
            // update position on server
            path.nodeMoved = false;
            moveNode(path.name, nodes[path.name].x, nodes[path.name].y);
            movePath = false;
            updateViewSize();
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
        viewProperties.zoomFactor += 0.1;
        redrawNodeNet(currentNodeSpace);
    }
    else if (event.character == "-" && event.event.target.tagName == "BODY") {
        if (viewProperties.zoomFactor > 0.2) viewProperties.zoomFactor -= 0.1;
        redrawNodeNet(currentNodeSpace);
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
    $(".nodenet_menu").on('click', 'li', handleContextMenu);
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
}

function initializeControls(){
    $('#nodenet_start').on('click', startNodenetrunner);
    $('#nodenet_stop').on('click', stopNodenetrunner);
    $('#nodenet_reset').on('click', resetNodenet);
    $('#nodenet_step_forward').on('click', stepNodenet);
}

function stepNodenet(event){
    event.preventDefault();
    if(nodenetRunning){
        stopNodenetrunner(event);
    }
    api.call("step_nodenet",
        {nodenet_uid: currentNodenet, nodespace:currentNodeSpace},
        success=function(data){
            refreshNodespace();
            dialogs.notification("Nodenet stepped", "success");
        });
}

function startNodenetrunner(event){
    event.preventDefault();
    nodenetRunning = true;
    api.call('start_nodenetrunner', {nodenet_uid: currentNodenet}, function(){
        refreshNodespace();
    });
}
function stopNodenetrunner(event){
    event.preventDefault();
    api.call('stop_nodenetrunner', {nodenet_uid: currentNodenet}, function(){ nodenetRunning = false; });
}

function resetNodenet(event){
    event.preventDefault();
    nodenetRunning = false;
    api.call(
        'revert_nodenet',
        {nodenet_uid: currentNodenet},
        function(){
            setCurrentNodenet(currentNodenet);
        }
    );
}

var clickPosition = null;

function openContextMenu(menu_id, event) {
    event.cancelBubble = true;
    clickPosition = new Point(event.offsetX, event.offsetY);
    $(menu_id).css({
        position: "absolute",
        zIndex: 500,
        marginLeft: -5, marginTop: -5,
        top: event.pageY, left: event.pageX });
    $(menu_id+" .dropdown-toggle").dropdown("toggle");
}

// build the node menu
function openNodeContextMenu(menu_id, event, nodeUid) {
    var menu = $(menu_id+" .dropdown-menu");
    menu.off('click', 'li');
    menu.empty();
    var node = nodes[nodeUid];
    if (node.type == "Concept") {
        menu.append('<li><a href="#">Create gen link</a></li>');
        menu.append('<li><a href="#">Create por/ret link</a></li>');
        menu.append('<li><a href="#">Create sub/sur link</a></li>');
        menu.append('<li><a href="#">Create cat/exp link</a></li>');
        menu.append('<li class="divider"></li>');
    } else if (node.gateIndexes.length) {
        for (var gateName in node.gates) {
            menu.append('<li><a href="#">Create '+gateName+' link</a></li>');
        }
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
    switch (clickType) {
        case null: // create nodes
            var type;
            var callback = function(data){
                dialogs.notification('Node created', 'success');
            };
            switch (menuText) {
                case "Create concept node":
                    type = "Concept";
                    break;
                case "Create native module":
                    type = "Native";
                    break;
                case "Create node space":
                    type = "Nodespace";
                    break;
                case "Create sensor":
                    type = "Sensor";
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
                case "Create actor":
                    type = "Actor";
                    break;
                case "Create activator":
                    type = "Activator";
                    break;
                case "Create event":
                    type = "Event";
                    break;
                case "Create register":
                    type = "Register";
                    break;
                default:
                    type = "Autoalign";
            }
            if(type == "Autoalign"){
                autoalignmentHandler(currentNodeSpace);
            } else {
                if (type == "Native") createNativeModuleHandler();
                else createNodeHandler(clickPosition.x/viewProperties.zoomFactor,
                    clickPosition.y/viewProperties.zoomFactor,
                    currentNodeSpace, "", type, null, callback);
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
                    if (menuText.substring(0, 6) == "Create" && menuText.indexOf(" link")>0) {
                        var linktype = menuText.substring(7, menuText.indexOf(" link"));
                        if(linktype.indexOf('/')){
                            linktype = linktype.split('/')[0];
                        }
                        clickIndex = available_gatetypes.indexOf(linktype);
                        createLinkHandler(clickOriginUid, clickIndex, menuText.substring(7, menuText.indexOf(" link")));
                    }
            }
            break;
        case "slot":
            switch (menuText) {
                case "Add monitor to slot":
                    addSlotMonitor(nodes[clickOriginUid], clickIndex);
                    break;
            }
            break;
        case "gate":
            switch (menuText) {
                case "Create link":
                    createLinkHandler(clickOriginUid, clickIndex);
                    break;
                case "Add monitor to gate":
                    addGateMonitor(nodes[clickOriginUid], clickIndex);
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
function autoalignmentHandler(currentNodespace) {
    api.call("align_nodes", {
            nodenet_uid: currentNodenet,
            nodespace: currentNodespace
        },
        function(data){
            setCurrentNodenet(currentNodenet, currentNodespace);
        });
}

// let user create a new node
function createNodeHandler(x, y, currentNodespace, name, type, parameters, callback) {
    var uid = makeUuid();
    params = {};
    if (!parameters) parameters = {};
    if (nodetypes[type]){
        for (var i in nodetypes[type].parameters){
            params[nodetypes[type].parameters[i]] = parameters[nodetypes[type].parameters[i]] || "";
        }
    }
    addNode(new Node(uid, x, y, currentNodeSpace, name, type, 0, null, params));
    view.draw();
    selectNode(uid);
    api.call("add_node", {
        nodenet_uid: currentNodenet,
        type: type,
        pos: [x,y],
        nodespace: currentNodespace,
        uid: uid,
        name: name,
        parameters: params },
        success=function(data){
            if(callback) callback(data);
            showNodeForm(uid);
        });
    return uid;
}


function createNativeModuleHandler(event){
    var form = $('#native_module_form');
    if (!event){
        $('#edit_native_modal .modal-body').append(form);
        form.show();
        var types = '';
        for (var name in nodetypes){
            types += '<option>'+name+'</option>';
        }
        $('#native_type').html(types);
        $('input[type="checkbox"]', false).checked = false;
        $('#native_function', form).val('');
        $('.native-default').show();
        $('.native-details').hide();
        //setNativeModuleFormValues(form, this.uid);
        $('#edit_native_modal').modal("show");
    } else {
        var type = $('#native_type');
        var custom = $('#native_new_type');
        var nodetype = custom.val() || type.val();
        if(event.target.className.indexOf('native-next') >= 0){
            $('.native-default').hide();
            $('.native-details').show();
            form.data = nodetype;
            if(nodetypes[nodetype]){
                $('.native-custom').hide();
                $('#native_parameters').html(getNodeParameterHTML(nodetypes[type.val()].parameters, nodetypes[type.val()].parameter_values));
            }
        } else if (event.target.className.indexOf('native-save') >= 0){
            var parameters;
            var nodename = $('#native_name').val();
            if(!nodetypes[nodetype]){
                var mapping = {'por': 'ret', 'sub': 'sur', 'isa': 'exp'};
                var relations = {gate: [], slot: []};
                var parts;
                var checkboxes = $('input[type="checkbox"]');
                for(var idx in checkboxes){
                    if(checkboxes[idx].checked){
                        parts = checkboxes[idx].name.split('_');
                        relations[parts[1]].push(parts[0]);
                        if (mapping[parts[0]]){
                            relations[parts[1]].push(mapping[parts[0]]);
                        }
                    }
                }
                parameters = {};
                var param_fields = $('input[name^="param_"]', form);
                var param_list = [];
                for(var i in param_fields){
                    if(param_fields[i].name == "param_name"){
                        param_list.push(param_fields[i].value);
                        parameters[param_fields[i].value] = param_fields[++i].value;
                    }
                }
                var nodefunction = $('#native_function').val();
                nodetypes[nodetype] = {
                    gatetypes: relations.gate,
                    slottypes: relations.slot,
                    parameters: param_list,
                    nodefunction_definition: nodefunction,
                    name: nodetype
                };
                api.call('add_node_type', {
                    nodenet_uid: currentNodenet,
                    node_type: nodetype,
                    slots: relations.slot,
                    gates: relations.gate,
                    parameters: param_list,
                    node_function: nodefunction},
                    function(data){
                        $('#edit_native_modal').modal("hide");
                        createNodeHandler(
                            clickPosition.x/viewProperties.zoomFactor,
                            clickPosition.y/viewProperties.zoomFactor,
                            currentNodeSpace,
                            nodename,
                            nodetype,
                            parameters);
                    },
                    api.defaultErrorCallback,
                    "post"
                );
            } else {
                parameters = {};
                var fields = $(":input", $('native_parameters'));
                for(var j in fields){
                    parameters[fields[j].name] = fields[j].value;
                }
                $('#edit_native_modal').modal("hide");
                createNodeHandler(clickPosition.x/viewProperties.zoomFactor,
                    clickPosition.y/viewProperties.zoomFactor,
                    currentNodeSpace,
                    nodename,
                    nodetype,
                    parameters);
            }

            // save this thing.

        }
    }
}


// let user delete the current node, or all selected nodes
function deleteNodeHandler(nodeUid) {
    function deleteNodeOnServer(node_uid){
        api.call("delete_node",
            {nodenet_uid:currentNodenet, node_uid: node_uid},
            success=function(data){
                dialogs.notification('node deleted', 'success');
            }
        );
    }
    var deletedNodes = [];
    if (nodeUid in nodes) {
        deletedNodes.push(nodeUid);
        removeNode(nodes[nodeUid]);
        if (nodeUid in selection) delete selection[nodeUid];
        // todo: tell the server all about it
    }
    for (var selected in selection) {
        deletedNodes.push(selected);
        removeNode(nodes[selected]);
        delete selection[selected];
        // todo: tell the server all about it
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
        removeLink(links[selected]);
        delete selection[selected];
        removeLinkOnServer(selected);
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

// establish the created link
function finalizeLinkHandler(nodeUid, slotIndex) {
    var sourceUid = linkCreationStart.sourceNode.uid;
    var targetUid = nodeUid;
    var gateIndex = linkCreationStart.gateIndex;

    if (!slotIndex || slotIndex < 0) slotIndex = 0;

    if ((targetUid in nodes) &&
        nodes[targetUid].slots && (nodes[targetUid].slotIndexes.length > slotIndex) &&
        (targetUid != sourceUid)) {

        var targetGates = nodes[targetUid].gates ? nodes[targetUid].gateIndexes.length : 0;
        var uuid = makeUuid();
        if(nodes[sourceUid].parent != currentNodeSpace){
            nodes[targetUid].linksFromOutside.push(uuid);
            nodes[sourceUid].linksToOutside.push(uuid);
        }
        switch (linkCreationStart.creationType) {
            case "por/ret":
                addLink(new Link(uuid, sourceUid, "por", targetUid, "gen", 1, 1));
                if (targetGates > 2) addLink(new Link(makeUuid(), targetUid, "ret", sourceUid, "gen", 1, 1));
                break;
            case "sub/sur":
                addLink(new Link(uuid, sourceUid, "sub", targetUid, "gen", 1, 1));
                if (targetGates > 4) addLink(new Link(makeUuid(), targetUid, "sur", sourceUid, "gen", 1, 1));
                break;
            case "cat/exp":
                addLink(new Link(uuid, sourceUid, "cat", targetUid, "gen", 1, 1));
                if (targetGates > 6) addLink(new Link(makeUuid(), targetUid, "exp", sourceUid, "gen", 1, 1));
                break;
            case "gen":
                addLink(new Link(uuid, sourceUid, "gen", targetUid, "gen", 1, 1));
                break;
            default:
                addLink(new Link(uuid, sourceUid, nodes[sourceUid].gateIndexes[gateIndex], targetUid, nodes[targetUid].slotIndexes[slotIndex], 1, 1));
        }
        // TODO: also write backwards link??
        api.call("add_link", {
            nodenet_uid: currentNodenet,
            source_node_uid: sourceUid,
            gate_type: nodes[sourceUid].gateIndexes[gateIndex],
            target_node_uid: targetUid,
            slot_type: nodes[targetUid].slotIndexes[slotIndex],
            weight: 1,
            uid: uuid
        });
        cancelLinkCreationHandler();
    }
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
    if(nodes[nodeUid].activation != activation){
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
    var gatefunction = null;
    for(var i in data){
        if(data[i].name == 'gatefunction'){
            gatefunction = data[i].value;
        } else {
            params[data[i].name] = parseFloat(data[i].value);
        }
    }
    if(!(node.type in gatefunctions[currentNodeSpace]) ||
        gatefunctions[currentNodeSpace][node.type][gate.name] != gatefunction){
        if(!(node.type in gatefunctions[currentNodeSpace])){
            gatefunctions[currentNodeSpace][node.type] = {};
        }
        gatefunctions[currentNodeSpace][node.type][gate.name] = gatefunction;
        api.call('set_gate_function', {
            nodenet_uid: currentNodenet,
            nodespace: currentNodeSpace,
            node_type: node.type,
            gate_type: gate.name,
            gate_function: gatefunction
        }, api.defaultSuccessCallback, api.defaultErrorCallback, method="POST");
    }
    api.call('set_gate_parameters', {
        nodenet_uid: currentNodenet,
        node_uid: node.uid,
        gate_type: gate.name,
        parameters: params
    });
}

function setNodeActivation(nodeUid, activation){
    nodes[nodeUid].activation = activation;
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
    nodes[nodeUid].name = name;
    api.call("set_node_name", {
        nodenet_uid: currentNodenet,
        node_uid: nodeUid,
        name: name
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
    nodes[clickOriginUid].parameters['datatargets'] = value;
    showNodeForm(nodeUid);
    api.call("bind_datasource_to_sensor", {
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
        });
    }
}

// handler for entering parent nodespace
function handleNodespaceUp() {
    deselectAll();
    if (nodes[currentNodeSpace].parent) { // not yet root nodespace
        refreshNodespace(nodes[currentNodeSpace].parent, {
            x: [0, canvas_container.width() * 2],
            y: [0, canvas_container.height() * 2]
        });
    }
}

function handleEditNodenet(event){
    event.preventDefault();
    var form = event.target;
    var params = {
        nodenet_name: $('#nodenet_name', form).val()
    };
    if(nodenet_data.world){
        params.world_uid = nodenet_data.world;
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

function delete_nodetype(event){
    event.preventDefault();
    var name = $(event.target).attr('data');
    for(var uid in nodes){
        if(nodes[uid].type == name){
            return dialogs.notification("There are still nodes registered to this nodetype. It can not be deleted");
        }
    }
    api.call('delete_node_type', {'nodenet_uid': currentNodenet, 'node_type': name}, function(data){
        delete nodetypes[name];
        setNodeTypes();
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
            x: [x-canvas_container.width(), canvas_container.width() * 2],
            y: [y, canvas_container.height() * 2]
        }, null, function(){
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

// sidebar editor forms ---------------------------------------------------------------

function initializeSidebarForms(){
    $('#edit_link_form').submit(handleEditLink);
    $('#edit_node_form').submit(handleEditNode);
    $('#edit_gate_form').submit(handleEditGate);
    $('#edit_nodenet_form').submit(handleEditNodenet);
    $('#native_module_form').submit(createNativeModuleHandler);
    $('#native_add_param').click(function(){
        $('#native_parameters').append('<tr><td><input name="param_name" type="text" class="inplace"/></td><td><input name="param_value" type="text"  class="inplace" /></td></tr>');
    });
    var worldadapter_selector = $('#nodenet_worldadapter');
    worldadapter_selector.on('change', function(){
        showDataSourcesTargetsForWorldadapter(worldadapter_selector.val());
    });
}

function showDataSourcesTargetsForWorldadapter(worldadapter){
    var i;
    var datatargets, datasources = '';
    if(worldadapter){
        if (worldadapters[worldadapter].datatargets) {
            for (i in worldadapters[worldadapter].datatargets){
                datatargets += '<tr><td>'+worldadapters[worldadapter].datatargets[i]+'</td></tr>';
            }
        }
        if (worldadapters[worldadapter].datasources){
            for (i in worldadapters[worldadapter].datasources){
                datasources += '<tr><td>'+worldadapters[worldadapter].datasources[i]+'</td></tr>';
            }
        }
    }
    $('#nodenet_datatargets').html(datatargets || '<tr><td>No datatargets defined</td></tr>');
    $('#nodenet_datasources').html(datasources || '<tr><td>No datasources defined</td></tr>');
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
        $('#node_activation_input').val(nodes[nodeUid].activation);
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
        var content = "", gates="", id, name;
        var link_list = "";
        var inlink_types = {};
        if(nodes[nodeUid].slots["gen"]){
            for(id in nodes[nodeUid].slots["gen"].incoming){
                if(!(links[id].gateName in inlink_types)) inlink_types[links[id].gateName] = [];
                inlink_types[links[id].gateName].push('<li><a href="#followlink" data="'+id+'" class="followlink">'+id.substr(0,8)+'&hellip;</a> <- <a href="#followNode" data="'+links[id].sourceNodeUid+'" class="follownode">'+(nodes[links[id].sourceNodeUid].name || nodes[links[id].sourceNodeUid].uid.substr(0,8)+'&hellip;')+'</a></li>');
            }
        }
        for(var j in available_gatetypes){
            if(available_gatetypes[j] in inlink_types){
                link_list += "<tr><td>"+available_gatetypes[j]+"</td><td><ul>"+inlink_types[available_gatetypes[j]].join(' ')+"</ul></td></tr>";
            }
        }
        $('#node_slots').html(link_list || "<tr><td>None</td></tr>");
        content = "";
        for(name in nodes[nodeUid].gates){
            link_list = "";
            for(id in nodes[nodeUid].gates[name].outgoing){
                link_list += '<li><a href="#followlink" data="'+id+'" class="followlink">'+id.substr(0,8)+'&hellip;</a> -> <a href="#followNode" data="'+links[id].targetNodeUid+'" class="follownode">'+(nodes[links[id].targetNodeUid].name || nodes[links[id].targetNodeUid].uid.substr(0,8)+'&hellip;')+'</a></li>';
            }
            if(link_list !== "") content += "<tr><td>"+name+"</td><td><ul>"+link_list+"<ul></td></tr>";
        }
        $('#node_gates').html(content || "<tr><td>None</td></tr>");
        $('a.followlink').on('click', followlink);
        $('a.follownode').on('click', follownode);
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
    $('#edit_nodenet_form').show();
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
            if(gatefunctions[currentNodeSpace] && node.type in gatefunctions[currentNodeSpace]){
                el.value = gatefunctions[currentNodeSpace][node.type][gate.name] || '';
            }
        }
    });
    form.show();
}

function updateMonitorList(){
    var el = $('#monitor_list');
    var html = '<table class="table-striped table-condensed">';
    for(var uid in monitors){
        html += '<tr><td><input type="checkbox" class="monitor_checkbox" value="'+uid+'" id="'+uid+'" /> <label for="'+uid+'" style="display:inline;color:#'+uid.substr(2,6)+'"><strong>' + monitors[uid].type + ' ' + monitors[uid].target + '</strong> @ Node ' + (nodes[monitors[uid].node_uid].name || monitors[uid].node_uid) + '</label></td></tr>';
    }
    html += '</table>';
    el.html(html);
    $('.monitor_checkbox', el).on('change', updateMonitorSelection);
}


/* todo:

 - get diffs
 - handle connection problems
 - multiple viewports
 - exporting and importing with own dialogs
 - edit native modules
 */
