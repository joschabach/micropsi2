/*
 * viewer for the world.
 */

var canvas = $('#world');

var viewProperties = {
    frameWidth: 1445,
    zoomFactor: 1,
    objectWidth: 8,
    lineHeight: 15,
    objectLabelColor: new Color ("#94c2f5"),
    objectForegroundColor: new Color ("#000000"),
    fontSize: 10,
    symbolSize: 14,
    highlightColor: new Color ("#ffffff"),
    gateShadowColor: new Color("#888888"),
    shadowColor: new Color ("#000000"),
    shadowStrokeWidth: 0,
    shadowDisplacement: new Point(0.5,1.5),
    innerShadowDisplacement: new Point(0.2,0.7),
    typeColors: {
        S: new Color('#009900'),
        U: new Color('#000099'),
        Tram: new Color('#990000'),
        Bus: new Color('#7000ff'),
        other: new Color('#304451')
    }
}

objects = {};

objectLayer = new Layer();
objectLayer.name = 'ObjectLayer';

objPrerenderLayer = new Layer();
objPrerenderLayer.name = 'PrerenderLayer';
objPrerenderLayer.visible = false;

var selectionRectangle = new Rectangle(10,20,30,40);
var selectionBox = new Path.Rectangle(selectionRectangle);
selectionBox.strokeWidth = 0.5;
selectionBox.strokeColor = 'black';
selectionBox.dashArray = [4,2];
objectLayer.addChild(selectionBox);


currentWorld = false;
if(!currentWorld){
    currentWorld = $.cookie('current_world');
}

if(currentWorld){
    // todo: get url from api.
    canvas.css('background', 'url("/static/img/berlin/berlin_transit.png") no-repeat top left');
    load_world_info();
}

function load_world_info(){
    api('get_world_objects', {world_uid: currentWorld}, function(data){
        for(var key in data){
            addObject(new WorldObject(data[key].uid, data[key].pos[0], data[key].pos[1], data[key].name, data[key].stationtype));
        }
        //updateViewSize();
    });
}

function updateViewSize() {
    var maxX = 0;
    var maxY = 0;
    var frameWidth = viewProperties.frameWidth*viewProperties.zoomFactor;
    var el = view.element.parentElement;
    prerenderLayer.removeChildren();
    for (var obj in objectLayer.children) {
        if (obj in objects) {
            var obj = objects[obj];
            // make sure no node gets lost to the top or left
            if (obj.x < frameWidth || obj.y < frameWidth) {
                obj.x = Math.max(obj.x, viewProperties.frameWidth);
                obj.y = Math.max(obj.y, viewProperties.frameWidth);
                redrawObject(obj);
            }
            maxX = Math.max(maxX, obj.x);
            maxY = Math.max(maxY, obj.y);
        }
    }
    view.viewSize = new Size(Math.max((maxX+viewProperties.frameWidth)*viewProperties.zoomFactor,
        el.clientWidth),
        Math.max((maxY+viewProperties.frameWidth)* viewProperties.zoomFactor,
            el.clientHeight));
    view.draw(true);
}


function WorldObject(uid, x, y, name, type){
    this.uid = uid;
    this.x = x;
    this.y = y;
    this.name = name;
    this.type = type;
    this.bounds = null
}

function addObject(worldobject){
    if(! (worldobject.uid in objects)) {
        console.log('adding obejct: ' + worldobject.name);
        renderObject(worldobject);
        objects[worldobject.uid] = worldobject;
    }
    return worldobject;
}

function redrawObject(obj){
    objectLayer.children[obj.uid].remove();
    renderObject(obj);
}

function renderObject(worldobject){
    worldobject.bounds = calculateObjectBounds(worldobject);
    var skeleton = createObjectSkeleton(worldobject);
    //var label = createObjectLabel(worldobject);
    //console.log(label);
    //var objectItem = new Group([skeleton, label]);
    //objectItem.name = worldobject.uid;
    //console.log(objectItem);
    objectLayer.addChild(skeleton);
}

function calculateObjectBounds(worldobject){
    var width, height;
    width = height = viewProperties.objectWidth * viewProperties.zoomFactor;
    if (worldobject.type == "Tram"){
        width = height = 5
    } else if (worldobject.type == 'other'  || worldobject.type == "Bus"){
        width = height = 3
    }
    return new Rectangle(worldobject.x*viewProperties.zoomFactor - width/2,
        worldobject.y*viewProperties.zoomFactor - height/2, // center worldobject on origin
        width, height);
}

function createObjectSkeleton(worldobject){
    var bounds = worldobject.bounds;
    var shape = new Path.Circle(new Point(bounds.x + bounds.width/2, bounds.y+bounds.height/2), bounds.width/2);
    if(worldobject.type == "S" || worldobject.type == "S+U"){
        shape.fillColor = viewProperties.typeColors.S;
    } else {
        shape.fillColor = viewProperties.typeColors[worldobject.type];
    }
    //var border = createBorder(shape, viewProperties.shadowDisplacement*viewProperties.zoomFactor);
    //var typeLabel = createCompactObjectBodyLabel(worldobject);
    //var skeleton = new Group([border, typeLabel]);
    return shape;
}

// draw the label of a compact worldobject
function createObjectLabel(worldobject) {
    var labelText = new PointText(new Point(worldobject.bounds.x + worldobject.bounds.width/2,
            worldobject.bounds.bottom+viewProperties.lineHeight));
    labelText.content = worldobject.name ? worldobject.name : worldobject.uid;
    labelText.characterStyle = {
        fontSize: viewProperties.fontSize,
        fillColor: viewProperties.objForegroundColor
    };
    labelText.paragraphStyle.justification = 'center';
    labelText.name = "labelText";
    return labelText;
}

// render the symbol within the compact worldobject body
function createCompactObjectBodyLabel(worldobject) {
    var bounds = worldobject.bounds;
    var symbolText = new PointText(new Point(bounds.x+bounds.width/2,
        bounds.y+bounds.height/2+viewProperties.symbolSize/2*viewProperties.zoomFactor));
    symbolText.fillColor = viewProperties.objectForegroundColor;
    symbolText.content = worldobject.type;
    symbolText.fontSize = viewProperties.symbolSize*viewProperties.zoomFactor;
    symbolText.paragraphStyle.justification = 'center';
    return symbolText;
}

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

function api(functionname, params, success, error, method){
    var url = '/rpc/'+functionname;
    if(method != "post"){
        args = '';
        for(var key in params){
            args += key+'='+encodeURIComponent(JSON.stringify(params[key]))+',';
        }
        url += '('+args.substr(0, args.length-1) + ')';
    }
    $.ajax({
        url: url,
        data: ((method == "post") ? params : null),
        type: method || "get",
        success: function(data){
            if(data.Error){
                if(error) error(data);
                else defaultErrorCallback(data);
            } else{
                if(success) success(data);
                else defaultSuccessCallback(data);
            }
        },
        error: error || defaultErrorCallback
    });
}
function defaultSuccessCallback(data){
    dialogs.notification("Changes saved", 'success');
}
function defaultErrorCallback(data){
    dialogs.notification("Error: " + data.Error || "serverside exception", 'error');
}
function EmptyCallback(){}
