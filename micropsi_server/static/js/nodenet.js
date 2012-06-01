var viewProperties = {
    zoomFactor: 1,
    activeColor: new Color("#009900"),
    inhibitedColor: new Color("#ff0000"),
    selectionColor: new Color("#0099ff"),
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
    outlineWidth: 0.4,
    outlineWidthSelected: 3.0,
    shadowColor: new Color ("#000000"),
    shadowStrokeWidth: 3,
    shadowDisplacement: new Point(0,1),
    linkTension: 50,
    linkRadius: 30,
    arrowWidth: 6,
    arrowLength: 10
};

var linkLayer = new Layer();
var nodeLayer = new Layer();
var currentNodeSpace = 0;


view.viewSize = new Size(1800,1800);




function initializeNodeNet(){
    // determine viewport
    // fetch visible nodes and links
    addNode(new Node("abcd", 142, 332, 0, "My first node", "Actor", 0.3));
    addNode(new Node("sdff", 300, 100, 0, "Otto", "Concept", 0.0));
    addNode(new Node("deds", 350, 180, 0, "Carl", "Native", 0.5));
    addLink(new Link("abcd", 0, "sdff", 0, 1, 1));
    addLink(new Link("sdff", 0, "abcd", 0, 1, 1));
    addLink(new Link("sdff", 1, "deds", 0, 1, 1));

    // render nodes
    drawNodeNet(currentNodeSpace);
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

// hashes from uids to object definitions; we import these via json
nodes = {};
links = {};

// target for links, part of a net entity
function Slot(name) {
	this.name = name;
	this.incoming = [];
	this.activation = 0;
}

// source for links, part of a net entity
function Gate(name) {
	this.name = name;
	this.outgoing = [];
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
 - hover over nodes
 - delete node

 - link annotations
 - rotate annotations
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



function drawNodeNet(currentNodeSpace) {
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
}

function removeNode(node) {
    // remove the node from screen, get rid of orphan links, and from hash
}

function eraseNode(node) {
    // get rid of the screen representation of a node
    nodeLayer.removeChild[node.uid];
}

function setNodePosition(node) {
    // like activation change, only put the node elsewhere and redraw the links
    nodeLayer.children[node.uid].remove();
    renderNode(node);
    redrawNodeLinks();
}

function redrawNodeLinks(node) {
    // redraw only the links that are connected to the given node
    for (gate in node.gates) {
        for (link in node.gates[gate].outgoing) {
            linkLayer.children[node.gates[gate].outgoing[link].uid].remove();
            renderLink(node.gates[gate].outgoing[link]);
        }
    }
    for (slot in node.slots) {
        for (link in node.slots[slot].incoming) {
            linkLayer.children[node.slots[slot].incoming[link].uid].remove();
            renderLink(node.slots[slot].incoming[link]);
        }
    }
}

// add or update link

function addLink(link) {
    //check if link already exists
    if (!(link.uid in links)) {
        // add link to source node and target node
        if (nodes[link.sourceNodeUid] && nodes[link.targetNodeUid]) {
            nodes[link.sourceNodeUid].gates[link.gateIndex].outgoing.push(link);
            nodes[link.targetNodeUid].slots[link.slotIndex].incoming.push(link);
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
            linkLayer.removeChild(link.uid);
            renderLink(link);
        }
    }
}

function removeLink(link) {
    // delete a link from the array, and from the screen
}

function eraseLink(link) {
    // erase link from screen
    linkLayer.removeChild[link.uid]
}

initializeNodeNet();

// draw link

function renderLink(link) {
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

    arrowEntry = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(endAngle)+endPoint;
    nodeExit = new Point(viewProperties.arrowLength*viewProperties.zoomFactor,0).rotate(startAngle)+startPoint;


    linkPath = new Path([[startPoint],[nodeExit,new Point(0,0),startDirection],[arrowEntry,endDirection]]);
    linkPath.strokeColor = linkColor;
    linkPath.strokeWidth = viewProperties.zoomFactor * linkWeight;
    if (gate.name=="cat" || gate.name == "exp") linkPath.dashArray = [4*viewProperties.zoomFactor,3*viewProperties.zoomFactor];


    linkItem = new Group([linkPath, arrowPath]);
    linkItem.name = "link";
    linkContainer = new Group(linkItem);
    linkContainer.name = link.uid;

    //linkContainer.scale(viewProperties.zoomFactor,endPoint);
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
    body = createNodeBody(node, shape);
    titleBar = createNodeTitleBar(node, bounds);
    titleBarDelimiter = createNodeTitleBarDelimiter(bounds);
    slots = createNodeSlots(node, bounds);
    gates = createNodeGates(node, bounds);
    labels = createFullNodeLabels(node, bounds);
    outline = createNodeOutline(shape);

    // define structure of the node
    nodeItem = new Group([shadow, body, titleBar, titleBarDelimiter]);
    if (slots) nodeItem.addChild(slots);
    if (gates) nodeItem.addChild(gates);
    nodeItem.addChild(labels);
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
    body = createNodeBody(node, shape);
    shadow = createNodeShadow(shape);
    symbol = createCompactNodeSymbol(node, bounds);
    label = createCompactNodeLabel(node, bounds);
    outline = createNodeOutline(shape);

    // define structure of the node
    nodeItem = new Group([shadow, body, symbol, outline]);
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
    titleBar.name = "titleBar";
    titleBar.fillColor = viewProperties.nodeLabelColor;
    return titleBar;
}

// draw a line below the title bar
function createNodeTitleBarDelimiter (bounds) {
    titleBarDelimiter = new Path.Line(bounds.x, bounds.y + viewProperties.lineHeight,
        bounds.right, bounds.y + viewProperties.lineHeight);
    titleBarDelimiter.strokeWidth = viewProperties.strokeWidth * viewProperties.zoomFactor;
    titleBarDelimiter.strokeColor = viewProperties.nodeForegroundColor;
    titleBarDelimiter.name = "titleBarDelimiter";
    return titleBarDelimiter;
}

// draw shadow of a node
function createNodeShadow(outline) {
    shadow = outline.clone();
    shadow.position += viewProperties.shadowDisplacement;
    shadow.name = "shadow";
    shadow.strokeColor = viewProperties.shadowColor;
    shadow.strokeColor.alpha = 0.2;
    shadow.strokeWidth = viewProperties.shadowStrokeWidth * viewProperties.zoomFactor;
    shadow.fillColor = viewProperties.shadowColor;

    shadow.shadowColor = viewProperties.shadowColor;
    shadow.shadowBlur = 10;
    return shadow;
}

// draw background, with activation of the node
function createNodeBody(node, outline) {
    body = outline.clone();
    body.name = "activation";
    body.fillColor = activationColor(node.activation, viewProperties.nodeColor);
    return body;
}

// draw slots of a node
function createNodeSlots(node, bounds) {
    if (node.slots.length) {
        slotStart = new Point(bounds.x+viewProperties.strokeWidth+viewProperties.lineHeight/2,
            bounds.y+2*viewProperties.lineHeight);
        slots = new Group(createNodeGateElement(slotStart));
        slots.name = "slots";
        offset = new Point (0, viewProperties.lineHeight);
        for (i=1; i<node.slots.length; i++) {
            slot = slots.lastChild.clone();
            slot.position+=offset;
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
        gates = new Group(createNodeGateElement(gateStart));
        gates.name = "gates";
        offset = new Point (0, viewProperties.lineHeight);
        for (i=1; i<node.gates.length; i++) {
            gate = gates.lastChild.clone();
            gate.position+=offset;
            gates.addChild(gate);
        }
        return gates;
    }
    else return null;
}

// draw the shape of an individual gate or slot
function createNodeGateElement(startPoint) {
    pillBounds = new Rectangle(startPoint.x, startPoint.y, viewProperties.slotWidth - viewProperties.lineHeight,
        viewProperties.lineHeight - 2*viewProperties.strokeWidth);
    pill = new Path();
    pill.add(pillBounds.bottomLeft);
    pill.arcTo(pillBounds.topLeft);
    pill.lineTo(pillBounds.topRight);
    pill.arcTo(pillBounds.bottomRight);
    pill.closePath();
    pill.fillColor = viewProperties.nodeColor;
    pill.strokeWidth = viewProperties.strokeWidth * viewProperties.zoomFactor;
    pill.strokeColor = viewProperties.nodeForegroundColor;
    return pill;
}

// draw all the text of a full node
function createFullNodeLabels(node, bounds) {
    labels = new Group();
    labels.name = "labels";

    fontStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize
    };
    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle (bounds.x+viewProperties.padding, bounds.y,
        bounds.width-2*viewProperties.padding, bounds.height);
    clipper.clipMask = true;
    labels.addChild(clipper);
    labels.opacity = 0.99; // clipping workaround to bug in paper.js

    // title text
    titleText = new PointText(new Point(bounds.x+viewProperties.padding, bounds.y+viewProperties.lineHeight*0.8));
    titleText.characterStyle = fontStyle;
    titleText.content = node.name.length ? node.name : node.uid;
    labels.addChild(titleText);

    // type
    typeText = new PointText(new Point(bounds.x+bounds.width/2, bounds.y+viewProperties.lineHeight*1.8));
    typeText.characterStyle = fontStyle;
    typeText.paragraphStyle.justification = 'center';
    typeText.content = node.type;
    labels.addChild(typeText);

    // slots and gates
    slotStart = new Point(bounds.x+viewProperties.slotWidth/2,
        bounds.y+viewProperties.lineHeight*2.7);
    for (i in node.slots) {
        slotText = new PointText(slotStart);
        slotText.characterStyle = fontStyle;
        slotText.paragraphStyle.justification = 'center';
        slotText.content = node.slots[i].name;
        labels.addChild(slotText);
        slotStart+=offset;
    }
    gateStart = new Point(bounds.x+width-viewProperties.slotWidth/2-viewProperties.strokeWidth,
        bounds.y+viewProperties.lineHeight*2.7);
    for (i in node.gates) {
        gateText = new PointText(gateStart);
        gateText.characterStyle = fontStyle;
        gateText.paragraphStyle.justification = 'center';
        gateText.content = node.gates[i].name;
        labels.addChild(gateText);
        gateStart += offset;
    }
    return labels;
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

// draw the symbol of a compact node
function createCompactNodeSymbol(node, bounds) {
    symbolText = new PointText(new Point(bounds.x+bounds.width/2,
        bounds.y+bounds.height/2+viewProperties.symbolSize/2));
    symbolText.fillColor = viewProperties.nodeForegroundColor;
    symbolText.content = node.symbol;
    symbolText.fontSize = viewProperties.symbolSize;
    symbolText.paragraphStyle.justification = 'center';
    return symbolText;
}

// draw outline of a node
function createNodeOutline(shape) {
    shape.name = "outline";
    shape.strokeColor = viewProperties.nodeForegroundColor;
    shape.strokeWidth = viewProperties.outlineWidth * viewProperties.zoomFactor;
    return shape;
}

// update activation in node background, slots and gates
function setActivation(node) {
    if (node.parent!=currentNodeSpace) return; // only do this is the node is visible

    nodeView = nodeLayer.children[node.uid];
    if (nodeView) {
        nodeItem = nodeView.children["node"];
        nodeItem.children["activation"].fillColor = activationColor(node.activation, viewProperties.nodeColor);
        if (!isCompact(node) && (node.slots.length || node.gates.length)) {
            for (i in node.slots) {
                nodeItem.children["slots"].children[i].fillColor = activationColor(node.slots[i].activation,
                    viewProperties.nodeColor);
            }
            for (i in node.gates) {
                nodeItem.children["gates"].children[i].fillColor = activationColor(node.gates[i].activation,
                    viewProperties.nodeColor);
            }
        }
    } else console.log ("node "+node.uid+" not found in current view");
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

var segment, path;
var movePath = false;
function onMouseDown(event) {
    segment = path = null;
    var hitResult = project.hitTest(event.point, hitOptions);

    if (event.modifiers.shift) {
        if (hitResult.type == 'segment') {
            hitResult.segment.remove();
        };
        return;
    }

    if (hitResult) {
        path = hitResult.item;
        if (hitResult.type == 'stroke') {
            while (path!=project && path.name!="link") path = path.parent;
            if (path.name=="link") {
                path = path.parent;
                console.log ("clicked link "+path.name)
            }
        }
    }
    movePath = hitResult.type == 'fill';
    if (movePath) {
    	path = hitResult.item;
    	while (path!=project && path.name!="node") path = path.parent;
        if (path.name=="node") {
            path = path.parent;
            project.activeLayer.addChild(path);
        }

    }
}

function onMouseMove(event) {
    var hitResult = project.hitTest(event.point, hitOptions);
    project.activeLayer.selected = false;
    if (hitResult && hitResult.item) {
        path = hitResult.item;
        while(path!=project && !/^node|link|gate|slot/.test(path.name) && path.parent) path = path.parent;
        if (path.name == "link") {
            // test = path.clone();
            // test.childen[0].strokeColor=viewProperties.selectionColor;
        }
    }
}

function onMouseDrag(event) {
    if (movePath) {
        path.position += event.delta;

        if (path.firstChild.name=="node") {
            node = nodes[path.name];
            node.x += event.delta.x/viewProperties.zoomFactor;
            node.y += event.delta.y/viewProperties.zoomFactor;
            redrawNodeLinks(node);
        }
    }
}

function onKeyDown(event) {
    // support zooming via view.zoom using characters + and -
    if (event.character == "+") {
        viewProperties.zoomFactor += .1;
        drawNodeNet(currentNodeSpace);
    }
    else if (event.character == "-") {
        if (viewProperties.zoomFactor > .2) viewProperties.zoomFactor -= .1;
        drawNodeNet(currentNodeSpace);
    }
}
