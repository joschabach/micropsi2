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

linkLayer = new Layer();
linkLayer.name = 'LinkLayer';
nodeLayer = new Layer();
nodeLayer.name = 'NodeLayer';
prerenderLayer = new Layer();
prerenderLayer.name = 'PrerenderLayer';
prerenderLayer.visible = false;

currentNodenet = $.cookie('selected_nodenet');  // TODO: fetch from cookie
var currentWorld = 0;       // cookie
var currentNodeSpace = 0;   // cookie

var rootNode = new Node("Root", 0, 0, 0, "Root", "Nodespace");

initializeMenus();
if(currentNodenet){
    setCurrentNodenet(currentNodenet);
} else {
    initializeNodeNet();
}

refreshNodenetList();
function refreshNodenetList(){
    $("#nodenet_list").load("/nodenet_list/"+currentNodenet, function(data){
        $('#nodenet_list .nodenet_select').on('click', function(event){
            event.preventDefault();
            var el = $(event.target);
            var uid = el.attr('data');
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
                $.cookie('selected_nodenet', currentNodenet, { expires: 7, path: '/' });
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

    currentNodeSpace = "Root";

    for (var key in nodes){
        if (key != "Root"){
            delete nodes[key];
        }
    }
    links = {};
    nodeLayer.removeChildren();
    addNode(rootNode);
    linkLayer.removeChildren();

    if (data){
        console.log(data);

        for(var uid in data.nodes){
            console.log('adding node:' + uid);
            addNode(new Node(uid, data.nodes[uid].x, data.nodes[uid].y, "Root", data.nodes[uid].name, data.nodes[uid].type, data.nodes[uid].activation));
        }

        var link;
        for(var index in data.links){
            link = data.links[index];
            // TODO: Decide whether to use gate/slot INDEX or gate/slot NAME
            console.log('adding link: ' + link.sourceNode + ' -> ' + link.targetNode);
            addLink(new Link(link.uid, link.sourceNode, link.sourceGate, link.targetNode, link.targetSlot, link.weight, link.certainty));
        }

    } else {

        addNode(new Node("a1", 150, 150, "Root", "Alice", "Actor", 1));
        addNode(new Node("a2", 350, 150, "Root", "Tom", "Actor", 0.3));
        addLink(new Link("a3", "a1", "gen", "a2", "gen", 1, 1));

    }
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
	this.slots={};
	this.gates={};
    this.parent = nodeSpaceUid; // parent nodespace, default is root
    this.fillColor = null;
    this.bounds = null; // current bounding box (after scaling)
	switch (type) {
        case "Nodespace":
            this.symbol = "NS";
            break;
        case "Sensor":
            this.symbol = "S";
            this.gates.gen = new Gate("gen");
            break;
        case "Actor":
            this.symbol = "A";
            this.slots.gen = new Slot("gen");
            this.gates.gen = new Gate("gen");
            break;
        case "Register":
			this.symbol = "R";
            this.slots.gen = new Slot("gen");
            this.gates.gen = new Gate("gen");
			break;
		case "Concept":
			this.symbol = "C";
            this.slots.gen = new Slot("gen");
            this.gates.gen = new Gate("gen");
			this.gates.por = new Gate("por");
			this.gates.ret = new Gate("ret");
			this.gates.sub = new Gate("sub");
			this.gates.sur = new Gate("sur");
			this.gates.cat = new Gate("cat");
			this.gates.exp = new Gate("exp");
			break;
        default: // native code node (completely custom)
            this.symbol = "Na";
            this.slots.gen = new Slot("gen");
            this.gates.gen = new Gate("gen");
            // TODO: fetch list of slots and gates from server
            break;
	}
    this.slotIndexes = Object.keys(this.slots);
    this.gateIndexes = Object.keys(this.gates);
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
    //check if link already exists
    if (!(link.uid in links)) {
        // add link to source node and target node
        if (nodes[link.sourceNodeUid] && nodes[link.targetNodeUid]) {
            nodes[link.sourceNodeUid].gates[link.gateName].outgoing[link.uid]=link;
            nodes[link.targetNodeUid].slots[link.slotName].incoming[link.uid]=link;
            // check if link is visible
            if (nodes[link.sourceNodeUid].parent == currentNodeSpace ||
                nodes[link.targetNodeUid].parent == currentNodeSpace) {
                renderLink(link);
            }
            links[link.uid] = link;
        } else {
            console.error("Error: Attempting to create link without establishing nodes first");
        }
    } else {
        // if weight or activation change, we need to redraw
        var oldLink = links[link.uid];
        if (oldLink.weight != link.weight ||
            oldLink.certainty != link.certainty ||
            nodes[oldLink.sourceNodeUid].gates[oldLink.gateName].activation !=
                nodes[link.sourceNodeUid].gates[link.gateName].activation) {
            linkLayer.children[link.uid].remove();
            renderLink(link);
        }
    }
}

// delete a link from the array, and from the screen
function removeLink(link) {
    delete links[link.uid];
    if (link.uid in linkLayer.children) linkLayer.children[link.uid].remove();
    delete nodes[link.sourceNodeUid].gates[link.gateName].outgoing[link.uid];
    delete nodes[link.targetNodeUid].slots[link.slotName].incoming[link.uid];
}

// add or update node, should usually be called from the JSON parser
function addNode(node) {
    // check if node already exists
    if (! (node.uid in nodes)) {
        if (node.parent == currentNodeSpace) renderNode(node);
        nodes[node.uid] = node;
    } else {
        var oldNode = nodes[node.uid];

        // if node only updates position or activation, we may save some time
        // import all properties individually; check if we really need to redraw
    }
    view.viewSize.x = Math.max (view.viewSize.x, (node.x + viewProperties.frameWidth)*viewProperties.zoomFactor);
    view.viewSize.y = Math.max (view.viewSize.y, (node.y + viewProperties.frameWidth)*viewProperties.zoomFactor);
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
    var el = view.element.parentElement;
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
    view.viewSize = new Size(Math.max((maxX+viewProperties.frameWidth)*viewProperties.zoomFactor,
        el.clientWidth),
        Math.max((maxY+viewProperties.frameWidth)* viewProperties.zoomFactor,
            el.clientHeight));
}

// complete redraw of the current node space
function redrawNodeNet() {
    console.log("redrawNodeNet");
    nodeLayer.removeChildren();
    linkLayer.removeChildren();
    var i;
    for (i in nodes) {
        if (nodes[i].parent == currentNodeSpace) renderNode(nodes[i]);
    }
    for (i in links) {
        var sourceNode = nodes[links[i].sourceNodeUid];
        var targetNode = nodes[links[i].targetNodeUid];
        // check for source and target nodes, slots and gates
        if (!sourceNode) {
            console.log("Did not find source Node for link from " +
                nodes[links[i].sourceNodeUid] + " to " +
                nodes[links[i].targetNodeUid]);
            continue;
        }
        if (!(links[i].gateName in sourceNode.gates)) {
            console.log("Node "+sourceNode.uid+ "does not have a gate with name "+links[i].gateName);
            continue;
        }
        if (!targetNode) {
            console.log("Did not find target Node for link from " +
                nodes[links[i].sourceNodeUid] + " to " +
                nodes[links[i].targetNodeUid]);
            continue;
        }
        if (!(links[i].slotName in targetNode.slots)) {
            console.log("Node "+targetNode.uid+ " does not have a slot with name "+links[i].slotName);
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
    var linkUid;
    for (var gateName in node.gates) {
        for (linkUid in node.gates[gateName].outgoing) {
            linkLayer.children[linkUid].remove();
            renderLink(links[linkUid]);
        }
    }
    for (var slotName in node.slots) {
        for (linkUid in node.slots[slotName].incoming) {
            linkLayer.children[linkUid].remove();
            renderLink(links[linkUid]);
        }
    }
}

// determine the point where link leaves the node
function calculateLinkStart(sourceNode, gateName) {
    var startPointIsPreliminary = false;
    var gate = sourceNode.gates[gateName];
    // Depending on whether the node is drawn in compact or full shape, links may originate at odd positions.
    // This depends on the node type and the link type.
    // If a link does not have a preferred direction on a compact node, it will point directly from the source
    // node to the target node. However, this requires to know both points, so there must be a preliminary step.
    var sourcePoints, startPoint, startAngle;
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
        var index = sourceNode.gateIndexes.indexOf(gateName);
        sourceBounds = sourceNode.bounds;
        startPoint = new Point(sourceBounds.x+sourceBounds.width,
            sourceBounds.y+viewProperties.lineHeight*(index+2.5)*viewProperties.zoomFactor);
        startAngle = 0;
    }
    return {
        "point": startPoint,
        "angle": startAngle,
        "isPreliminary": startPointIsPreliminary
    };
}

// determine the point where a link enters the node
function calculateLinkEnd(targetNode, slotName, linkType) {
    var endPointIsPreliminary = false;
    var slot = targetNode.slots[slotName];
    var targetBounds, endPoint, endAngle;
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
        var index = targetNode.slotIndexes.indexOf(slotName);
        targetBounds = targetNode.bounds;
        endAngle = 180;
        endPoint = new Point(targetBounds.x,
            targetBounds.y+viewProperties.lineHeight*(index+2.5)*viewProperties.zoomFactor);
    }
    return {
        "point": endPoint,
        "angle": endAngle,
        "isPreliminary": endPointIsPreliminary
    };
}

// draw link
function renderLink(link) {
    var sourceNode = nodes[link.sourceNodeUid];
    var targetNode = nodes[link.targetNodeUid];

    var gate = sourceNode.gates[link.gateName];

    var linkStart = calculateLinkStart(sourceNode, link.gateName);
    var linkEnd = calculateLinkEnd(targetNode, link.slotName, link.gateName);

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

    var linkStart = calculateLinkStart(sourceNode, sourceNode.gateIndexes[gateIndex]);

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
    titleText.content = node.name ? node.name : node.uid;
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
        border.name = "pillshape";
        if (viewProperties.rasterize) border = border.rasterize();
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
        var labelText = new PointText(new Point(bounds.x + node.bounds.width/2,
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
        var outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
        outline.strokeColor = viewProperties.outlineColor;
        outline.strokeWidth = viewProperties.outlineWidth;
    }
}

// mark node as selected, and add it to the selected nodes
function selectLink(linkUid) {
    selection[linkUid] = links[linkUid];
    var linkShape = linkLayer.children[linkUid].children["link"];
    var oldHoverColor = viewProperties.selectionColor;
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

// deselect all nodes and links
function deselectAll() {
    for (var uid in selection){
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
                else if (!linkCreationStart) selectNode(nodeUid);
                console.log ("clicked node "+nodeUid);
                // check for slots and gates
                var i;
                if ((i = testSlots(node, p)) >-1) {
                    console.log("clicked slot #" + i);
                    clickType = "slot";
                    clickIndex = i;
                    if (event.modifiers.control || event.event.button == 2) openContextMenu("#slot_menu", event.event);
                    else if (linkCreationStart) finalizeLinkHandler(nodeUid, clickIndex); // was slotIndex TODO: clickIndex?? linkcreationstart.gateIndex???
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
            moveNode(path.name, nodes[path.name].x, nodes[path.name].y);
        }
        updateViewSize();
    }
}



function onKeyDown(event) {
    // support zooming via view.zoom using characters + and -
    if (event.character == "+") {
        viewProperties.zoomFactor += 0.1;
        redrawNodeNet(currentNodeSpace);
    }
    else if (event.character == "-") {
        if (viewProperties.zoomFactor > 0.2) viewProperties.zoomFactor -= 0.1;
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
    $(".nodenet_menu").on('click', 'li', handleContextMenu);
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
    menu.append('<li><a href="#">Rename node</a></li>');
    menu.append('<li><a href="#">Delete node</a></li>');
    menu.on('click', 'li', handleContextMenu);
    openContextMenu(menu_id, event);
}

// universal handler for all context menu events. You can get the origin path from the variable clickTarget.
function handleContextMenu(event) {
    var menuText = event.target.text;
    switch (clickType) {
        case null: // create nodes
            var type;
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
                    var nodeUid = clickOriginUid;
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
    var uid = makeUuid();
    addNode(new Node(uid, x, y, currentNodeSpace, "", type, 0));
    $.ajax({
        url: '/rpc/add_node('+
            'nodenet_uid="' + currentNodenet + '",' +
            'type="' + type + '",' +
            'x=' + x + ',' +
            'y=' + y + ',' +
            'nodespace="' + currentNodespace + '",' +
            'uid="' + uid + '",' +
            'name="' + uid + '")',
        error: function(data){
            dialogs.notification(data.Error || "Error", "error");
        }
    });
}

// let user delete the current node, or all selected nodes
function deleteNodeHandler(nodeUid) {
    function deleteNodeOnServer(node_uid){
        $.ajax({
            url: '/rpc/delete_node('+
                'nodenet_uid="' + currentNodenet + '",'+
                'node_uid="' + node_uid + '")',
            error: function(data){
                dialogs.notification(data.Error || "Error removing Node", "error");
            }
        });
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
}

// let user delete the current link, or all selected links
function deleteLinkHandler(linkUid) {
    function removeLinkOnServer(linkUid){
        var url = '/rpc/delete_link('+
                'nodenet_uid="'+ currentNodenet +'",'+
                'link_uid="'+ linkUid +'")';
        $.ajax({
            url: url,
            error: function(data){
                dialogs.notification(data.Error || "Error removing link", "error");
            },
            success: function(data){
                dialogs.notification('Link removed', 'success');
            }
        });
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
        $.ajax({
            url: '/rpc/add_link('+
                'nodenet_uid="' + currentNodenet + '",' +
                'source_node_uid="' + sourceUid + '",' +
                'gate_type="' + nodes[sourceUid].gateIndexes[gateIndex] + '",' +
                'target_node_uid="' + targetUid + '",' +
                'slot_type="' + nodes[targetUid].slotIndexes[slotIndex] + '",' +
                'weight=1,'+
                'uid="'+ uuid +'")',
            error: function(data){
                dialogs.notification(data.Error || "Error", "error");
            }
        });
        // todo: tell the server about it
        cancelLinkCreationHandler();
    }
}

// cancel link creation
function cancelLinkCreationHandler() {
    if ("tempLink" in nodeLayer.children) nodeLayer.children["tempLink"].remove();
    linkCreationStart = null;
}

function moveNode(nodeUid, x, y){
    $.ajax({
        url: '/rpc/set_node_parameters('+
            'nodenet_uid="'+currentNodenet+'",'+
            'node_uid="'+nodeUid+'",'+
            'x='+x+',y='+y+')',
        success: function(data){
            dialogs.notification('node moved', 'success');
        },
        error: function(data){
            dialogs.notification('error moving node', 'error');
        }
    });
}

// handler for renaming the node
function handleRenameNodeModal(event) {
    var nodeUid = clickOriginUid;
    if (nodeUid in nodes) {
        nodes[nodeUid].name = $("#rename_node_input").val();
        redrawNode(nodes[nodeUid]);
        $("#rename_node_modal").modal("hide");
        view.draw();
        $.ajax({
            url: '/rpc/set_node_parameters('+
                'nodenet_uid="'+currentNodenet+'",'+
                'node_uid="'+nodeUid+'",'+
                'name="'+nodes[nodeUid].name+'")',
            success: function(data){
                dialogs.notification('node renamed', 'success');
            },
            error: function(data){
                dialogs.notification('error renaming node', 'error');
            }
        });
    }
}

// handler for entering a nodespace
function handleEnterNodespace(nodespaceUid) {
    if (nodespaceUid in nodes) {
        deselectAll();
        currentNodeSpace = nodespaceUid;
        var c = currentNodeSpace;
        $("#nodespace_name").val(nodes[c].name ? nodes[c].name : nodes[c].uid);
        redrawNodeNet();
        view.draw();
    }
}

// handler for entering parent nodespace
function handleNodespaceUp() {
    deselectAll();
    if (nodes[currentNodeSpace].parent) { // not yet root nodespace
        currentNodeSpace = nodes[currentNodeSpace].parent;
        var c = currentNodeSpace;
        $("#nodespace_name").val(nodes[c].name ? nodes[c].name : nodes[c].uid);
        redrawNodeNet();
    }
}

function makeUuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    }); // todo: replace with a uuid fetched from server
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