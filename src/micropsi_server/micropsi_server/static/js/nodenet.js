var viewProperties = {
    zoomFactor: 1.0,
    activeColor: new Color("#009900"),
    inhibitedColor: new Color("#ff0000"),
    selectionColor: new Color("#0099ff"),
    linkColor: new Color("#000000"),
    bgColor: new Color("#ffffff"),
    nodeColor: new Color("#c2c2d6"),
    nodeLabelColor: new Color ("#94c2f5"),
    nodeForegroundColor: new Color ("#000000"),
    nodeFontColor: new Color ("#000000"),
    fontSize: 8,
    symbolSize: 14,
    nodeWidth: 100,
    compactWidth: 40,
    cornerWidth: 5,
    padding: 5,
    slotWidth: 40,
    lineHeight: 15,
    compactNodes: true,
    compactModules: true,
    strokeWidth: 0.3,
    outlineWidth: 0.4,
    outlineWidthSelected: 3.0,
    shadowColor: new Color ("#000000"),
    shadowStrokeWidth: 3,
    shadowDisplacement: new Point(0,0.3)
};

var nodeLayer = new Layer();
var linkLayer = new Layer();
var currentNodeSpace = 0;

// data structure for net entities
function Node(uid, x, y, name, type, activation) {
	this.uid = uid;
	this.x = x;
	this.y = y;
	this.activation = activation;
	this.name = name;
	this.type = type;
	this.symbol = "?";
	this.slots=[];
	this.gates=[];
    this.parent = 0; // parent nodespace, default is root
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
            this.slots.push(new Slot("gen"));
            this.gates.push(new Gate("gen"));
            this.gates.push(new Gate("sur"));
            break;
        case "Actor":
            this.symbol = "A";
            this.slots.push(new Slot("gen"));
            this.gates.push(new Gate("gen"));
            this.gates.push(new Gate("sur"));
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
function Link(nodeUid1, gateIndex, nodeUid2, slotIndex, weight, annotation){
}

/* todo:
 - selection of node
 - deselect by clicking in background
 - multi-select of nodes with shift
 - toggle selct with ctrl
 - multi-select by dragging a frame
 - hover over nodes
 - delete node

 - links
 - link start coordinates and directions, based on gate
 - link activations
 - arrows
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

function initializeNodeNet(){
    // read zoomFactor
    var zoomFactor = viewProperties.zoomFactor;
    // determine viewport
    // fetch visible nodes and links
    var exampleNode = new Node("abcd", 100, 120, "My first node", "Native", 0.3);

    // render nodes
    var nodeView = renderNode(exampleNode, zoomFactor);
    // setSelected(nodeView);
}


initializeNodeNet();

// draw net entity
function renderNode(node, zoomFactor) {
    if (isCompact(node, zoomFactor)) renderCompactNode(node, zoomFactor);
    else renderFullNode(node, zoomFactor);
    setActivation(node);
}

// draw net entity with slots and gates
function renderFullNode(node, zoomFactor) {
    // determine width, height and bounding box
    width = viewProperties.nodeWidth;
    height = viewProperties.lineHeight*(Math.max(node.slots.length, node.gates.length)+2);
    if (node.type == "NodeSpace") height = Math.max(height, viewProperties.lineHeight*4);
    topLeft = new Point(node.x* zoomFactor-width/2, node.y*zoomFactor-height/2); // center node on origin
    topRight = new Point(topLeft.x+width, topLeft.y);
    bottomLeft = new Point(topLeft.x, topLeft.y + height);
    bottomRight = new Point (topRight.x, bottomLeft.y);
    titleBarLeft = new Point(topLeft.x, topLeft.y+viewProperties.lineHeight);
    titleBarRight = new Point(topRight.x, titleBarLeft.y);

    // create outline and title bar shape
    if (node.type == "NodeSpace") { // draw a box
        outline = new Path.Rectangle(topLeft.x, topLeft.y, width, height);
        titleBar = new Path.Rectangle(topLeft.x, topLeft.y, width, viewProperties.lineHeight);
    } else { // draw rounded corners
        outline = new Path();
        outline.add(new Point(topLeft.x, topLeft.y+viewProperties.cornerWidth));
        outline.quadraticCurveTo(topLeft, new Point(topLeft.x+viewProperties.cornerWidth, topLeft.y));
        outline.lineTo(new Point(topLeft.x + width - viewProperties.cornerWidth, topLeft.y));
        outline.quadraticCurveTo(topRight, new Point(topRight.x, topRight.y+viewProperties.cornerWidth));
        titleBar = outline.clone();
        titleBar.lineTo(titleBarRight);
        titleBar.lineTo(titleBarLeft);
        titleBar.closePath();
        outline.lineTo(new Point(bottomRight.x, bottomRight.y-viewProperties.cornerWidth));
        outline.quadraticCurveTo(bottomRight, new Point(bottomRight.x-viewProperties.cornerWidth, bottomRight.y));
        outline.lineTo(new Point(bottomLeft.x+viewProperties.cornerWidth, bottomLeft.y));
        outline.quadraticCurveTo(bottomLeft, new Point(bottomLeft.x, bottomLeft.y-viewProperties.cornerWidth));
        outline.closePath();
    }

    // define structure of the node
    nodeItem = new Group();
    nodeItem.name = "node";
    nodeContainer = new Group(nodeItem);
    nodeContainer.name = node.uid;
    // drop shadow
    shadow = outline.clone();
    shadow.position += new Point(viewProperties.shadowDisplacement.x * zoomFactor,
                                viewProperties.shadowDisplacement.y * zoomFactor);
    shadow.name = "shadow";
    shadow.strokeColor = viewProperties.shadowColor;
    shadow.strokeColor.alpha = 0.2;
    shadow.strokeWidth = viewProperties.shadowStrokeWidth * zoomFactor;
    nodeItem.addChild(shadow);
    // background, shows activation of the node
    body = outline.clone();
    body.name = "activation";
    body.fillColor = activationColor(node.activation, viewProperties.nodeColor);
    nodeItem.addChild(body);
    // title
    titleBar.name = "titleBar";
    titleBar.fillColor = viewProperties.nodeLabelColor;
    nodeItem.addChild(titleBar);
    titleBarDelimiter = new Path.Line(titleBarLeft, titleBarRight);
    titleBarDelimiter.strokeWidth = viewProperties.strokeWidth * zoomFactor;
    titleBarDelimiter.strokeColor = viewProperties.nodeForegroundColor;
    titleBarDelimiter.name = "titleBarDelimiter";
    nodeItem.addChild(titleBarDelimiter);
    // slots
    slots = new Group();
    slots.name = "slots";
    nodeItem.addChild(slots);
    // gates
    gates = new Group();
    gates.name = "gates";
    nodeItem.addChild(gates);
    // text
    labels = new Group();
    labels.name = "labels";
    nodeItem.addChild(labels);
    // outline
    outline.name = "outline";
    outline.strokeColor = viewProperties.nodeForegroundColor;
    outline.strokeWidth = viewProperties.outlineWidth * zoomFactor;
    nodeItem.addChild(outline);

    // render slots and gates
    if (node.slots.length || node.gates.length) {
        slotStart = new Point(titleBarLeft.x+viewProperties.strokeWidth * zoomFactor+viewProperties.lineHeight/2,
                              titleBarLeft.y+viewProperties.lineHeight);
        gateStart = new Point(slotStart.x+width-viewProperties.slotWidth-viewProperties.strokeWidth * zoomFactor,
                              slotStart.y);
        pillHeight = viewProperties.lineHeight - 2*viewProperties.strokeWidth * zoomFactor;
        pillWidth = viewProperties.slotWidth;
        pillTopLeft = slotStart;
        pillTopRight = new Point(pillTopLeft.x+pillWidth-viewProperties.lineHeight, pillTopLeft.y);
        pillBottomLeft = new Point(pillTopLeft.x, pillTopLeft.y+pillHeight);
        pillBottomRight = new Point(pillTopRight.x, pillBottomLeft.y);

        pill = new Path();
        pill.add(pillBottomLeft);
        pill.arcTo(pillTopLeft);
        pill.lineTo(pillTopRight);
        pill.arcTo(pillBottomRight);
        pill.closePath();
        pill.fillColor = viewProperties.nodeColor;
        pill.strokeWidth = viewProperties.strokeWidth * zoomFactor;
        pill.strokeColor = viewProperties.nodeForegroundColor;
        if (!node.slots.length) { // no slots? move our pill to the gates
            pill.position += new Point(position.x+viewProperties.nodeWidth-pillWidth
                                       -viewProperties.strokeWidth * zoomFactor, 0);
            gates.addChild(pill);
        } else {
            if (node.gates.length) { // there are slots, make a clone for the gates
                gate = pill.clone();
                gate.position += gateStart-slotStart;
                gates.addChild(gate);
            }
            slots.addChild(pill);
        }
        offset = new Point (0, viewProperties.lineHeight);
        for (i=1; i<node.slots.length; i++) {
            slot = slots.lastChild.clone();
            slot.position+=offset;
            slots.addChild(slot);
        }
        for (i=1; i<node.gates.length; i++) {
            gate = gates.lastChild.clone();
            gate.position+=offset;
            gates.addChild(gate);
        }
    }
    // render text
    fontStyle = {
        fillColor: viewProperties.nodeFontColor,
        fontSize: viewProperties.fontSize
    };
    // clipping rectangle, so text does not flow out of the node
    clipper = new Path.Rectangle (topLeft.x+viewProperties.padding, topLeft.y,
                                  width-2*viewProperties.padding, height);
    //clipper.clipMask = true;
    labels.addChild(clipper);
    labels.opacity = 0.99; // clipping workaround to bug in paper.js
    // title text
    titleText = new PointText(new Point(topLeft.x+viewProperties.padding, topLeft.y+viewProperties.lineHeight*0.8));
    titleText.style = fontStyle;
    titleText.content = node.name.length ? node.name : node.uid;
    labels.addChild(titleText);
    // type
    typeText = new PointText(new Point(topLeft.x+width/2, topLeft.y+viewProperties.lineHeight*1.8));
    typeText.style = fontStyle;
    typeText.paragraphStyle.justification = 'center';
    typeText.content = node.type;
    labels.addChild(typeText);
    // slots
    slotStart = new Point(titleBarLeft.x+viewProperties.slotWidth/2,
                          titleBarLeft.y+viewProperties.lineHeight*1.7);
    for (i in node.slots) {
        slotText = new PointText(slotStart);
        slotText.style = fontStyle;
        slotText.paragraphStyle.justification = 'center';
        slotText.content = node.slots[i].name;
        labels.addChild(slotText);
        slotStart+=offset;
    }
    gateStart = new Point(titleBarLeft.x+width-viewProperties.slotWidth/2-viewProperties.strokeWidth * zoomFactor,
                          titleBarLeft.y+viewProperties.lineHeight*1.7);
    for (i in node.gates) {
        gateText = new PointText(gateStart);
        gateText.style = fontStyle;
        gateText.paragraphStyle.justification = 'center';
        gateText.content = node.gates[i].name;
        labels.addChild(gateText);
        gateStart += offset;
    }
    nodeLayer.addChild(nodeContainer);
    nodeContainer.scale(zoomFactor);
}

// draw compact version of a net entity
function renderCompactNode(node, zoomFactor) {
    // determine width, height and bounding box
    width = viewProperties.compactWidth;
    height = viewProperties.compactWidth;
    if (node.type == "Sensor") {
        height *= .6;
        width *= 1.2;
    }
    if (node.type == "Actor") height = height*.7;
    topLeft = new Point(node.x* zoomFactor-width/2, node.y*zoomFactor-height/2); // center node on origin
    topRight = new Point(topLeft.x+width, topLeft.y);
    bottomLeft = new Point(topLeft.x, topLeft.y + height);
    bottomRight = new Point (topRight.x, bottomLeft.y);

    // create outline
    switch (node.type) {
        case "Nodespace":
            outline = new Path.Rectangle(topLeft.x, topLeft.y, width, height);
            break;
        case "Native":
            outline = new Path.RoundRectangle(new Rectangle(topLeft.x, topLeft.y, width, height),
                                              viewProperties.cornerWidth);
            break;
        case "Sensor":
            outline = new Path();
            outline.add(bottomLeft);
            outline.arcTo(bottomRight);
            outline.closePath();
            break;
        case "Actor":
            outline = new Path();
            outline.add(bottomLeft);
            outline.lineTo(new Point(topLeft.x+width *.3, topLeft.y));
            outline.lineTo(new Point(topLeft.x+width *.7, topLeft.y));
            outline.lineTo(bottomRight);
            outline.closePath();
            break;
        default: // draw circle
            outline = new Path.Circle(new Point(node.x*zoomFactor, node.y*zoomFactor), width/2);
    }

    // define structure of the node
    nodeItem = new Group();
    nodeItem.name = "node";
    nodeContainer = new Group(nodeItem);
    nodeContainer.name = node.uid;
    // drop shadow
    shadow = outline.clone();
    shadow.position += new Point(viewProperties.shadowDisplacement.x * zoomFactor,
        viewProperties.shadowDisplacement.y * zoomFactor);
    shadow.name = "shadow";
    shadow.strokeColor = viewProperties.shadowColor;
    shadow.strokeColor.alpha = 0.2;
    shadow.strokeWidth = viewProperties.shadowStrokeWidth * zoomFactor;
    nodeItem.addChild(shadow);
    // background, shows activation of the node
    body = outline.clone();
    body.name = "activation";
    body.fillColor = activationColor(node.activation, viewProperties.nodeColor);
    nodeItem.addChild(body);
    // symbol
    symbolText = new PointText(new Point(node.x*zoomFactor, node.y*zoomFactor+viewProperties.symbolSize/2));
    symbolText.fillColor = viewProperties.nodeForegroundColor;
    symbolText.content = node.symbol;
    symbolText.fontSize = viewProperties.symbolSize;
    symbolText.paragraphStyle.justification = 'center';
    nodeItem.addChild(symbolText);
    // outline
    outline.name = "outline";
    outline.strokeColor = viewProperties.nodeForegroundColor;
    outline.strokeWidth = viewProperties.outlineWidth * zoomFactor;
    nodeItem.addChild(outline);
    // label
    if (node.name.length) { // only display a label for named nodes
        labelText = new PointText(new Point(node.x*zoomFactor, node.y*zoomFactor+height/2+viewProperties.lineHeight));
        labelText.fillColor = viewProperties.nodeForegroundColor;
        labelText.content = node.name.length? node.name : node.uid;
        labelText.fontSize = viewProperties.fontSize/zoomFactor;
        labelText.paragraphStyle.justification = 'center';
        labelText.name = "labelText";
        /*
        label = new Path();
        bounds = labelText.handleBounds;
        label.add(new Point(bounds.x, bounds.y+bounds.height+viewProperties.padding));
        label.arcTo(new Point(bounds.x, bounds.y-viewProperties.padding));
        label.lineTo(new Point(bounds.x+bounds.width, bounds.y-viewProperties.padding));
        label.arcTo(new Point(bounds.x+bounds.width, bounds.y+bounds.height+viewProperties.padding));
        label.closePath();
        label.fillColor = viewProperties.nodeLabelColor;
        label.outlineColor = viewProperties.nodeForegroundColor;
        label.strokeWidth = viewProperties.strokeWidth*zoomFactor;
        label.name = "label";
        nodeItem.addChild(label);
        */
        nodeItem.addChild(labelText);
    }
    nodeLayer.addChild(nodeContainer);
    nodeContainer.scale(zoomFactor);
}

// update activation in node background, slots and gates
function setActivation(node) {
    nodeView = nodeLayer.children[node.uid];
    if (nodeView) {
        nodeItem = nodeView.children["node"];
        nodeItem.children["activation"].fillColor = activationColor(node.activation, viewProperties.nodeColor);
        if (!isCompact(node) && (node.slots.length || node.gates.length)) {
            for (i in node.slots) {
                nodeItem.children["slots"].children[i].fillColor = activationColor(node.slots[i].activation, viewProperties.nodeColor);
            }
            for (i in node.gates) {
                nodeItem.children["gates"].children[i].fillColor = activationColor(node.gates[i].activation, viewProperties.nodeColor);
            }
        }
    } else console.log ("node "+node.uid+" not found in current view");
}

// should we draw this node in compact style or full?
function isCompact(node, zoomFactor) {
    if (zoomFactor < 0.5) return true; // you cannot read this anyway
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

var values = {
    paths: 1,
    minPoints: 5,
    maxPoints: 15,
    minRadius: 30,
    maxRadius: 90
};

var hitOptions = {
    segments: false,
    stroke: true,
    fill: true,
    tolerance: 5
};

var radiusDelta = values.maxRadius - values.minRadius;
var pointsDelta = values.maxPoints - values.minPoints;
for (var i = 0; i < values.paths; i++) {
    var radius = values.minRadius + Math.random() * radiusDelta;
    var points = values.minPoints + Math.floor(Math.random() * pointsDelta);
    var path = createBlob(view.size * Point.random(), radius, points);
    var lightness = (Math.random() - 0.5) * 0.4 + 0.4;
    var hue = Math.random() * 360;
    path.style = {
        fillColor: new HslColor(hue, 1, lightness),
        strokeColor: 'black'
    };
};

function createBlob(center, maxRadius, points) {
    var path = new Path();
    path.closed = true;
    for (var i = 0; i < points; i++) {
        var delta = new Point({
            length: (maxRadius * 0.5) + (Math.random() * maxRadius * 0.5),
            angle: (360 / points) * i
        });
        path.add(center + delta);
    }
    path.smooth();
    return path;
}

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
        if (hitResult.type == 'segment') {
            segment = hitResult.segment;
        } else if (hitResult.type == 'stroke') {
            var location = hitResult.location;
            segment = path.insert(location.index + 1, event.point);
            path.smooth();
        }
    }
    movePath = hitResult.type == 'fill';
    if (movePath) {
    	path = hitResult.item;
    	while (path!=project && path.name!="node") path = path.parent;
        if (path.name=="node") project.activeLayer.addChild(path.parent);

    }
}

function onMouseMove(event) {
    var hitResult = project.hitTest(event.point, hitOptions);
    project.activeLayer.selected = false;
    if (hitResult && hitResult.item)
        hitResult.item.selected = true;
}

function onMouseDrag(event) {
    if (segment) {
        segment.point = event.point;
        path.smooth();
    }

    if (movePath)
        path.position += event.delta;
}