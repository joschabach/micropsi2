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
    fontSize: 8.5,
    symbolSize: 14,
    nodeWidth: 84,
    compactNodeWidth: 32,
    cornerWidth: 6,
    padding: 5,
    slotWidth: 34,
    lineHeight: 15,
    compactNodes: false,
    compactModules: false,
    strokeWidth: 0.3,
    outlineColor: null,
    outlineWidth: 0.3,
    outlineWidthSelected: 2.0,
    lightColor: new Color ("#ffffff"),
    gateShadowColor: new Color("#888888"),
    shadowColor: new Color ("#000000"),
    shadowStrokeWidth: 0,
    shadowDisplacement: new Point(0.3,1),
    linkTension: 50,
    linkRadius: 30,
    arrowWidth: 6,
    arrowLength: 10
};

// hashes from uids to object definitions; we import these via json
nodes = {};
links = {};
selection = {};

var selectionLayer = new Layer();
var linkLayer = new Layer();
var nodeLayer = new Layer();

var currentNodeSpace = 0;


view.viewSize = new Size(1800,1800);

initializeNodeNet();



function initializeNodeNet(){
    // fetch visible nodes and links
    addNode(new Node("abcd", 142, 332, 0, "My first node", "Actor", 0.3));
    addNode(new Node("sdff", 300, 100, 0, "Otto", "Concept", 0.0));
    addNode(new Node("deds", 350, 180, 0, "Carl", "Native", 0.5));
    addLink(new Link("abcd", 0, "sdff", 0, 1, 1));
    addLink(new Link("sdff", 0, "abcd", 0, 1, 1));
    addLink(new Link("sdff", 1, "deds", 0, 1, 1));
    updateViewSize();
}

function updateViewSize() {
    // adapt the size of the current view to the contained nodes and the canvas size
    var maxX = maxY = 0;
    var frameWidth = viewProperties.frameWidth*viewProperties.zoomFactor;
    for (nodeUid in nodes) {
        node = nodes[nodeUid];
        // make sure no node gets lost to the top or left
        node.x = Math.max(frameWidth, node.x);
        node.y = Math.max(frameWidth, node.y);
        maxX = Math.max(maxX, node.x);
        maxY = Math.max(maxY, node.y);
    }
    view.viewSize = new Size(Math.max((maxX+viewProperties.frameWidth)*viewProperties.zoomFactor, view.canvas.parentElement.clientWidth),
        Math.max((maxY+viewProperties.frameWidth)* viewProperties.zoomFactor, view.canvas.parentElement.clientHeight));
}



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
	switch (type) {
        case "Nodespace":
            this.symbol = "NS";
            break;
        case "Native":
            this.symbol = "Na";
            this.slots.push(new Slot("gen"));
            this.gates.push(new Gate("gen"));
            // TODO: fetch list of slots and gates from server
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
}

/* todo:
 - selection of node
 - deselect by clicking in background
 - multi-select of nodes with shift
 - toggle selct with ctrl
 - multi-select by dragging a frame
 - delete node

 - links into invisible nodespaces
 - select link
 - deselect link
 - delete link

 - context menu
 - add node w type
 - add link w type
 - add link from gate
 - add link via dialog

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
 - scaling of viewport
 - multiple viewports
 - creation of agents
 - switching between agents
 - exporting and importing
  */



function redrawNodeNet(currentNodeSpace) {
    // complete redraw of the current node space
    if (nodeLayer) nodeLayer.removeChildren();
    if (linkLayer) linkLayer.removeChildren();
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
        if (sourceNode.gates.length < links[i].slotIndex) {
            console.log("Node "+sourceNode.uid+ "does not have a slot with index "+links[i].slotIndex);
            continue;
        }
        if (!targetNode) {
            console.log("Did not find target Node for link from "
                +nodes[links[i].sourceNodeUid]+" to "
                +nodes[links[i].targetNodeUid]);
            continue;
        }
        if (targetNode.gates.length < links[i].gateIndex) {
            console.log("Node "+targetNode.uid+ " does not have a gate with index "+links[i].gateIndex);
            continue;
        }
        // check if the link is visible
        if (sourceNode.parent == currentNodeSpace || targetNode.parent == currentNodeSpace) {
            renderLink(links[i]);
        }
    }
    updateViewSize();
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

function removeNode(node) {
    // remove the node from screen, get rid of orphan links, and from hash
    if (node.uid in nodeLayer.children) {
        nodeLayer.children[node.uid].remove();
        for (gateIndex in node.gates) {
            for (linkUid in node.gates[gateIndex].outgoing) {
                delete links[linkUid];
                linkLayer.children[linkUid].remove();
            }
        }
        for (slotIndex in node.slots) {
            for (linkUid in node.slots[slotIndex].incoming) {
                delete links[linkUid];
                linkLayer.children[linkUid].remove();
            }
        }
    }
    delete nodes[node.uid];
}


function setNodePosition(node) {
    // like activation change, only put the node elsewhere and redraw the links
    nodeLayer.children[node.uid].remove();
    renderNode(node);
    redrawNodeLinks(node);
}

function redrawNodeLinks(node) {
    // redraw only the links that are connected to the given node
    for (gateIndex in node.gates) {
        for (linkUid in node.gates[gateIndex].outgoing) {
            linkLayer.children[linkUid].remove();
            renderLink(node.gates[gateIndex].outgoing[linkUid]);
        }
    }
    for (slotIndex in node.slots) {
        for (linkUid in node.slots[slotIndex].incoming) {
            linkLayer.children[linkUid].remove();
            renderLink(node.slots[slotIndex].incoming[linkUid]);
        }
    }
}

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

function removeLink(link) {
    // delete a link from the array, and from the screen
    delete links[link.uid];
    if (nodes[link.sourceNodeUid].parent == currentNodeSpace ||
        nodes[link.targetNodeUid].parent == currentNodeSpace) {
        linkLayer.children[link.uid].remove();
    }
    delete nodes[link.sourceNodeUid].gates[link.gateIndex].outgoing[link.uid];
    delete nodes[link.targetNodeUid].slots[link.slotIndex].incoming[link.uid];
}



function renderLink(link) {
    // draw link
    sourceNode = nodes[link.sourceNodeUid];
    targetNode = nodes[link.targetNodeUid];

    gate = sourceNode.gates[link.gateIndex];
    linkType = gate.name;

    startPointIsPreliminary = false;
    endPointIsPreliminary = false;

    // Depending on whether the node is drawn in compact or full shape, links may originate at odd positions.
    // This depends on the node type and the link type.
    // If a link does not have a preferred direction on a compact node, it will point directly from the source
    // node to the target node. However, this requires to know both points, so there must be a preliminary step.
    if (isCompact(sourceNode)) {
        sourceBounds = calculateCompactNodeDimensions(sourceNode);
        if (sourceNode.type=="Sensor" || sourceNode.type == "Actor") {
            if (sourceNode.type == "Sensor")
                startPoint = new Point(sourceBounds.x+sourceBounds.width*0.5*viewProperties.zoomFactor,sourceBounds.y);
            else
                startPoint = new Point(sourceBounds.x+sourceBounds.width*0.4*viewProperties.zoomFactor, sourceBounds.y);
            startAngle = 270;
        } else {
            switch (linkType){
                case "por":
                    startPoint = new Point(sourceBounds.x + sourceBounds.width*viewProperties.zoomFactor,
                        sourceBounds.y + sourceBounds.height*0.4*viewProperties.zoomFactor);
                    startAngle = 0;
                    break;
                case "ret":
                    startPoint = new Point(sourceBounds.x,
                        sourceBounds.y + sourceBounds.height*0.6*viewProperties.zoomFactor);
                    startAngle = 180;
                    break;
                case "sub":
                    startPoint = new Point(sourceBounds.x + sourceBounds.width*0.6*viewProperties.zoomFactor,
                        sourceBounds.y+ sourceBounds.height*viewProperties.zoomFactor);
                    startAngle = 90;
                    break;
                case "sur":
                    startPoint = new Point(sourceBounds.x + sourceBounds.width*0.4*viewProperties.zoomFactor,
                        sourceBounds.y);
                    startAngle = 270;
                    break;
                default:
                    startPoint = new Point(sourceBounds.x + sourceBounds.width*0.5*viewProperties.zoomFactor,
                        sourceBounds.y + sourceBounds.height*0.5*viewProperties.zoomFactor);
                    startPointIsPreliminary = true;
                    break;
            }
        }
    } else {
        sourceBounds = calculateFullNodeDimensions(sourceNode);
        startPoint = new Point(sourceBounds.x+sourceBounds.width*viewProperties.zoomFactor,
            sourceBounds.y+viewProperties.lineHeight*(link.gateIndex+2.5)*viewProperties.zoomFactor);
        startAngle = 0;
    }
    if (isCompact(targetNode)) {
        targetBounds = calculateCompactNodeDimensions(targetNode);
        if (targetNode.type=="Sensor" || targetNode.type == "Actor") {
            endPoint = new Point(targetBounds.x + targetBounds.width*0.6*viewProperties.zoomFactor, targetBounds.y);
            endAngle = 270;
        } else {
            switch (linkType){
                case "por":
                    endPoint = new Point(targetBounds.x,
                        targetBounds.y + targetBounds.height*0.4*viewProperties.zoomFactor);
                    endAngle = 180;
                    break;
                case "ret":
                    endPoint = new Point(targetBounds.x + targetBounds.width*viewProperties.zoomFactor,
                        targetBounds.y + targetBounds.height*0.6*viewProperties.zoomFactor);
                    endAngle = 0;
                    break;
                case "sub":
                    endPoint = new Point(targetBounds.x + targetBounds.width*0.6*viewProperties.zoomFactor,
                        targetBounds.y);
                    endAngle = 270;
                    break;
                case "sur":
                    endPoint = new Point(targetBounds.x + targetBounds.width*0.4*viewProperties.zoomFactor,
                        targetBounds.y + targetBounds.height*viewProperties.zoomFactor);
                    endAngle = 90;
                    break;
                default:
                    endPoint = new Point(targetBounds.x + targetBounds.width*0.5*viewProperties.zoomFactor,
                        targetBounds.y + targetBounds.height*0.5*viewProperties.zoomFactor);
                    endPointIsPreliminary = true;
                    break;
            }
        }
    } else {
        targetBounds = calculateFullNodeDimensions(targetNode);
        endAngle = 180;
        endPoint = new Point(targetBounds.x, targetBounds.y+viewProperties.lineHeight*(link.slotIndex+2.5)*viewProperties.zoomFactor);
    }
    if (startPointIsPreliminary) { // start from boundary of a compact node
        correctionVector = new Point(sourceBounds.width/2*viewProperties.zoomFactor, 0);
        startAngle = (endPoint - startPoint).angle;
        startPoint += correctionVector.rotate(startAngle-10);
    }
    if (endPointIsPreliminary) { // end at boundary of a compact node
        correctionVector = new Point(sourceBounds.width/2*viewProperties.zoomFactor, 0);
        endAngle = (startPoint-endPoint).angle;
        endPoint += correctionVector.rotate(endAngle+10);
    }

    linkWeight = Math.max(0.1, Math.min(1.0, Math.abs(link.weight)));
    linkColor = activationColor(gate.activation * link.weight, viewProperties.linkColor);

    startDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(startAngle);
    endDirection = new Point(viewProperties.linkTension*viewProperties.zoomFactor,0).rotate(endAngle);

    arrowPath = new Path(endPoint);
    arrowPath.lineBy(new Point(viewProperties.arrowLength, viewProperties.arrowWidth/2));
    arrowPath.lineBy(new Point(0, -viewProperties.arrowWidth));
    arrowPath.closePath();
    arrowPath.scale(viewProperties.zoomFactor, endPoint);
    arrowPath.rotate(endDirection.angle, endPoint);
    arrowPath.fillColor = linkColor;
    arrowPath.name = "arrow";

    arrowEntry = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(endAngle)+endPoint;
    nodeExit = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(startAngle)+startPoint;

    linkPath = new Path([[startPoint],[nodeExit,new Point(0,0),startDirection],[arrowEntry,endDirection]]);
    linkPath.strokeColor = linkColor;
    linkPath.strokeWidth = viewProperties.zoomFactor * linkWeight;
    linkPath.name = "line";
    if (gate.name=="cat" || gate.name == "exp") linkPath.dashArray = [4*viewProperties.zoomFactor,3*viewProperties.zoomFactor];

    linkItem = new Group([linkPath, arrowPath]);
    linkItem.name = "link";
    linkContainer = new Group(linkItem);
    linkContainer.name = link.uid;

    linkLayer.addChild(linkContainer);
}

// draw net entity
function renderNode(node) {
    if (isCompact(node)) renderCompactNode(node);
    else renderFullNode(node);
    setActivation(node);
}

// draw net entity with slots and gates
function renderFullNode(node) {
    bounds = calculateFullNodeDimensions(node);
    shape = createFullNodeShape(node, bounds);
    shadow = createNodeShadow(shape);
    body = createFullNodeBody(node, shape, bounds);
    titleBar = createNodeTitleBar(node, bounds);
    titleBarDelimiter = createNodeTitleBarDelimiter(bounds);
    slots = createNodeSlots(node, bounds);
    gates = createNodeGates(node, bounds);
    outline = createNodeOutline(shape);
    // define structure of the node
    nodeItem = new Group([shadow, body, titleBar, titleBarDelimiter]);
    if (slots) nodeItem.addChild(slots);
    if (gates) nodeItem.addChild(gates);
    nodeItem.addChild(outline);
    nodeItem.name = "node";
    nodeContainer = new Group(nodeItem);
    nodeContainer.name = node.uid;
    nodeContainer.scale(viewProperties.zoomFactor, bounds.point);
    nodeLayer.addChild(nodeContainer);
}

// render compact version of a net entity
function renderCompactNode(node) {
    bounds = calculateCompactNodeDimensions(node);

    shape = createCompactNodeShape(node, bounds);
    body = createCompactNodeBody(node, shape, bounds);
    shadow = createNodeShadow(shape);
    label = createCompactNodeLabel(node, bounds);
    outline = createNodeOutline(shape);

    // define structure of the node
    nodeItem = new Group([shadow, body]);
    nodeItem.addChild(outline);
    if (label) nodeItem.addChild(label);
    nodeItem.name = "node";
    nodeContainer = new Group(nodeItem);
    nodeContainer.name = node.uid;
    nodeContainer.scale(viewProperties.zoomFactor, bounds.point);
    nodeLayer.addChild(nodeContainer);
}

// calculate dimensions of a fully rendered node
function calculateFullNodeDimensions(node) {
    width = viewProperties.nodeWidth;
    height = viewProperties.lineHeight*(Math.max(node.slots.length, node.gates.length)+2);
    if (node.type == "Nodespace") height = Math.max(height, viewProperties.lineHeight*4);
    return new Rectangle((node.x-width/2)*viewProperties.zoomFactor,
                         (node.y-height/2)*viewProperties.zoomFactor, // center node on origin
                         width, height);
}

// calculate dimensions of a node rendered in compact mode
function calculateCompactNodeDimensions(node) {
    width = viewProperties.compactNodeWidth;
    height = viewProperties.compactNodeWidth;
    return new Rectangle(node.x* viewProperties.zoomFactor-width/2,
        node.y*viewProperties.zoomFactor-height/2, // center node on origin
        width, height);
}

// determine shape of a full node
function createFullNodeShape(node, bounds) {
    if (node.type == "Nodespace") return new Path.Rectangle(bounds);
    else return new Path.RoundRectangle(bounds, viewProperties.cornerWidth);
}

// determine shape of a compact node
function createCompactNodeShape(node, bounds) {
    switch (node.type) {
        case "Nodespace":
            shape = new Path.Rectangle(bounds);
            break;
        case "Native":
            shape = new Path.RoundRectangle(bounds, viewProperties.cornerWidth);
            break;
        case "Sensor":
            shape = new Path();
            shape.add(bounds.bottomLeft);
            shape.cubicCurveTo(new Point(bounds.x, bounds.y-bounds.height *.3),
                new Point(bounds.right, bounds.y-bounds.height *.3), bounds.bottomRight);
            shape.closePath();
            break;
        case "Actor":
            shape = new Path();
            shape.add(bounds.bottomLeft);
            shape.lineTo(new Point(bounds.x+bounds.width *.35, bounds.y));
            shape.lineTo(new Point(bounds.x+bounds.width *.65, bounds.y));
            shape.lineTo(bounds.bottomRight);
            shape.closePath();
            break;
        default: // draw circle
            shape = new Path.Circle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
    }
    return shape;
}

// draw title bar shape of a full node
function createNodeTitleBar(node, bounds) {
    titleBarBounds = new Rectangle(bounds.x, bounds.y, bounds.width, viewProperties.lineHeight);
    if (node.type == "Nodespace") titleBar = new Path.Rectangle(titleBarBounds);
    else { // draw rounded corners
        titleBar = new Path();
        titleBar.add(new Point(bounds.x, bounds.y+viewProperties.cornerWidth));
        titleBar.quadraticCurveTo(bounds.point, new Point(bounds.x+viewProperties.cornerWidth, bounds.y));
        titleBar.lineTo(new Point(bounds.right - viewProperties.cornerWidth, bounds.y));
        titleBar.quadraticCurveTo(bounds.topRight, new Point(bounds.right, bounds.y+viewProperties.cornerWidth));
        titleBar.lineTo(titleBarBounds.bottomRight);
        titleBar.lineTo(titleBarBounds.bottomLeft);
        titleBar.closePath();
    }
    titleBar.name = "titleBarBackground";
    //titleBar.fillColor = viewProperties.nodeLabelColor;

    // title bar text
    label = new Group();
    label.name = "titleBarLabel";
    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle (bounds.x+viewProperties.padding, bounds.y,
        bounds.width-2*viewProperties.padding, viewProperties.lineHeight);
    clipper.clipMask = true;
    label.addChild(clipper);
    label.opacity = 0.99; // clipping workaround to bug in paper.js
    titleText = new PointText(new Point(bounds.x+viewProperties.padding, bounds.y+viewProperties.lineHeight*0.8));
    titleText.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize
    };
    titleText.content = node.name.length ? node.name : node.uid;
    titleText.name = "text";
    label.addChild(titleText);
    titleBarGroup = new Group([titleBar, label]);
    titleBarGroup.name = "titleBar";

    return titleBarGroup;
}

// draw a line below the title bar
function createNodeTitleBarDelimiter (bounds) {
    upper = new Path.Line(bounds.x, bounds.y + viewProperties.lineHeight -viewProperties.strokeWidth,
        bounds.right, bounds.y + viewProperties.lineHeight - viewProperties.strokeWidth);
    upper.strokeWidth = viewProperties.strokeWidth * viewProperties.zoomFactor;
    upper.strokeColor = viewProperties.nodeForegroundColor;
    lower = new Path.Line(bounds.x, bounds.y + viewProperties.lineHeight,
        bounds.right, bounds.y + viewProperties.lineHeight);
    lower.strokeWidth = viewProperties.strokeWidth * viewProperties.zoomFactor;
    lower.strokeColor = viewProperties.lightColor;
    titleBarDelimiter = new Group([upper, lower]);
    titleBarDelimiter.name = "titleBarDelimiter";
    return titleBarDelimiter;
}

// draw shadow of a node
function createNodeShadow(outline) {
    shadow = outline.clone();
    shadow.position += viewProperties.shadowDisplacement;
    shadow.name = "shadow";
    shadow.fillColor = viewProperties.shadowColor;
    shadow.fillColor.alpha = 0.5;
    return shadow;
}

// draw background, with activation of the node
function createFullNodeBody(node, outline, bounds) {
    activation = outline.clone();
    activation.name = "activation";
    activation.fillColor = activationColor(node.activation, viewProperties.nodeColor);
    activation.fillColor.alpha = 0.8;

    // body text
    label = new Group();
    label.name = "bodyLabel";
    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle (bounds.x+viewProperties.padding, bounds.y,
        bounds.width-2*viewProperties.padding, bounds.height);
    clipper.clipMask = true;
    label.addChild(clipper);
    label.opacity = 0.99; // clipping workaround to bug in paper.js
    typeText = new PointText(new Point(bounds.x+bounds.width/2, bounds.y+viewProperties.lineHeight*1.8));
    typeText.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize
    };
    typeText.paragraphStyle.justification = 'center';
    typeText.content = node.type;
    typeText.name = "text";
    label.addChild(typeText);

    body = new Group([activation, label]);
    body.name = "body";

    return body;
}


// draw background, with activation of the node
function createCompactNodeBody(node, outline, bounds) {
    activation = outline.clone();
    activation.name = "activation";
    activation.fillColor = activationColor(node.activation, viewProperties.nodeColor);
    symbolText = new PointText(new Point(bounds.x+bounds.width/2,
        bounds.y+bounds.height/2+viewProperties.symbolSize/2));
    symbolText.fillColor = viewProperties.nodeForegroundColor;
    symbolText.content = node.symbol;
    symbolText.fontSize = viewProperties.symbolSize;
    symbolText.paragraphStyle.justification = 'center';
    body = new Group([activation, symbolText]);
    body.name = "body";
    return body;
}

// draw slots of a node
function createNodeSlots(node, bounds) {
    if (node.slots.length) {
        slotStart = new Point(bounds.x+viewProperties.strokeWidth+viewProperties.lineHeight/2,
            bounds.y+2*viewProperties.lineHeight);
        slot = createNodeGateElement(slotStart, "slot", node.slots[0].name);
        slots = new Group(slot);
        slots.name = "slots";
        offset = new Point (0, viewProperties.lineHeight);
        for (i=1; i<node.slots.length; i++) {
            slot = slots.lastChild.clone();
            slot.position+=offset;
            slot.children["label"].children["text"].content=node.slots[i].name;
            slots.addChild(slot);
        }
        return slots;
    }
    else return null;
}

// draw gates of a node
function createNodeGates(node, bounds) {
    if (node.gates.length) {
        gateStart = new Point(bounds.x+viewProperties.lineHeight/2+bounds.width-viewProperties.slotWidth,
            bounds.y+2*viewProperties.lineHeight);
        gate = createNodeGateElement(gateStart, "gate", node.gates[0].name);
        gates = new Group(gate);
        gates.name = "gates";
        offset = new Point (0, viewProperties.lineHeight);
        for (i=1; i<node.gates.length; i++) {
            gate = gates.lastChild.clone();
            gate.position+=offset;
            gate.children["label"].children["text"].content=node.gates[i].name;
            gates.addChild(gate);
        }
        return gates;
    }
    else return null;
}

// draw the shape of an individual gate or slot
function createNodeGateElement(startPoint, type, labelText) {
    pillBounds = new Rectangle(startPoint.x, startPoint.y+1, viewProperties.slotWidth - viewProperties.lineHeight,
        viewProperties.lineHeight - 2);
    pill = new Path();
    pill.add(pillBounds.bottomLeft);
    pill.arcTo(pillBounds.topLeft);
    pill.lineTo(pillBounds.topRight);
    pill.arcTo(pillBounds.bottomRight);
    pill.closePath();
    pill.fillColor = viewProperties.gateShadowColor;
    pill.fillColor.alpha = 0.8;
    pill.name = "shadow";
    activation = pill.clone();
    activation.position -= viewProperties.shadowDisplacement;
    activation.fillColor = viewProperties.nodeColor;
    activation.name = "activation";

    label = new Group();
    label.name = "label";

    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle (pillBounds);
    clipper.clipMask = true;
    label.addChild(clipper);
    label.opacity = 0.99; // clipping workaround to bug in paper.js
    slotText = new PointText(startPoint.x+(viewProperties.slotWidth - viewProperties.lineHeight)/2,
        startPoint.y + viewProperties.lineHeight/1.5);
    slotText.characterStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize
    };
    slotText.paragraphStyle.justification = 'center';
    slotText.content = labelText;
    slotText.name = "text";
    label.addChild(slotText);

    nodeGateElement = new Group([pill, activation, label]);
    nodeGateElement.name = type;

    return nodeGateElement;
}

// draw the label of a compact node
function createCompactNodeLabel(node, bounds) {
    if (node.name.length) { // only display a label for named nodes
        labelText = new PointText(new Point(bounds.x + bounds.width/2,
            bounds.bottom+viewProperties.lineHeight/viewProperties.zoomFactor));
        labelText.content = node.name;
        labelText.characterStyle = {
            fontSize: viewProperties.fontSize/viewProperties.zoomFactor,
            fillColor: viewProperties.nodeForegroundColor
        };
        labelText.paragraphStyle.justification = 'center';
        labelText.name = "labelText";
        return labelText;
    }
    return null;
}

// draw outline of a node
function createNodeOutline(shape) {
    shape.name = "outline";
    shape.strokeColor = viewProperties.outlineColor;
    shape.strokeWidth = viewProperties.outlineWidth * viewProperties.zoomFactor;
    return shape;
}

// update activation in node background, slots and gates
function setActivation(node) {
    if (node.parent!=currentNodeSpace) return; // only do this is the node is visible

    nodeView = nodeLayer.children[node.uid];
    if (nodeView) {
        nodeItem = nodeView.children["node"];
        nodeItem.children["body"].children["activation"].fillColor =
            activationColor(node.activation, viewProperties.nodeColor);
        if (!isCompact(node) && (node.slots.length || node.gates.length)) {
            for (i in node.slots) {
                nodeItem.children["slots"].children[i].children["activation"].fillColor =
                    activationColor(node.slots[i].activation,
                    viewProperties.nodeColor);
            }
            for (i in node.gates) {
                nodeItem.children["gates"].children[i].children["activation"].fillColor =
                    activationColor(node.gates[i].activation,
                    viewProperties.nodeColor);
            }
        }
    } else console.log ("node "+node.uid+" not found in current view");
}

// mark node as selected, and add it to the selected nodes
function selectNode(nodeUid) {
    selection[nodeUid] = nodes[nodeUid];
    outline = nodeLayer.children[nodeUid].children["node"].children["outline"];
    outline.strokeColor = viewProperties.selectionColor;
    outline.strokeWidth = viewProperties.outlineWidthSelected;
}

function deselectNode(nodeUid) {
    if (nodeUid in selection) {
        delete selection[nodeUid];
        outline = nodeLayer.children[nodeUid].children["node"].children["outline"];
        outline.strokeColor = viewProperties.outlineColor;
        outline.strokeWidth = viewProperties.outlineWidth;
    }
}

// should we draw this node in compact style or full?
function isCompact(node) {
    if (viewProperties.zoomFactor < 0.5) return true; // you cannot read this anyway
    if (node.type == "Native" || node.type=="Nodespace") return viewProperties.compactModules;
    if (/^Concept|Register|Sensor|Actor/.test(node.type)) return viewProperties.compactNodes;
    return false; // we don't know how to render this in compact form
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

// ----

var hitOptions = {
    segments: false,
    stroke: true,
    fill: true,
    tolerance: 5
};

var path, hoverPath;
var movePath = false;
function onMouseDown(event) {
    path = hoverPath = null;
    var hitResult = project.hitTest(event.point, hitOptions);

    if (event.modifiers.shift) {
        //
        return;
    }
    console.log(event);
    if (!hitResult) {
        movePath = false;
        // deselect all
        for (nodeUid in selection){
            deselectNode(nodeUid);
        }

    }
    else {
        path = hitResult.item;
        if (hitResult.type == 'stroke' || hitResult.type =="fill") {
            while(path!=project && !/^node|link|gate|slot/.test(path.name) && path.parent) path = path.parent;

            if (path.name == "slot") {
                console.log("clicked slot #" + path.index);
                while (path!=project && path.name!="node") path = path.parent;
            }
            if (path.name == "gate") {
                console.log("clicked gate #" + path.index);
                while (path!=project && path.name!="node") path = path.parent;
            }
            if (path.name == "link") {
                path = path.parent;
                console.log("clicked link " + path.name);
            }
            if (path.name=="node") {
                path = path.parent;
                nodeLayer.addChild(path);
                movePath = true;
                selectNode(path.name);
                console.log ("clicked node "+path.name);
            }
        }
    }
}

var hover = null;
var hoverArrow = null;
var oldHoverColor = null;
var previousItem = null;

function onMouseMove(event) {
    // hover
    var hitResult = project.hitTest(event.point, hitOptions);
    if (hitResult) {
        if (hitResult.item == previousItem) return;
        else previousItem = hitResult.item;
    }

    if (hover) {
        if (hover.name == "activation") hover.fillColor = oldHoverColor;
        else {
            hover.strokeColor = oldHoverColor;
            hoverArrow.fillColor = oldHoverColor;
        }
        hover = null;
    }
    if (hitResult && hitResult.item) {
        path = hitResult.item;
        while(path!=project && !/^node|link|gate|slot/.test(path.name) && path.parent) path = path.parent;
        if (path.name == "slot") {
            console.log("hovering at slot #" + path.index);
            hover = path.children["activation"];
            oldHoverColor = hover.fillColor;
            hover.fillColor = viewProperties.hoverColor;
        }
        if (path.name == "gate") {
            console.log("hovering at gate #" + path.index);
            hover = path.children["activation"];
            oldHoverColor = hover.fillColor;
            hover.fillColor = viewProperties.hoverColor;
        }
        if (path.name == "node") {
            console.log("hovering at node " + path.parent.name);
            hover = path.children["body"].children["activation"];
            oldHoverColor = hover.fillColor;
            hover.fillColor = viewProperties.hoverColor;
            //hover.selected=true;
        }
        if (path.name == "link") {
            console.log("hovering at link " + path.parent.name);
            hover = path.children["line"];
            oldHoverColor = hover.strokeColor;
            hover.strokeColor = viewProperties.hoverColor;
            hoverArrow = path.children["arrow"];
            hoverArrow.fillColor = viewProperties.hoverColor;
        }
    }
}

function onMouseDrag(event) {
    // move current node
    if (movePath) {

        if (path.firstChild.name=="node") {
            path.position += event.delta;
            node = nodes[path.name];
            node.x += event.delta.x/viewProperties.zoomFactor;
            node.y += event.delta.y/viewProperties.zoomFactor;
            redrawNodeLinks(node);
        }
    }
}

function onMouseUp(event) {
    if (movePath) updateViewSize();
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
}

function onResize(event) {
    console.log("resize");
    updateViewSize();
}

