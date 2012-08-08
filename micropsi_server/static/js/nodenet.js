/*
 * Paperscript code, defines the rendering of the node net within its canvas
 *
 * Autor: joscha
 * Date: 03.05.2012
 */


// initialization ---------------------------------------------------------------------

var viewProperties = {
    zoomFactor: 1,
    frameWidth: 100,
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
    rasterize: true
};

// hashes from uids to object definitions; we import these via json
nodes = {};
links = {};
selection = {};

var linkLayer = new Layer();
var nodeLayer = new Layer();
var prerenderLayer = new Layer();
prerenderLayer.visible = false;


var currentNodenet = "b2";  // TODO: fetch from cookie
var currentWorld = 0;       // cookie
var currentNodeSpace = 0;   // cookie

initializeMenus();
initializeNodeNet();

refreshNodenetList();

function refreshNodenetList(){
    $("#nodenet_list").load("/nodenet_list/"+currentNodenet, function(data){
        $('#nodenet_list .nodenet_select').on('click', function(event){
            event.preventDefault();
            var el = $(event.target);
            uid = el.attr('data');
            setCurrentNodenet(uid);
        });
    });
}

function setCurrentNodenet(uid){
    $.ajax('/rpc/load_nodenet_into_ui(nodenet_uid="'+uid+'")', {
        success: function(data){
            // todo: server should deliver according status code.
            if (!data.Error){
                currentNodenet = uid;
                initializeNodeNet(data);
                refreshNodenetList();
            } else {
                dialogs.notification(data.Error, "error");
            }
        }
    });
}

// fetch visible nodes and links
function initializeNodeNet(data){

    console.log("initializing new nodenet");
    console.log(data);

    linkLayer.removeChildren();
    nodeLayer.removeChildren();
    prerenderLayer.removeChildren();

    prerenderLayer.visible = false;
    currentNodeSpace = "Root";
    addNode(new Node("Root", 0, 0, 0, "Root", "Nodespace"));

    addNode(new Node("a1", 150, 450, "Root", "Alice", "Actor", 1));
    addNode(new Node("a2", 250, 450, "Root", "Tom", "Actor", 0.3));
    addNode(new Node("a3", 350, 450, "Root", "André", "Actor", 0.0));
    addNode(new Node("a4", 450, 450, "Root", "Boris", "Actor", -0.1));
    addNode(new Node("a5", 550, 450, "Root", "Sarah", "Actor", 0.3));
    addNode(new Node("a5b", 300, 80, "Root", "Umzug", "Concept", 0.2));
    addNode(new Node("a6", 100, 270, "Root", "Planung", "Concept", 0.3));
    addLink(new Link("a5b", 3, "a6", 0, 0.8, 1));

    addNode(new Node("a7", 250, 270, "Root", "Vorbereitung", "Concept", 0.6));
    addNode(new Node("a8", 400, 270, "Root", "Fahrzeugbestellung", "Concept", -0.8));
    addNode(new Node("a9", 550, 270, "Root", "Einladung", "Concept", 0.7));
    addNode(new Node("a10", 700, 270, "Root", "Packen", "Concept", 0.2));
    addNode(new Node("a11", 950, 270, "Root", "Durchführung", "Concept", 0.0));
    addNode(new Node("a11b", 1100, 270, "Root", "Fahrzeugrückgabe", "Concept", -0.6));
    addNode(new Node("a12", 1250, 270, "Root", "Party", "Concept", 0.0));
    addNode(new Node("a12b", 1400, 350, "Root", "Einkäufe", "Concept", 0.2));
    addNode(new Node("a13", 700, 450, "Root", "Fahrzeug", "Native", 0.5));
    addNode(new Node("a14", 800, 450, "Root", "Kisten", "Register", 0.5));
    addNode(new Node("a15", 900, 450, "Root", "Getränke", "Register", 0.5));
    addNode(new Node("a16", 680, 380, "Root", "Datum", "Sensor", -0.5));
    addNode(new Node("a17", 780, 380, "Root", "Orts-Temperatur", "Sensor", 0.5));

    addLink(new Link("a1", 0, "a6", 0, 1, 1));
    addLink(new Link("a1", 0, "a7", 0, 1, 1));
    addLink(new Link("a1", 0, "a8", 0, 0.5, 1));
    addLink(new Link("a1", 0, "a9", 0, 0.8, 1));
    addLink(new Link("a1", 0, "a10", 0, 1, 1));
    addLink(new Link("a1", 0, "a12", 0, 1, 1));
    addLink(new Link("a1", 0, "a12b", 0, 1, 1));
    addLink(new Link("a2", 0, "a12b", 0, 1, 1));
    addLink(new Link("a2", 0, "a8", 0, 0.5, 1));
    addLink(new Link("a2", 0, "a11", 0, 1, 1));
    addLink(new Link("a2", 0, "a11b", 0, 1, 1));
    addLink(new Link("a2", 0, "a10", 0, 0.8, 1));
    addLink(new Link("a3", 0, "a10", 0, 1, 1));
    addLink(new Link("a3", 0, "a12", 0, 1, 1));
    addLink(new Link("a4", 0, "a11", 0, 1, 1));
    addLink(new Link("a4", 0, "a12", 0, 1, 1));
    addLink(new Link("a5", 0, "a11", 0, 1, 1));

    addLink(new Link("a13", 0, "a8", 0, 1, 1));
    addLink(new Link("a11", 3, "a13", 0, 1, 1));
    addLink(new Link("a12b", 3, "a13", 0, 1, 1));
    addLink(new Link("a11b", 3, "a13", 0, 1, 1));
    addLink(new Link("a12b", 3, "a15", 0, 0.7, 1));
    addLink(new Link("a15", 0, "a12", 0, 1, 1));
    addLink(new Link("a14", 0, "a10", 0, 1, 1));

    addLink(new Link("a16", 0, "a8", 0, 1, 1));
    addLink(new Link("a16", 0, "a11", 0, 0.9, 1));
    addLink(new Link("a16", 0, "a11b", 0, 1, 1));

    addLink(new Link("a17", 0, "a11", 0, 0.3, 1));

    addLink(new Link("a5b", 3, "a7", 0, 0.9, 1));
    addLink(new Link("a5b", 3, "a8", 0, 1, 1));
    addLink(new Link("a5b", 3, "a9", 0, 0.9, 1));
    addLink(new Link("a5b", 3, "a10", 0, 1, 1));
    addLink(new Link("a5b", 3, "a11", 0, 1, 1));
    addLink(new Link("a5b", 3, "a11b", 0, 1, 1));
    addLink(new Link("a5b", 3, "a12", 0, 0.7, 1));

    addLink(new Link("a6", 4, "a5b", 0, 0.2, 1));
    addLink(new Link("a7", 4, "a5b", 0, 0.1, 1));
    addLink(new Link("a8", 4, "a5b", 0, 0.4, 1));
    addLink(new Link("a9", 4, "a5b", 0, 1, 1));
    addLink(new Link("a10", 4, "a5b", 0, 1, 1));
    addLink(new Link("a11", 4, "a5b", 0, 1, 1));
    addLink(new Link("a11b", 4, "a5b", 0, 0.8, 1));
    addLink(new Link("a12", 4, "a5b", 0, 0.3, 1));

    addLink(new Link("a12b", 4, "a12", 0, 0.7, 1));
    addLink(new Link("a12", 3, "a12b", 0, 1, 1));

    addLink(new Link("a6", 1, "a7", 0, 1, 1));
    addLink(new Link("a7", 1, "a8", 0, 1, 1));
    addLink(new Link("a8", 1, "a9", 0, 1, 1));
    addLink(new Link("a9", 1, "a10", 0, 1, 1));
    addLink(new Link("a10", 1, "a11", 0, 1, 1));
    addLink(new Link("a11", 1, "a11b", 0, 1, 1));
    addLink(new Link("a11b", 1, "a12", 0, 1, 1));
    addLink(new Link("a7", 2, "a6", 0, 1, 1));
    addLink(new Link("a8", 2, "a7", 0, 1, 1));
    addLink(new Link("a9", 2, "a8", 0, 1, 1));
    addLink(new Link("a10", 2, "a9", 0, 1, 1));
    addLink(new Link("a11", 2, "a10", 0, 1, 1));
    addLink(new Link("a11b", 2, "a11", 0, 1, 1));
    addLink(new Link("a12", 2, "a11b", 0, 1, 1));



    updateViewSize();
}

// data structures ----------------------------------------------------------------------


// data structure for net entities
function Node(uid, x, y, nodeSpaceUid, name, type, activation) {
	this.uid = uid;
	this.x = x;
	this.y = y;
	this.activation = activation;
	this.name = name;
	this.type = type;
	this.symbol = "?";
	this.slots=[];
	this.gates=[];
    this.parent = nodeSpaceUid; // parent nodespace, default is root
    this.fillColor = null;
    this.bounds = null; // current bounding box (after scaling)
	switch (type) {
        case "Nodespace":
            this.symbol = "NS";
            break;
        case "Sensor":
            this.symbol = "S";
            this.gates.push(new Gate("gen"));
            break;
        case "Actor":
            this.symbol = "A";
            this.slots.push(new Slot("gen"));
            this.gates.push(new Gate("gen"));
            break;
        case "Register":
			this.symbol = "R";
			this.slots.push(new Slot("gen"));
			this.gates.push(new Gate("gen"));
			break;
		case "Concept":
			this.symbol = "C";
			this.slots.push(new Slot("gen"));
            this.gates.push(new Gate("gen"));
			this.gates.push(new Gate("por"));
			this.gates.push(new Gate("ret"));
			this.gates.push(new Gate("sub"));
			this.gates.push(new Gate("sur"));
			this.gates.push(new Gate("cat"));
			this.gates.push(new Gate("exp"));
			break;
        default: // native code node (completely custom)
            this.symbol = "Na";
            this.slots.push(new Slot("gen"));
            this.gates.push(new Gate("gen"));
            // TODO: fetch list of slots and gates from server
            break;
	}
}

// target for links, part of a net entity
function Slot(name) {
	this.name = name;
	this.incoming = {};
	this.activation = 0;
}

// source for links, part of a net entity
function Gate(name) {
	this.name = name;
	this.outgoing = {};
	this.activation = 0;
}

// link, connects two nodes, from a gate to a slot
function Link(sourceNodeUid, gateIndex, targetNodeUid, slotIndex, weight, certainty){
    this.uid = [sourceNodeUid,"#",gateIndex,"-",targetNodeUid,"#",slotIndex].join("");
    this.sourceNodeUid = sourceNodeUid;
    this.gateIndex = gateIndex;
    this.targetNodeUid = targetNodeUid;
    this.slotIndex = slotIndex;
    this.weight = weight;
    this.certainty = certainty;

    this.strokeColor = null;
    this.strokeWidth = null;
}

// data manipulation ----------------------------------------------------------------

// add or update link
function addLink(link) {
    //check if link already exists
    if (!(link.uid in links)) {
        // add link to source node and target node
        if (nodes[link.sourceNodeUid] && nodes[link.targetNodeUid]) {
            nodes[link.sourceNodeUid].gates[link.gateIndex].outgoing[link.uid]=link;
            nodes[link.targetNodeUid].slots[link.slotIndex].incoming[link.uid]=link;
            // check if link is visible
            if (nodes[link.sourceNodeUid].parent == currentNodeSpace ||
                nodes[link.targetNodeUid].parent == currentNodeSpace) {
                renderLink(link);
            }
            links[link.uid] = link;
        } else {
            console.log("Error: Attempting to create link without establishing nodes first");
        }
    } else {
        // if weight or activation change, we need to redraw
        oldLink = links[link.uid];
        if (oldLink.weight != link.weight ||
            oldLink.certainty != link.certainty ||
            nodes[oldLink.sourceNodeUid].gates[oldLink.gateIndex].activation !=
                nodes[link.sourceNodeUid].gates[link.gateIndex].activation) {
            linkLayer.children[link.uid].remove();
            renderLink(link);
        }
    }
}

// delete a link from the array, and from the screen
function removeLink(link) {
    delete links[link.uid];
    if (link.uid in linkLayer.children) linkLayer.children[link.uid].remove();
    delete nodes[link.sourceNodeUid].gates[link.gateIndex].outgoing[link.uid];
    delete nodes[link.targetNodeUid].slots[link.slotIndex].incoming[link.uid];
}

// add or update node, should usually be called from the JSON parser
function addNode(node) {
    // check if node already exists
    if (! (node.uid in nodes)) {
        if (node.parent == currentNodeSpace) renderNode(node);
        nodes[node.uid] = node;
    } else {
        oldNode = nodes[node.uid];

        // if node only updates position or activation, we may save some time
        // import all properties individually; check if we really need to redraw
    }
    view.viewSize.x = Math.max (view.viewSize.x, (node.x + viewProperties.frameWidth)*viewProperties.zoomFactor);
    view.viewSize.y = Math.max (view.viewSize.y, (node.y + viewProperties.frameWidth)*viewProperties.zoomFactor);
}

// remove the node from hash, get rid of orphan links, and delete it from the screen
function removeNode(node) {
    for (gateIndex in node.gates) {
        for (linkUid in node.gates[gateIndex].outgoing) {
            removeLink(links[linkUid]);
        }
    }
    for (slotIndex in node.slots) {
        for (linkUid in node.slots[slotIndex].incoming) {
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
    var maxX = maxY = 0;
    var frameWidth = viewProperties.frameWidth*viewProperties.zoomFactor;
    var el = view.element.parentElement;
    prerenderLayer.removeChildren();
    for (nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            node = nodes[nodeUid];
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
    view.viewSize = new Size(Math.max((maxX+viewProperties.frameWidth)*viewProperties.zoomFactor,
        el.clientWidth),
        Math.max((maxY+viewProperties.frameWidth)* viewProperties.zoomFactor,
            el.clientHeight));
}

// complete redraw of the current node space
function redrawNodeNet() {
    nodeLayer.removeChildren();
    linkLayer.removeChildren();

    for (i in nodes) {
        if (nodes[i].parent == currentNodeSpace) renderNode(nodes[i]);
    }
    for (i in links) {
        sourceNode = nodes[links[i].sourceNodeUid];
        targetNode = nodes[links[i].targetNodeUid];
        // check for source and target nodes, slots and gates
        if (!sourceNode) {
            console.log("Did not find source Node for link from "
                +nodes[links[i].sourceNodeUid]+" to "
                +nodes[links[i].targetNodeUid]);
            continue;
        }
        if (sourceNode.gates.length < links[i].gateIndex) {
            console.log("Node "+sourceNode.uid+ "does not have a gate with index "+links[i].gateIndex);
            continue;
        }
        if (!targetNode) {
            console.log("Did not find target Node for link from "
                +nodes[links[i].sourceNodeUid]+" to "
                +nodes[links[i].targetNodeUid]);
            continue;
        }
        if (targetNode.slots.length < links[i].slotIndex) {
            console.log("Node "+targetNode.uid+ " does not have a slot with index "+links[i].slotIndex);
            continue;
        }
        // check if the link is visible
        if (sourceNode.parent == currentNodeSpace || targetNode.parent == currentNodeSpace) {
            renderLink(links[i]);
        }
    }
    updateViewSize();
}

// like activation change, only put the node elsewhere and redraw the links
function redrawNode(node) {
    nodeLayer.children[node.uid].remove();
    renderNode(node);
    redrawNodeLinks(node);
}

// redraw only the links that are connected to the given node
function redrawNodeLinks(node) {
    for (gateIndex in node.gates) {
        for (linkUid in node.gates[gateIndex].outgoing) {
            linkLayer.children[linkUid].remove();
            renderLink(links[linkUid]);
        }
    }
    for (slotIndex in node.slots) {
        for (linkUid in node.slots[slotIndex].incoming) {
            linkLayer.children[linkUid].remove();
            renderLink(links[linkUid]);
        }
    }
}

// determine the point where link leaves the node
function calculateLinkStart(sourceNode, gateIndex) {
    var startPointIsPreliminary = false;
    gate = sourceNode.gates[gateIndex];
    // Depending on whether the node is drawn in compact or full shape, links may originate at odd positions.
    // This depends on the node type and the link type.
    // If a link does not have a preferred direction on a compact node, it will point directly from the source
    // node to the target node. However, this requires to know both points, so there must be a preliminary step.
    if (isCompact(sourceNode)) {
        sourceBounds = sourceNode.bounds;
        if (sourceNode.type=="Sensor" || sourceNode.type == "Actor") {
            if (sourceNode.type == "Sensor")
                startPoint = new Point(sourceBounds.x+sourceBounds.width*0.5,
                    sourceBounds.y);
            else
                startPoint = new Point(sourceBounds.x+sourceBounds.width*0.4,
                    sourceBounds.y);
            startAngle = 270;
        } else {
            switch (gate.name){
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
        sourceBounds = sourceNode.bounds;
        startPoint = new Point(sourceBounds.x+sourceBounds.width,
            sourceBounds.y+viewProperties.lineHeight*(gateIndex+2.5)*viewProperties.zoomFactor);
        startAngle = 0;
    }
    return {
        "point": startPoint,
        "angle": startAngle,
        "isPreliminary": startPointIsPreliminary
    }
}

// determine the point where a link enters the node
function calculateLinkEnd(targetNode, slotIndex, linkType) {
    var endPointIsPreliminary = false;
    slot = targetNode.slots[slotIndex];
    if (isCompact(targetNode)) {
        targetBounds = targetNode.bounds;
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
        targetBounds = targetNode.bounds;
        endAngle = 180;
        endPoint = new Point(targetBounds.x,
            targetBounds.y+viewProperties.lineHeight*(slotIndex+2.5)*viewProperties.zoomFactor);
    }
    return {
        "point": endPoint,
        "angle": endAngle,
        "isPreliminary": endPointIsPreliminary
    }
}

// draw link
function renderLink(link) {
    sourceNode = nodes[link.sourceNodeUid];
    targetNode = nodes[link.targetNodeUid];

    linkStart = calculateLinkStart(sourceNode, link.gateIndex);
    linkEnd = calculateLinkEnd(targetNode, link.slotIndex, gate.name);


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

    startDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkStart.angle);
    endDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkEnd.angle);

    arrowPath = createArrow(linkEnd.point, endDirection.angle, link.strokeColor);
    linkPath = createLink(linkStart.point, linkStart.angle, startDirection, linkEnd.point, linkEnd.angle, endDirection, link.strokeColor, link.strokeWidth);

    linkItem = new Group([linkPath, arrowPath]);
    linkItem.name = "link";
    linkContainer = new Group(linkItem);
    linkContainer.name = link.uid;

    linkLayer.addChild(linkContainer);
}

// draw the line part of the link
function createLink(startPoint, startAngle, startDirection, endPoint, endAngle, endDirection, linkColor, linkWidth) {
    arrowEntry = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(endAngle)+endPoint;
    nodeExit = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(startAngle)+startPoint;

    linkPath = new Path([[startPoint],[nodeExit,new Point(0,0),startDirection],[arrowEntry,endDirection]]);
    linkPath.strokeColor = linkColor;
    linkPath.strokeWidth = viewProperties.zoomFactor * linkWidth;
    linkPath.name = "line";
    if (gate.name=="cat" || gate.name == "exp") linkPath.dashArray = [4*viewProperties.zoomFactor,
        3*viewProperties.zoomFactor];
    return linkPath;
}

// draw the arrow head of the link
function createArrow(endPoint, endAngle, arrowColor) {
    arrowPath = new Path(endPoint);
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
    sourceNode = linkCreationStart.sourceNode;
    gateIndex = linkCreationStart.gateIndex;

    linkStart = calculateLinkStart(sourceNode, gateIndex);

    if (linkStart.isPreliminary) { // start from boundary of a compact node
        correctionVector = new Point(sourceBounds.width/2, 0);
        linkStart.angle = (endPoint - linkStart.point).angle;
        linkStart.point += correctionVector.rotate(linkStart.angle-10);
    }

    startDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(linkStart.angle);
    endDirection = new Point(-viewProperties.linkTension*viewProperties.zoomFactor,0);

    arrowPath = createArrow(endPoint, 180, viewProperties.selectionColor);
    linkPath = createLink(linkStart.point, linkStart.angle, startDirection, endPoint, 180, endDirection,
        viewProperties.selectionColor, 2*viewProperties.zoomFactor);

    tempLink = new Group([linkPath, arrowPath]);
    tempLink.name = "tempLink";

    if ("tempLink" in nodeLayer.children) nodeLayer.children["tempLink"].remove();
    nodeLayer.addChild(tempLink);
}

// draw net entity
function renderNode(node) {
    if (isCompact(node)) renderCompactNode(node);
    else renderFullNode(node);
    setActivation(node);
}

// draw net entity with slots and gates
function renderFullNode(node) {
    node.bounds = calculateNodeBounds(node);
    skeleton = createFullNodeSkeleton(node);
    activations = createFullNodeActivations(node);
    titleBar = createFullNodeLabel(node);
    nodeItem = new Group([activations, skeleton, titleBar]);
    nodeItem.name = node.uid;
    nodeLayer.addChild(nodeItem);
}

// render compact version of a net entity
function renderCompactNode(node) {
    node.bounds = calculateNodeBounds(node);
    skeleton = createCompactNodeSkeleton(node);
    activations = createCompactNodeActivations(node);
    label = createCompactNodeLabel(node);
    nodeItem = new Group([activations, skeleton]);
    if (label) nodeItem.addChild(label);
    nodeItem.name = node.uid;
    nodeLayer.addChild(nodeItem);
}

// calculate the dimensions of a node in the current rendering
function calculateNodeBounds(node) {
    if (!isCompact(node)) {
        width = viewProperties.nodeWidth * viewProperties.zoomFactor;
        height = viewProperties.lineHeight*(Math.max(node.slots.length, node.gates.length)+2)*viewProperties.zoomFactor;
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
    bounds = node.bounds;
    switch (node.type) {
        case "Nodespace":
            shape = new Path.Rectangle(bounds);
            break;
        case "Sensor":
            shape = new Path();
            shape.add(bounds.bottomLeft);
            shape.cubicCurveTo(new Point(bounds.x, bounds.y-bounds.height *.3),
                new Point(bounds.right, bounds.y-bounds.height *.3), bounds.bottomRight);
            shape.closePath();
            break;
        case "Actor":
            shape = new Path([bounds.bottomRight,
                new Point(bounds.x+bounds.width *.65, bounds.y),
                new Point(bounds.x+bounds.width *.35, bounds.y),
                new Point(bounds.x+bounds.width *.35, bounds.y),
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
    bounds = node.bounds;
    label = new Group();
    label.name = "titleBarLabel";
    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle (bounds.x+viewProperties.padding*viewProperties.zoomFactor,
        bounds.y,
        bounds.width-2*viewProperties.padding*viewProperties.zoomFactor,
        viewProperties.lineHeight*viewProperties.zoomFactor);
    clipper.clipMask = true;
    label.addChild(clipper);
    label.opacity = 0.99; // clipping workaround to bug in paper.js
    titleText = new PointText(new Point(bounds.x+viewProperties.padding*viewProperties.zoomFactor,
        bounds.y+viewProperties.lineHeight*0.8*viewProperties.zoomFactor));
    titleText.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize*viewProperties.zoomFactor
    };
    titleText.content = node.name ? node.name : node.uid;
    titleText.name = "text";
    label.addChild(titleText);
    return label;
}

// draw a line below the title bar
function createNodeTitleBarDelimiter (node) {
    bounds = node.bounds;
    upper = new Path.Rectangle(bounds.x+viewProperties.shadowDisplacement.x*viewProperties.zoomFactor,
        bounds.y + (viewProperties.lineHeight - viewProperties.strokeWidth)*viewProperties.zoomFactor,
        bounds.width - viewProperties.shadowDisplacement.x*viewProperties.zoomFactor,
        viewProperties.innerShadowDisplacement.y*viewProperties.zoomFactor);
    upper.fillColor = viewProperties.shadowColor;
    upper.fillColor.alpha = 0.3;
    lower = upper.clone();
    lower.position += new Point(0, viewProperties.innerShadowDisplacement.y*viewProperties.zoomFactor);
    lower.fillColor = viewProperties.highlightColor;
    lower.fillColor.alpha = 0.3;
    titleBarDelimiter = new Group([upper, lower]);
    titleBarDelimiter.name = "titleBarDelimiter";
    return titleBarDelimiter;
}

// turn shape into shadowed outline
function createBorder(shape, displacement) {
    highlight = shape.clone();
    highlight.fillColor = viewProperties.highlightColor;
    highlightSubtract = highlight.clone();
    highlightSubtract.position += displacement;
    highlightClipper = highlight.clone();
    highlightClipper.position -= new Point(0.5, 0.5);
    highlightClipper.clipMask = true;
    upper = new Group([highlightClipper, new CompoundPath([highlight, highlightSubtract])]);
    upper.opacity = 0.5;

    shadowSubtract = shape;
    shadowSubtract.fillColor = viewProperties.shadowColor;
    shadow = shadowSubtract.clone();
    shadow.position += displacement;
    shadowClipper = shadow.clone();
    shadowClipper.position += new Point(0.5, 0.5);
    shadowClipper.clipMask = true;
    lower = new Group([shadowClipper, new CompoundPath([shadow, shadowSubtract])]);
    lower.opacity = 0.5;

    border = new Group([lower, upper]);
    border.setName("border");
    return border;
}

// full node body text
function createFullNodeBodyLabel(node) {
    bounds = node.bounds;
    label = new Group();
    label.name = "bodyLabel";
    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle (bounds.x+viewProperties.padding*viewProperties.zoomFactor, bounds.y,
        bounds.width-2*viewProperties.padding*viewProperties.zoomFactor, bounds.height);
    clipper.clipMask = true;
    label.addChild(clipper);
    label.opacity = 0.99; // clipping workaround to bug in paper.js
    typeText = new PointText(new Point(bounds.x+bounds.width/2,
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
    if (!(node.type in prerenderLayer.children)) {
        shape = createFullNodeShape(node);
        border = createBorder(shape, viewProperties.shadowDisplacement*viewProperties.zoomFactor);
        typeLabel = createFullNodeBodyLabel(node);
        titleBarDelimiter = createNodeTitleBarDelimiter(node);
        skeleton = new Group([border, titleBarDelimiter, typeLabel]);
        if (node.slots) {
            for (i = 0; i< node.slots.length; i++)
                skeleton.addChild(createPillsWithLabels(getSlotBounds(node, i), node.slots[i].name));
        }
        if (node.gates) {
            for (i = 0; i< node.gates.length; i++)
                skeleton.addChild(createPillsWithLabels(getGateBounds(node, i), node.gates[i].name));
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
    name = "fullNodeActivation "+node.type;
    if (!(name in prerenderLayer.children)) {
        body = createFullNodeShape(node);
        body.name = "body";
        body.fillColor = viewProperties.nodeColor;
        activation = new Group([body]);
        activation.name = "activation";
        if (node.slots.length) {
            slots = new Group();
            slots.name = "slots";
            for (i = 0; i< node.slots.length; i++) {
                bounds = getSlotBounds(node, i);
                slots.addChild(new Path.RoundRectangle(bounds, bounds.height/2));
            }
            activation.addChild(slots);
        }
        if (node.gates.length) {
            gates = new Group();
            gates.name = "gates";
            for (i = 0; i< node.gates.length; i++) {
                bounds = getGateBounds(node, i);
                gates.addChild(new Path.RoundRectangle(bounds, bounds.height/2));
            }
            activation.addChild(gates);
        }
        container = new Group([activation]);
        container.name = name;
        prerenderLayer.addChild(container);
    }
    activation = prerenderLayer.children[name].firstChild.clone();
    activation.position = node.bounds.center;
    return activation;
}

// render the static part of a compact node
function createCompactNodeSkeleton(node) {
    shape = createCompactNodeShape(node);
    border = createBorder(shape, viewProperties.shadowDisplacement*viewProperties.zoomFactor);
    typeLabel = createCompactNodeBodyLabel(node);
    skeleton = new Group([border, typeLabel]);
    return skeleton;
}

// render the symbol within the compact node body
function createCompactNodeBodyLabel(node) {
    bounds = node.bounds;
    symbolText = new PointText(new Point(bounds.x+bounds.width/2,
        bounds.y+bounds.height/2+viewProperties.symbolSize/2*viewProperties.zoomFactor));
    symbolText.fillColor = viewProperties.nodeForegroundColor;
    symbolText.content = node.symbol;
    symbolText.fontSize = viewProperties.symbolSize*viewProperties.zoomFactor;
    symbolText.paragraphStyle.justification = 'center';
    return symbolText;
}

// render the activation part of a compact node
function createCompactNodeActivations(node) {
    body = createCompactNodeShape(node);
    body.fillColor = viewProperties.nodeColor;
    body.name = "body";
    activation = new Group([body]);
    activation.name = "activation";
    return activation;
}

// create the border of slots and gates, and add the respective label
function createPillsWithLabels(bounds, labeltext) {
    if (!("pillshape" in prerenderLayer.children)) {
        shape = Path.RoundRectangle(bounds, bounds.height/2);
        border = createBorder(shape, viewProperties.innerShadowDisplacement);
        border.name = "pillshape";
        if (viewProperties.rasterize) border = border.rasterize();
        prerenderLayer.addChild(border);
    }
    border = prerenderLayer.children["pillshape"].clone();
    border.position = bounds.center;
    label = new Group();
    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle(bounds);
    clipper.clipMask = true;
    label.addChild(clipper);
    label.opacity = 0.99; // clipping workaround to bug in paper.js
    text = new PointText(bounds.center+new Point(0, viewProperties.lineHeight *0.3));
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
        labelText = new PointText(new Point(bounds.x + node.bounds.width/2,
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
        nodeItem = nodeLayer.children[node.uid];
        node.fillColor = nodeItem.children["activation"].children["body"].fillColor =
            activationColor(node.activation, viewProperties.nodeColor);
        if (!isCompact(node) && (node.slots.length || node.gates.length)) {
            for (i in node.slots) {
                nodeItem.children["activation"].children["slots"].children[i].fillColor =
                    activationColor(node.slots[i].activation,
                    viewProperties.nodeColor);
            }
            for (i in node.gates) {
                nodeItem.children["activation"].children["gates"].children[i].fillColor =
                    activationColor(node.gates[i].activation,
                    viewProperties.nodeColor);
            }
        }
    } else console.log ("node "+node.uid+" not found in current view");
}

// mark node as selected, and add it to the selected nodes
function selectNode(nodeUid) {
    selection[nodeUid] = nodes[nodeUid];
    outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
    outline.strokeColor = viewProperties.selectionColor;
    outline.strokeWidth = viewProperties.outlineWidthSelected*viewProperties.zoomFactor;
}

// remove selection marking of node, and remove if from the set of selected nodes
function deselectNode(nodeUid) {
    if (nodeUid in selection) {
        delete selection[nodeUid];
        outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
        outline.strokeColor = viewProperties.outlineColor;
        outline.strokeWidth = viewProperties.outlineWidth;
    }
}

// mark node as selected, and add it to the selected nodes
function selectLink(linkUid) {
    selection[linkUid] = links[linkUid];
    linkShape = linkLayer.children[linkUid].children["link"];
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
        linkShape = linkLayer.children[linkUid].children["link"];
        linkShape.children["line"].strokeColor = links[linkUid].strokeColor;
        linkShape.children["line"].strokeWidth = links[linkUid].strokeWidth*viewProperties.zoomFactor;
        linkShape.children["arrow"].fillColor = links[linkUid].strokeColor;
        linkShape.children["arrow"].strokeWidth = 0;
        linkShape.children["arrow"].strokeColor = null;
    }
}

// deselect all nodes and links
function deselectAll() {
    for (uid in selection){
        if (uid in nodes) deselectNode(uid);
        if (uid in links) deselectLink(uid);
    }
}

// should we draw this node in compact style or full?
function isCompact(node) {
    if (viewProperties.zoomFactor < viewProperties.forceCompactBelowZoomFactor) return true;
    if (node.type == "Native" || node.type=="Nodespace") return viewProperties.compactModules;
    if (/^Concept|Register|Sensor|Actor/.test(node.type)) return viewProperties.compactNodes;
    return false; // we don't know how to render this in compact form
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
	col = new Color();
	if (activation >0) c = viewProperties.activeColor; else c = viewProperties.inhibitedColor;
	a = Math.abs(activation);
	r = 1.0-a;
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

function onMouseDown(event) {
    path = hoverPath = null;
    p = event.point;
    // first, check for nodes
    // we iterate over all bounding boxes, but should improve speed by maintaining an index
    for (nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            node = nodes[nodeUid];
            bounds = node.bounds;
            if (bounds.contains(p)) {
                path = nodeLayer.children[nodeUid];
                clickOriginUid = nodeUid;
                nodeLayer.addChild(path); // bring to front
                if (!event.modifiers.shift &&
                    !event.modifiers.control && !event.modifiers.command && event.event.button != 2) deselectAll();
                if (event.modifiers.command && nodeUid in selection) deselectNode(nodeUid); // toggle
                else if (!linkCreationStart) selectNode(nodeUid);
                console.log ("clicked node "+nodeUid);
                // check for slots and gates
                if ((i = testSlots(node, p)) >-1) {
                    console.log("clicked slot #" + i);
                    clickType = "slot";
                    clickIndex = i;
                    if (event.modifiers.control || event.event.button == 2) openContextMenu("#slot_menu", event.event);
                    else if (linkCreationStart) finalizeLinkHandler(nodeUid, slotIndex);
                    return;
                } else if ((i = testGates(node, p)) > -1) {
                    console.log("clicked gate #" + i);
                    clickType = "gate";
                    clickIndex = i;
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
        if (event.modifiers.control || event.event.button == 2) openContextMenu("#create_node_menu", event.event);
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
                console.log("clicked link " + path.name);
                clickType = "link";
                clickOriginUid = path.name;
                if (event.modifiers.control || event.event.button == 2) openContextMenu("#link_menu", event.event);
            }
        }
    }
}

var hover = null;
var hoverArrow = null;
var oldHoverColor = null;

function onMouseMove(event) {
    p = event.point;
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
    for (nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            node = nodes[nodeUid];
            bounds = node.bounds;
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
    p = view.viewToProject(DomEvent.getOffset(event, view._canvas))
    for (nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            node = nodes[nodeUid];
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
            for (slotIndex = 0; slotIndex < node.slots.length; slotIndex++) {
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
            for (gateIndex = 0; gateIndex < node.gates.length; gateIndex++) {
                if (getGateBounds(node, gateIndex).contains(p)) return gateIndex;
            }
        }
    }
    return -1;
}

function onMouseDrag(event) {
    // move current node
    if (movePath) {
            path.position += event.delta;
            node = nodes[path.name];
            node.x += event.delta.x/viewProperties.zoomFactor;
            node.y += event.delta.y/viewProperties.zoomFactor;
            node.bounds = calculateNodeBounds(node);
            redrawNodeLinks(node);
    }
}

function onMouseUp(event) {
    if (movePath) {
        updateViewSize();
    }
}



function onKeyDown(event) {
    // support zooming via view.zoom using characters + and -
    if (event.character == "+") {
        viewProperties.zoomFactor += .1;
        redrawNodeNet(currentNodeSpace);
    }
    else if (event.character == "-") {
        if (viewProperties.zoomFactor > .2) viewProperties.zoomFactor -= .1;
        redrawNodeNet(currentNodeSpace);
    }
    // delete nodes and links
    else if (event.key == "backspace" || event.key == "delete") {
        if (event.event.target.tagName == "BODY") {
            deleteNodeHandler();
            deleteLinkHandler();
        }
    }
    else if (event.key == "escape") {
        if (linkCreationStart) cancelLinkCreationHandler();
    }
}

function onResize(event) {
    console.log("resize");
    updateViewSize();
}

// menus -----------------------------------------------------------------------------


function initializeMenus() {
    $(".dropdown-menu").on('click', 'li', handleContextMenu);
    $("#rename_node_modal .btn-primary").on('click', handleRenameNodeModal);
    $("#nodenet").on('dblclick', onDoubleClick);
    $("#nodespace_up").on('click', handleNodespaceUp);
}

var clickPosition = null;

function openContextMenu(menu_id, event) {
    event.cancelBubble = true;
    clickPosition = new Point(event.offsetX, event.offsetY);
    $(menu_id).css({
        position: "absolute",
        zIndex: 500,
        marginLeft: 0, marginTop: 0,
        top: event.pageY, left: event.pageX });
    $(menu_id+" .dropdown-toggle").dropdown("toggle");
}

// build the node menu
function openNodeContextMenu(menu_id, event, nodeUid) {
    menu = $(menu_id+" .dropdown-menu");
    menu.off('click', 'li');
    menu.empty();
    node = nodes[nodeUid];
    if (node.type == "Concept") {
        menu.append('<li><a href="#">Create gen link</a></li>');
        menu.append('<li><a href="#">Create por/ret link</a></li>');
        menu.append('<li><a href="#">Create sub/sur link</a></li>');
        menu.append('<li><a href="#">Create cat/exp link</a></li>');
        menu.append('<li class="divider"></li>');
    } else if (node.gates.length) {
        for (gateIndex in node.gates) {
            menu.append('<li><a href="#">Create '+node.gates[gateIndex].name+' link</a></li>')
        }
        menu.append('<li class="divider"></li>');
    }
    menu.append('<li><a href="#">Rename node</a></li>');
    menu.append('<li><a href="#">Delete node</a></li>');
    menu.on('click', 'li', handleContextMenu);
    openContextMenu(menu_id, event);
}

// universal handler for all context menu events. You can get the origin path from the variable clickTarget.
function handleContextMenu(event) {
    menuText = event.target.text;

    switch (clickType) {
        case null: // create nodes
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
                    break;
                case "Create actor":
                    type = "Actor";
                    break;
                default:
                    type = "Register";
            }
            createNodeHandler(clickPosition.x/viewProperties.zoomFactor, clickPosition.y/viewProperties.zoomFactor,
                currentNodeSpace, "", type);
            break;
        case "node":
            switch (menuText) {
                case "Rename node":
                    nodeUid = clickOriginUid;
                    if (nodeUid in nodes) {
                        $("#rename_node_input").val(nodes[nodeUid].name);
                        $("#rename_node_modal").modal("show");
                        $("#rename_node_input").select();
                        $("#rename_node_input").focus();
                    }
                    break;
                case "Delete node":
                    deleteNodeHandler(clickOriginUid);
                    break;
                default:
                    // link creation
                    if (menuText.substring(0, 6) == "Create" && menuText.indexOf(" link")>0) {
                        createLinkHandler(clickOriginUid, clickIndex, menuText.substring(7, menuText.indexOf(" link")));
                    }
            }
            break;
        case "slot":
            switch (menuText) {
                case "Add monitor to slot":
                    // todo: add monitor to slot
                    break;
            }
            break;
        case "gate":
            switch (menuText) {
                case "Create link":
                    createLinkHandler(clickOriginUid, clickIndex);
                    break;
                case "Add monitor to gate":
                    // todo: add monitor to gate
                    break;
            }
            break;
        case "link":
            switch (menuText) {
                case "Delete link":
                    deleteLinkHandler(clickOriginUid);
                    break;
            }
    }
    view.draw();
}

// let user create a new node
function createNodeHandler(x, y, currentNodespace, name, type) {
    addNode(new Node(makeUuid(), x, y, currentNodeSpace, "", type, 0));
    // todo: tell the server all about it
}

// let user delete the current node, or all selected nodes
function deleteNodeHandler(nodeUid) {
    if (nodeUid in nodes) {
        removeNode(nodes[nodeUid]);
        if (nodeUid in selection) delete selection[nodeUid];
        // todo: tell the server all about it
    }
    for (nodeUid in selection) {
        removeNode(nodes[nodeUid]);
        delete selection[nodeUid];
        // todo: tell the server all about it
    }
}

// let user delete the current link, or all selected links
function deleteLinkHandler(linkUid) {
    if (linkUid in links) {
        removeLink(links[linkUid]);
        if (linkUid in selection) delete selection[linkUid];
        // todo: tell the server all about it
    }
    for (linkUid in selection) {
        removeLink(links[linkUid]);
        delete selection[linkUid];
        // todo: tell the server all about it
    }
}

linkCreationStart = null;

// start the creation of a new link
function createLinkHandler(nodeUid, gateIndex, creationType) {
    if ((nodeUid in nodes) && (nodes[nodeUid].gates.length > gateIndex)){
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
        }
    }
}

// establish the created link
function finalizeLinkHandler(nodeUid, slotIndex) {
    sourceUid = linkCreationStart.sourceNode.uid;
    targetUid = nodeUid;
    gateIndex = linkCreationStart.gateIndex;
    if (!slotIndex || slotIndex < 0) slotIndex = 0;

    if ((targetUid in nodes) &&
        nodes[targetUid].slots && (nodes[targetUid].slots.length > slotIndex) &&
        (targetUid != sourceUid)) {

        targetGates = nodes[targetUid].gates ? nodes[targetUid].gates.length : 0;

        switch (linkCreationStart.creationType) {
            case "por/ret":
                addLink(new Link(sourceUid, 1, targetUid, 0, 1, 1));
                if (targetGates > 2) addLink(new Link(targetUid, 2, sourceUid, 0, 1, 1));
                break;
            case "sub/sur":
                addLink(new Link(sourceUid, 3, targetUid, 0, 1, 1));
                if (targetGates > 4) addLink(new Link(targetUid, 4, sourceUid, 0, 1, 1));
                break;
            case "cat/exp":
                addLink(new Link(sourceUid, 5, targetUid, 0, 1, 1));
                if (targetGates > 6) addLink(new Link(targetUid, 6, sourceUid, 0, 1, 1));
                break;
            case "gen":
                addLink(new Link(sourceUid, 0, targetUid, 0, 1, 1));
                break;
            default:
                addLink(new Link(sourceUid, gateIndex, targetUid, slotIndex, 1, 1));
        }
        // todo: tell the server about it
        cancelLinkCreationHandler();
    }
}

// cancel link creation
function cancelLinkCreationHandler() {
    if ("tempLink" in nodeLayer.children) nodeLayer.children["tempLink"].remove();
    linkCreationStart = null;
}

// handler for renaming the node
function handleRenameNodeModal(event) {
    nodeUid = clickOriginUid;
    if (nodeUid in nodes) {
        nodes[nodeUid].name = $("#rename_node_input").val();
        redrawNode(nodes[nodeUid]);
        $("#rename_node_modal").modal("hide");
        view.draw();
        // todo: tell the server all about it
    }
}

// handler for entering a nodespace
function handleEnterNodespace(nodespaceUid) {
    if (nodespaceUid in nodes) {
        deselectAll();
        c = currentNodeSpace = nodespaceUid;
        $("#nodespace_name").val(nodes[c].name ? nodes[c].name : nodes[c].uid);
        redrawNodeNet();
        view.draw();
    }
}

// handler for entering parent nodespace
function handleNodespaceUp() {
    deselectAll();
    if (nodes[currentNodeSpace].parent) { // not yet root nodespace
        c = currentNodeSpace = nodes[currentNodeSpace].parent;
        $("#nodespace_name").val(nodes[c].name ? nodes[c].name : nodes[c].uid);
        redrawNodeNet();
    }
}

function makeUuid() {
    uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    }); // todo: replace with a uuid fetched from server
    return uuid;
}


/* todo:

 - multi-select by dragging a frame

 - links into invisible nodespaces

 - communicate with server
 - get nodes in viewport
 - get links from visible nodes
 - get individual nodes and links (standard communication should make sure that we get a maximum number of nodes,
 after this restrict it to the visible nodes, but include the linked nodes outside the view)
 - get diffs
 - sent updates of editor to server
 - start and stop simulations
 - handle connection problems

 - editor ui elements
 - multiple viewports
 - creation of agents
 - switching between agents
 - exporting and importing

 - handle double click on node spaces
 - handle data sources and data targets
 - handle native modules
 */