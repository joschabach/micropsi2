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
    flowConnectionColor: new Color("#1F3755"),
    nodeColor: new Color("#c2c2d6"),
    nodeForegroundColor: new Color ("#000000"),
    nodeFontColor: new Color ("#000000"),
    fontSize: 10,
    symbolSize: 14,
    nodeWidth: 84,
    compactNodeWidth: 32,
    flowModuleWidth: 160,
    cornerWidth: 6,
    padding: 5,
    slotWidth: 34,
    lineHeight: 15,
    compactNodes: false,
    outsideDummyDistance: 30,
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
    snap_to_grid: false,
    load_link_threshold: 1000
};

var nodenetscope = paper;

var nodenet_loaded = false;

// hashes from uids to object definitions; we import these via json
nodes = {};
links = {};
flow_connections = {};
selection = {};
monitors = {};

available_gatefunctions = {}
gatefunction_icons = {
    'sigmoid': 'Σ',
    'elu': 'E',
    'relu': 'R',
    'absolute': '|x|',
    'one_over_x': '1/x',
    'identity': '',
    'threshold': 'T'
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

var nodenetcookie = $.cookie('selected_nodenet') || '';
if (nodenetcookie && nodenetcookie.indexOf('/') > 0){
    nodenetcookie = nodenetcookie.replace('"', '').split("/");
    currentNodenet = nodenetcookie[0];
    currentNodeSpace = nodenetcookie[1] || null;
} else {
    currentNodenet = '';
    currentNodeSpace = '';
}

nodespaceProperties = {};

// compatibility
nodespace_property_defaults = {
    'renderlinks': ($.cookie('renderlinks') || 'always'),
    'activation_display': 'redgreen'
}


currentWorldadapter = null;

var selectionRectangle = new Rectangle(1,1,1,1);
selectionBox = new Path.Rectangle(selectionRectangle);
selectionBox.strokeWidth = 0.5;
selectionBox.strokeColor = 'black';
selectionBox.dashArray = [4,2];
selectionBox.name = "selectionBox";

nodetypes = {};
native_modules = {};
flow_modules = {};
native_module_categories = {};
flow_module_categories = {};
available_gatetypes = [];
nodespaces = {};
sorted_nodetypes = [];
sorted_native_modules = [];
sorted_flow_modules = [];
nodenet_data = null;

initializeMenus();
initializeDialogs();
initializeControls();
initializeSidebarForms();

canvas_container = $('#nodenet').parent();

var clipboard = {};

// hm. not really nice. but let's see if we got other pairs, or need them configurable:
var inverse_link_map = {'por':'ret', 'sub':'sur', 'cat':'exp'};
var inverse_link_targets = ['ret', 'sur', 'exp'];

if(currentNodenet){
    setCurrentNodenet(currentNodenet, currentNodeSpace);
} else {
    splash = new PointText(new Point(50, 50));
    splash.characterStyle = { fontSize: 20, fillColor: "#66666" };
    splash.content = 'Create an agent by selecting "New..." from the "Agent" menu.';
    nodeLayer.addChild(splash);
    toggleButtons(false);
}

worldadapters = {};
currentSimulationStep = 0;
nodenetRunning = false;

get_available_worlds();

registerResizeHandler();

globalDataSources = [];
globalDataTargets = [];

available_operations = {};

$(document).on('nodenet_changed', function(event, new_nodenet){
    setCurrentNodenet(new_nodenet, null, true);
});
$(document).on('new_world_created', function(data){
    get_available_worlds();
});

function toggleButtons(on){
    if(on)
        $('[data-nodenet-control]').removeAttr('disabled');
    else
        $('[data-nodenet-control]').attr('disabled', 'disabled');
}

function get_available_worlds(){
    api.call('get_available_worlds', {}, success=function(data){
        var html = '<option value="">None</option>';
        worlds = [];
        for(var uid in data){
            worlds.push([uid, data[uid].name]);
        }
        worlds.sort(function(a, b){return a[1] - b[1]});
        for(var i in worlds){
            html += '<option value="'+worlds[i][0]+'">'+worlds[i][1]+'</option>';
        }
        $('#nodenet_world_uid').html(html);
        if(currentNodenet && nodenet_data){
            $('#nodenet_world_uid').val(nodenet_data.world);
        }
    });
}

function get_available_worldadapters(world_uid, callback){
    worldadapters = {};
    if(world_uid){
        api.call("get_worldadapters", {world_uid: world_uid, nodenet_uid: currentNodenet},
            success=function(data){
                worldadapters = data;
                var str = '';
                var name;
                var keys = Object.keys(worldadapters);
                keys.sort();
                for (var idx in keys){
                    name = keys[idx];
                    str += '<option title="'+worldadapters[name]['description']+'">'+name+'</option>';
                }
                $('#nodenet_worldadapter').html(str).removeAttr('disabled');
                if(callback){
                    callback(data);
                }
        });
    } else {
        $('#nodenet_worldadapter').html('<option>&lt;No world selected&gt;</option>').attr('disabled', 'disabled');
        if(callback){
            callback({});
        }
    }
}

function get_available_gatefunctions(){
    api.call('get_available_gatefunctions', {nodenet_uid: currentNodenet}, function(data){
        html = '';
        available_gatefunctions = data;
        for(var key in available_gatefunctions){
            html += '<option>'+key+'</option>';
        }
        $('#gate_gatefunction').html(html);
    });
}

function setNodenetValues(data){
    $('#nodenet_world_uid').val(data.world);
    $('#nodenet_uid').val(currentNodenet);
    $('#nodenet_nodenet_name').val(data.name);
    $('#ui_snap').attr('checked', data.snap_to_grid);
    if (!jQuery.isEmptyObject(worldadapters)) {
        var worldadapter_select = $('#nodenet_worldadapter');
        worldadapter_select.val(data.worldadapter);
        worldadapter_select.trigger("change");
        if(worldadapter_select.val() != data.worldadapter){
            dialogs.notification("The worldadapter of this nodenet is not compatible to the world. Please choose a worldadapter from the list", 'Error');
        }
    }
}

function buildCategoryTree(item, path, idx){
    if (idx < path.length){
        var name = path[idx];
        if (!item[name]){
            item[name] = {};
        }
        buildCategoryTree(item[name], path, idx + 1);
    }
}


api.call("get_available_operations", {}, function(data){
    available_operations = data
});


function setCurrentNodenet(uid, nodespace, changed){
    if(!nodespace){
        nodespace = null;
    }
    $('#loading').show();
    api.call('get_nodenet_metadata', {nodenet_uid: uid},
        function(data){
            $('#loading').hide();
            nodenetscope.activate();
            toggleButtons(true);

            var nodenetChanged = changed || (uid != currentNodenet);
            currentNodenet = uid;
            currentNodeSpace = data.rootnodespace;
            currentWorldadapter = data.worldadapter;
            nodespaceProperties = data.nodespace_ui_properties || {};
            for(var key in data.nodespaces){
                if(!(key in nodespaceProperties)){
                    nodespaceProperties[key] = {};
                }
                if(!nodespaceProperties[key].renderlinks){
                    nodespaceProperties[key].renderlinks = nodespace_property_defaults.renderlinks;
                }
                if(!nodespaceProperties[key].activation_display){
                    nodespaceProperties[key].activation_display = nodespace_property_defaults.activation_display;
                }
            }
            if(nodenetChanged){
                clipboard = {};
                selection = {};
                nodespaces = {};
                nodes = {};
                links = {};
                nodeLayer.removeChildren();
                linkLayer.removeChildren();
            }
            $(document).trigger('nodenet_loaded', uid);
            $('.nodenet_step').text(data.current_step || 0);
            $('.world_step').text(data.current_world_step || 0);

            nodenet_data = data;
            nodenet_data['snap_to_grid'] = $.cookie('snap_to_grid') || viewProperties.snap_to_grid;

            showDefaultForm();

            $.cookie('selected_nodenet', currentNodenet+"/", { expires: 7, path: '/' });
            if(nodenetChanged || jQuery.isEmptyObject(nodetypes)){
                var sortfunc = function(a, b){
                    if(a < b) return -1;
                    if(a > b) return 1;
                    return 0;
                };
                nodetypes = data.nodetypes;
                sorted_nodetypes = Object.keys(nodetypes);
                sorted_nodetypes.sort(sortfunc);

                native_modules = data.native_modules;
                sorted_native_modules = Object.keys(native_modules);
                sorted_native_modules.sort(sortfunc);

                flow_modules = data.flow_modules;
                sorted_flow_modules = Object.keys(flow_modules);
                sorted_flow_modules.sort(sortfunc);

                categories = [];
                for(var key in native_modules){
                    nodetypes[key] = native_modules[key];
                    categories.push(native_modules[key].category.split('/'));
                }
                native_module_categories = {}
                for(var i =0; i < categories.length; i++){
                    buildCategoryTree(native_module_categories, categories[i], 0);
                }
                flow_categories = [];
                for(var key in flow_modules){
                    nodetypes[key] = flow_modules[key];
                    flow_categories.push(flow_modules[key].category.split('/'));
                }
                flow_module_categories = {}
                for(var i =0; i < flow_categories.length; i++){
                    buildCategoryTree(flow_module_categories, flow_categories[i], 0);
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
                get_available_gatefunctions();
                getNodespaceList();
                $(document).trigger('refreshNodenetList');
            }
            nodenet_loaded = true;
            refreshNodespace(nodespace)
        },
        function(data) {
            api.defaultErrorCallback(data);
            $('#loading').hide();
            $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
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
            for(var key in sorted[i].properties){
                nodespaceProperties[sorted[i].uid][key] = sorted[i].properties[key];
            }
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

        nodenetRunning = data.is_active;

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

        // we're rendering nodes first, and these might include links from an old nodespace
        // re-rendering the node might want to re-render the links, which fails if the targetnodes
        // are not yet there... thus, just remove all links for the moment.
        for(uid in links){
            removeLink(links[uid]);
        }
        var links_data = {}
        var flow_connections = {};
        for(uid in data.nodes){
            var node = data.nodes[uid]
            item = new Node(uid, node['position'][0], node['position'][1], node.parent_nodespace, node.name, node.type, node.activation, node.state, node.parameters, node.gate_activations, node.gate_configuration, node.is_highdimensional, node.inlinks, node.outlinks, node.inputmap);
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
            for(gate in node.links){
                for(var i = 0; i < node.links[gate].length; i++){
                    luid = uid + ":" + gate + ":" + node.links[gate][i]['target_slot_name'] + ":" + node.links[gate][i]['target_node_uid']
                    links_data[luid] = node.links[gate][i]
                    links_data[luid].source_node_uid = uid
                    links_data[luid].source_gate_name = gate
                }
            }
            if(node.inputmap){
                for(var name in node.inputmap){
                    var source_uid = node.inputmap[name][0];
                    var source_name = node.inputmap[name][1];
                    if(source_uid && source_name){
                        cid = source_uid + ":" + source_name + ":" + name + ":" + uid;
                        links_data[cid] = {
                            'source_node_uid': source_uid,
                            'target_node_uid': uid,
                            'source_name': source_name,
                            'target_name': name,
                            'is_flow_connection': true
                        };
                    }
                }
            }
        }

        if(nodespaceProperties[currentNodeSpace].renderlinks != 'none'){
            loadLinksForSelection(function(data){
                for(var uid in links) {
                    if(!(uid in data)) {
                        removeLink(links[uid]);
                    }
                }
                addLinks(data.links);
            }, false, true);

            for(var uid in links) {
                if(!(uid in links_data)) {
                    removeLink(links[uid]);
                }
            }
            for(var uid in flow_connections) {
                if(!(uid in links_data)) {
                    removeLink(flow_connections[uid]);
                }
            }
            addLinks(links_data);
        }

        updateModulators(data.modulators);

        if(data.monitors){
            monitors = data.monitors;
        }
        if(changed){
            updateNodespaceForm();
        }
    }
    updateViewSize();
    drawGridLines(view.element);
}

function setNodespaceDiffData(data, changed){
    nodenetscope.activate();
    if (data && !jQuery.isEmptyObject(data)){
        if(!('selectionBox' in nodeLayer)){
            nodeLayer.addChild(selectionBox);
        }
        var uid;

        // structure first:
        if(data.changes){
            for(var i=0; i < data.changes.nodes_deleted.length; i++){
                uid = data.changes.nodes_deleted[i];
                if (uid in selection) delete selection[uid];
                if(uid in nodes) removeNode(nodes[uid]);
            }
            for(var i=0; i < data.changes.nodespaces_deleted.length; i++){
                uid = data.changes.nodespaces_deleted[i];
                if (uid in selection) delete selection[uid];
                if (uid in nodes) removeNode(nodes[uid]);
                delete nodespaces[uid]
            }
            links_data = {}
            for(var uid in data.changes.nodes_dirty){
                var nodedata = data.changes.nodes_dirty[uid];
                item = new Node(uid, nodedata['position'][0], nodedata['position'][1], nodedata.parent_nodespace, nodedata.name, nodedata.type, nodedata.activation, nodedata.state, nodedata.parameters, nodedata.gate_activations, nodedata.gate_configuration, nodedata.is_highdimensional, nodedata.inlinks, nodedata.outlinks);
                if(uid in nodes){
                    for (var gateName in nodes[uid].gates) {
                        for (linkUid in nodes[uid].gates[gateName].outgoing) {
                            if(linkUid in linkLayer.children) {
                                removeLink(links[linkUid]);
                            }
                        }
                    }
                    redrawNode(item);
                    nodes[uid].update(item);
                } else{
                    addNode(item);
                }
                for(gate in nodedata.links){
                    for(var i = 0; i < nodedata.links[gate].length; i++){
                        luid = uid + ":" + gate + ":" + nodedata.links[gate][i]['target_slot_name'] + ":" + nodedata.links[gate][i]['target_node_uid']
                        links_data[luid] = nodedata.links[gate][i]
                        links_data[luid].source_node_uid = uid
                        links_data[luid].source_gate_name = gate
                    }
                }
                if(nodedata.inputmap){
                    for(var name in nodedata.inputmap){
                        var source_uid = nodedata.inputmap[name][0];
                        var source_name = nodedata.inputmap[name][1];
                        if (source_uid && source_name){
                            cid = source_uid + ":" + source_name + ":" + name + ":" + uid;
                            links_data[cid] = {
                                'source_node_uid': source_uid,
                                'target_node_uid': uid,
                                'source_name': source_name,
                                'target_name': name,
                                'is_flow_connection': true
                            };
                        }
                    }
                }
            }
            addLinks(links_data);
        }
        // activations:
        for(var uid in nodes){
            activations = false
            if(uid in data.activations){
                activations = data.activations[uid];
            }
            var gen = 0
            for(var i=0; i < nodes[uid].gateIndexes.length; i++){
                var type = nodes[uid].gateIndexes[i];
                var gateAct = (activations) ? activations[i] : 0;
                nodes[uid].gates[type].activation = gateAct;
                if(type == 'gen'){
                    gen = gateAct;
                }
            }
            nodes[uid].activation = gen;
            setActivation(nodes[uid]);
            redrawNodeLinks(nodes[uid]);
        }

        updateModulators(data.modulators);

        if(data.monitors){
            monitors = data.monitors;
        }
        if(changed){
            updateNodespaceForm();
        }
    }
    updateViewSize();
    drawGridLines(view.element);
}

function addLinks(link_data){
    var link, sourceId, targetId;
    var outsideLinks = [];

    for(uid in link_data){
        sourceId = link_data[uid]['source_node_uid'];
        targetId = link_data[uid]['target_node_uid'];
        if (sourceId in nodes && targetId in nodes && nodes[sourceId].parent == nodes[targetId].parent){
            if(link_data[uid].is_flow_connection){
                link = new Link(uid, sourceId, link_data[uid].source_name, targetId, link_data[uid].target_name, 1, true);
            } else {
                link = new Link(uid, sourceId, link_data[uid].source_gate_name, targetId, link_data[uid].target_slot_name, link_data[uid].weight);
            }
            if(uid in links){
                redrawLink(link);
            } else if(uid in flow_connections){
                redrawFlowConnection(link);
            } else {
                addLink(link);
            }
        } else if(sourceId in nodes || targetId in nodes){
            link = new Link(uid, sourceId, link_data[uid].source_gate_name, targetId, link_data[uid].target_slot_name, link_data[uid].weight);
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
}


function get_nodenet_params(){
    return {
        'nodespaces': [currentNodeSpace],
        'step': currentSimulationStep - 1,
        'include_links': nodespaceProperties[currentNodeSpace].renderlinks == 'always',
    }
}
function get_nodenet_diff_params(){
    return {
        'nodespaces': [currentNodeSpace],
        'step': window.currentSimulationStep,
        'include_links': nodespaceProperties[currentNodeSpace].renderlinks == 'always'
    }
}


if($('#nodenet_editor').height() > 0){
    register_stepping_function('nodenet_diff', get_nodenet_diff_params, setNodespaceDiffData);
}
$('#nodenet_editor').on('shown', function(){
    register_stepping_function('nodenet_diff', get_nodenet_diff_params, setNodespaceDiffData);
    if(!calculationRunning){
        $(document).trigger('runner_stepped');
    }
});
$('#nodenet_editor').on('hidden', function(){
    unregister_stepping_function('nodenet_diff');
});

function refreshNodespace(nodespace, step, callback){
    if(!nodespace) nodespace = currentNodeSpace;
    if(!currentNodenet || !nodespace){
        return;
    }
    nodespace = nodespace || currentNodeSpace;
    params = {
        nodenet_uid: currentNodenet,
        nodespaces: [nodespace],
        include_links: true
    };
    if(nodespaceProperties[nodespace] && nodespaceProperties[nodespace].renderlinks != 'always'){
        params.include_links = false;
    }
    api.call('get_nodes', params , success=function(data){
        var changed = nodespace != currentNodeSpace;
        if(changed){
            currentNodeSpace = nodespace;
            $.cookie('selected_nodenet', currentNodenet+"/"+currentNodeSpace, { expires: 7, path: '/' });
            if(!$.isEmptyObject(nodespaces)){
                $("#current_nodespace_name").text(nodespaces[nodespace].name);
            }
            nodeLayer.removeChildren();
            linkLayer.removeChildren();
        }
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

function updateModulators(data){
    var table = $('table.modulators');
    html = '';
    var sorted = [];
    globalDataSources = [];
    globalDataTargets = [];
    if($.isEmptyObject(data)){
        return $('.modulators_container').hide();
    }
    $('.modulators_container').show();
    for(key in data){
        sorted.push({'name': key, 'value': data[key]});
    }
    sorted.sort(sortByName);
    var emo_html = '';
    var base_html = ''
    // display reversed to get emo_ before base_
    for(var i = 0; i < sorted.length; i++){
        var html = '<tr><td>'+sorted[i].name+'</td><td>'+sorted[i].value.toFixed(2)+'</td><td><button class="btn btn-mini" data="'+sorted[i].name+'">monitor</button></td></tr>';
        if(sorted[i].name.substr(0, 3) == "emo"){
            emo_html += html
            globalDataSources.push(sorted[i].name);
        } else {
            base_html += html
            globalDataTargets.push(sorted[i].name);
        }
    }
    table.html(emo_html + base_html);
    $('button', table).each(function(idx, button){
        $(button).on('click', function(evt){
            evt.preventDefault();
            addMonitor('modulator', $(button).attr('data'));
        });
    });
}

// data structures ----------------------------------------------------------------------


// data structure for net entities
function Node(uid, x, y, nodeSpaceUid, name, type, activation, state, parameters, gate_activations, gate_configuration, is_highdim, inlinks, outlinks, inputmap) {
	this.uid = uid;
	this.x = x;
	this.y = y;
	this.activation = activation || 0;
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
    this.parameters = parameters || [];
    this.bounds = null; // current bounding box (after scaling)
    this.slotIndexes = [];
    this.gateIndexes = [];
    this.gate_configuration = gate_configuration || {};
    this.gate_activations = gate_activations || {};
    this.is_highdim = is_highdim;
    this.inlinks = inlinks || 0;
    this.outlinks = outlinks || 0;
    this.symbol = nodetypes[type].symbol || type.substr(0,1);
    this.is_flow_module = (this.type in flow_modules)
    this.inputmap = inputmap;
    var i;
    for(i in nodetypes[type].slottypes){
        this.slots[nodetypes[type].slottypes[i]] = new Slot(nodetypes[type].slottypes[i]);
    }
    for(i in nodetypes[type].gatetypes){
        var gatetype = nodetypes[type].gatetypes[i]
        parameters = {};
        activation = this.gate_activations[gatetype];
        var highdim = is_highdim && gatetype in nodetypes[type].dimensionality.gates;
        this.gates[gatetype] = new Gate(gatetype, i, activation, this.gate_configuration[gatetype], highdim);
    }
    this.slotIndexes = Object.keys(this.slots);
    this.gateIndexes = Object.keys(this.gates);

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
        this.gate_configuration = item.gate_configuration || {};
        this.gate_activations = item.gate_activations;
        this.outlinks = item.outlinks;
        this.inlinks = item.inlinks;
        this.inputmap = item.inputmap;
        for(var i in nodetypes[type].gatetypes){
            var gatetype = nodetypes[type].gatetypes[i];
            this.gates[gatetype].gate_configuration = this.gate_configuration[gatetype];
            this.gates[gatetype].activation = this.gate_activations[gatetype];

        }
    };

    this.gatechecksum = function(){
        var gatechecksum = "";
        for(var i in nodetypes[type].gatetypes){
            var gatetype = nodetypes[type].gatetypes[i];
            gatechecksum += "-" + this.gates[gatetype].activation;
            gatechecksum += ':' + this.gates[gatetype].gate_cgatefunction;
        }
        return gatechecksum;
    };
}

// target for links, part of a net entity
function Slot(name) {
	this.name = name;
	this.incoming = {};
	this.activation = 0;
}

// source for links, part of a net entity
function Gate(name, index, activation, gate_configuration, is_highdim) {
	this.name = name;
    this.index = index;
	this.outgoing = {};
	this.activation = activation;
    this.is_highdim = is_highdim;
    this.gatefunction = 'identity';
    this.gatefunction_parameters = {}
    if (gate_configuration) {
        if(gate_configuration.gatefunction){
            this.gatefunction = gate_configuration.gatefunction;
        }
        if(gate_configuration.gatefunction_parameters){
            this.gatefunction_parameters = gate_configuration.gatefunction_parameters;
        }
    }
}

// link, connects two nodes, from a gate to a slot
function Link(uid, sourceNodeUid, gateName, targetNodeUid, slotName, weight, is_flow_connection){
    this.uid = uid;
    this.sourceNodeUid = sourceNodeUid;
    this.gateName = gateName;
    this.targetNodeUid = targetNodeUid;
    this.slotName = slotName;
    this.weight = weight;
    this.is_flow_connection = is_flow_connection;
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
        if(((sourceNode.uid && !gate) || (targetNode.uid && !slot)) && !link.is_flow_connection){
            console.error('Incompatible slots and gates: gate:'+ link.gateName + ' / slot:'+link.slotName);
            return;
        }
        if(link.is_flow_connection){
            renderFlowConnection(link);
            flow_connections[link.uid] = link;
        } else {
            links[link.uid] = link;
            // check if link is visible
            if (!(isOutsideNodespace(nodes[link.sourceNodeUid]) &&
                isOutsideNodespace(nodes[link.targetNodeUid]))) {
                renderLink(link);
            }
        }
    } else {
        console.error("Error: Attempting to create link without establishing nodes first");
    }
}

function redrawLink(link, forceRedraw){
    var oldLink = links[link.uid];
    if (forceRedraw || !oldLink || !(link.uid in linkLayer.children) || oldLink.weight != link.weight ||
            !nodes[oldLink.sourceNodeUid] || !nodes[link.sourceNodeUid] ||
            nodes[oldLink.sourceNodeUid].gates[oldLink.gateName].activation !=
            nodes[link.sourceNodeUid].gates[link.gateName].activation) {
        if(link.uid in linkLayer.children){
            linkLayer.children[link.uid].remove();
        }
        renderLink(link);
        links[link.uid] = link;
    }
}
function redrawFlowConnection(link, forceRedraw){
    var oldLink = flow_connections[link.uid];
    if (forceRedraw || !oldLink || !(link.uid in linkLayer.children) || oldLink.weight != link.weight ||
            !nodes[oldLink.sourceNodeUid] || !nodes[link.sourceNodeUid]) {
        if(link.uid in linkLayer.children){
            linkLayer.children[link.uid].remove();
        }
        renderFlowConnection(link);
        flow_connections[link.uid] = link;
    }
}

// delete a link from the array, and from the screen
function removeLink(link) {
    sourceNode = nodes[link.sourceNodeUid];
    targetNode = nodes[link.targetNodeUid];
    if(!sourceNode || ! targetNode){
        delete links[link.uid];
        if (link.uid in linkLayer.children) linkLayer.children[link.uid].remove();
        if(sourceNode) delete sourceNode.gates[link.gateName].outgoing[link.uid];
        if(targetNode) delete targetNode.slots[link.slotName].incoming[link.uid];
        return;
    }
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
    var el = canvas_container;
    for (var nodeUid in nodeLayer.children) {
        if (nodeUid in nodes) {
            var node = nodes[nodeUid];
            maxX = Math.max(maxX, node.x * viewProperties.zoomFactor + node.bounds.width + viewProperties.frameWidth);
            maxY = Math.max(maxY, node.y * viewProperties.zoomFactor + node.bounds.height + viewProperties.frameWidth);
        }
    }
    var newSize = new Size(
        Math.min(viewProperties.xMax, Math.max((maxX+viewProperties.frameWidth),
        el.width())),
        Math.min(viewProperties.yMax, Math.max(el.height(), maxY)));
    if(newSize.height && newSize.width){
        view.viewSize = newSize;
    }
    for(var uid in nodes){
        redrawNode(nodes[uid]);
    }
    view.draw(true);
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
    for(uid in flow_connections){
        var sourceNode = nodes[flow_connections[uid].sourceNodeUid];
        var targetNode = nodes[flow_connections[uid].targetNodeUid];
        // check if the link is visible
        if (!(isOutsideNodespace(sourceNode) && isOutsideNodespace(targetNode))) {
            renderFlowConnection(flow_connections[uid]);
        }
    }
    updateViewSize();
    drawGridLines(view.element);
}

// like activation change, only put the node elsewhere and redraw the links
function redrawNode(node, forceRedraw) {
    if(forceRedraw || nodeRedrawNeeded(node)){
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
            node.name == nodes[node.uid].name &&
            node.activation == nodes[node.uid].activation &&
            node.gatechecksum() == nodes[node.uid].gatechecksum() &&
            viewProperties.zoomFactor == nodes[node.uid].zoomFactor){
            return false;
        }
    }
    return true;
}

// redraw only the links that are connected to the given node
function redrawNodeLinks(node) {
    var linkUid;
    for(var dir in node.placeholder){
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
    redrawNodeFlowConnections(node);
}
function redrawNodeFlowConnections(node) {
    if(node.is_flow_module){
        for(var uid in flow_connections){
            if(flow_connections[uid].sourceNodeUid == node.uid || flow_connections[uid].targetNodeUid == node.uid){
                if(uid in linkLayer.children) {
                    linkLayer.children[uid].remove();
                }
                renderFlowConnection(flow_connections[uid]);
            }
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
        if (sourceNode.type=="Sensor" || sourceNode.type == "Actuator") {
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
        if (targetNode.type=="Sensor" || targetNode.type == "Actuator") {
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
    if(nodespaceProperties[currentNodeSpace].renderlinks == 'no'){
        return;
    }
    if(nodespaceProperties[currentNodeSpace].renderlinks == 'selection'){
        var is_selected = selection && (link.sourceNodeUid in selection || link.targetNodeUid in selection);
        if(!is_selected){
            return;
        }
    }
    var sourceNode = nodes[link.sourceNodeUid];
    var targetNode = nodes[link.targetNodeUid];

    if(isOutsideNodespace(sourceNode) && isOutsideNodespace(targetNode)){
        return;
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
    if(sourceNode){
        link.strokeColor = activationColor(sourceNode.gates[link.gateName].activation * link.weight, viewProperties.linkColor);
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
    if (nodespaceProperties[currentNodeSpace].activation_display == 'alpha'){
        if(sourceNode){
            linkContainer.opacity = Math.max(0.1, sourceNode.activation)
        } else {
            linkContainer.opacity = 0.1
        }
    }
    linkLayer.addChild(linkContainer);
}

function renderFlowConnection(link, force) {
    if(nodespaceProperties[currentNodeSpace].renderlinks == 'no'){
        return;
    }
    if(nodespaceProperties[currentNodeSpace].renderlinks == 'selection'){
        var is_selected = selection && (link.sourceNodeUid in selection || link.targetNodeUid in selection);
        if(!is_selected){
            return;
        }
    }
    var sourceNode = nodes[link.sourceNodeUid];
    var targetNode = nodes[link.targetNodeUid];
    if(!sourceNode || !targetNode){
        // TODO: deleting nodes need to clean flowconnections
        return;
    }
    var sourceType = flow_modules[sourceNode.type];
    var targetType = flow_modules[targetNode.type];

    var itemlength = sourceNode.bounds.width / sourceType.outputs.length;
    var idx = sourceType.outputs.indexOf(link.gateName);
    var linkStart = new Point(sourceNode.bounds.x + ((idx+.5) * itemlength), sourceNode.bounds.y + viewProperties.lineHeight * 0.7 * viewProperties.zoomFactor);
    itemlength = targetNode.bounds.width / targetType.inputs.length;
    idx = targetType.inputs.indexOf(link.slotName);
    var linkEnd = new Point(targetNode.bounds.x + ((idx+.5) * itemlength), targetNode.bounds.y + targetNode.bounds.height - viewProperties.lineHeight * 0.3 * viewProperties.zoomFactor);

    var linkPath = new Path([linkStart, linkEnd]);
    linkPath.strokeColor = viewProperties.flowConnectionColor;
    linkPath.strokeWidth = 10 * viewProperties.zoomFactor;
    linkPath.opacity = 0.8;
    linkPath.name = "path";
    linkPath.dashArray = [viewProperties.zoomFactor,viewProperties.zoomFactor];
    var linkContainer = new Group(linkPath);
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
        selectNode(node.uid, false);
    }
    node.zoomFactor = viewProperties.zoomFactor;
}

// draw net entity with slots and gates
function renderFullNode(node) {
    node.bounds = calculateNodeBounds(node);
    var nodeItem;
    if(node.type == 'Comment'){
        nodeItem = renderComment(node);
    } else if(node.type in flow_modules){
        var skeleton = createFullNodeSkeleton(node);
        var activations = createFullNodeActivations(node);
        var inputs = createFlowInputs(node);
        var outputs = createFlowOutputs(node);
        var gateAnnotations = createGateAnnotation(node);
        nodeItem = new Group([activations, skeleton, inputs, outputs, gateAnnotations]);
    } else {
        var skeleton = createFullNodeSkeleton(node);
        var activations = createFullNodeActivations(node);
        var titleBar = createFullNodeLabel(node);
        var gateAnnotations = createGateAnnotation(node);
        nodeItem = new Group([activations, skeleton, titleBar, gateAnnotations]);
    }
    nodeItem.name = node.uid;
    nodeItem.isCompact = false;
    nodeLayer.addChild(nodeItem);
}

function createFlowInputs(node){
    var inputs = flow_modules[node.type].inputs;
    var num = inputs.length;
    var inputshapes = [];
    var itemlength = node.bounds.width / num;
    for(var i = 0; i < num; i++){
        var label = new PointText(node.bounds.x + ((i+.5) * itemlength), node.bounds.y + node.bounds.height - viewProperties.lineHeight * 0.3 * viewProperties.zoomFactor);
        label.content = inputs[i];
        label.name = inputs[i];
        label.paragraphStyle.justification = 'center';
        label.characterStyle = {
            fillColor: viewProperties.nodeFontColor,
            fontSize: viewProperties.fontSize*viewProperties.zoomFactor
        }
        if(num > 1 && i < num - 1){
            var border = new Path.Rectangle(
                    node.bounds.x + ((i+1) * itemlength),
                    node.bounds.y + node.bounds.height - viewProperties.lineHeight * viewProperties.zoomFactor,
                    viewProperties.shadowDisplacement.x * viewProperties.zoomFactor,
                    viewProperties.lineHeight * viewProperties.zoomFactor
                );
            border.fillColor = viewProperties.shadowColor;
            border.fillColor.alpha = 0.3;
            inputshapes.push(new Group([label, border]));
        } else {
            inputshapes.push(label);
        }
    }
    var bounds = node.bounds;
    var upper = new Path.Rectangle(bounds.x+viewProperties.shadowDisplacement.x*viewProperties.zoomFactor,
        bounds.y + bounds.height - (viewProperties.lineHeight - viewProperties.strokeWidth)*viewProperties.zoomFactor,
        bounds.width - viewProperties.shadowDisplacement.x*viewProperties.zoomFactor,
        viewProperties.innerShadowDisplacement.y*viewProperties.zoomFactor);
    upper.fillColor = viewProperties.shadowColor;
    upper.fillColor.alpha = 0.3;
    var lower = upper.clone();
    lower.position += new Point(0, viewProperties.innerShadowDisplacement.y*viewProperties.zoomFactor);
    lower.fillColor = viewProperties.highlightColor;
    lower.fillColor.alpha = 0.3;
    var delimiter = new Group([upper, lower]);
    delimiter.name = "delimiter";
    inputshapes.push(delimiter);
    var group = new Group(inputshapes);
    group.name = 'flowModuleInputs';
    return group;
}

function createFlowOutputs(node, with_delimiter){
    var outputs = flow_modules[node.type].outputs;
    var num = outputs.length;
    var outputshapes = [];
    var itemlength = node.bounds.width / num;
    for(var i = 0; i < num; i++){
        var label = new PointText(node.bounds.x + ((i+.5) * itemlength), node.bounds.y + viewProperties.lineHeight * 0.7 * viewProperties.zoomFactor);
        label.content = outputs[i];
        label.name = outputs[i];
        label.paragraphStyle.justification = 'center';
        label.characterStyle = {
            fillColor: viewProperties.nodeFontColor,
            fontSize: viewProperties.fontSize*viewProperties.zoomFactor
        }
        if(num > 1 && i < num - 1){
            var border = new Path.Rectangle(
                    node.bounds.x + ((i+1) * itemlength),
                    node.bounds.y,
                    viewProperties.shadowDisplacement.x * viewProperties.zoomFactor,
                    viewProperties.lineHeight * viewProperties.zoomFactor
                );
            border.fillColor = viewProperties.shadowColor;
            border.fillColor.alpha = 0.3;
            outputshapes.push(new Group([label, border]));
        } else {
            outputshapes.push(label);
        }
    }
    if(with_delimiter){
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
        delimiter = new Group([upper, lower]);
        delimiter.name = "delimiter";
        outputshapes.push(delimiter);
    }
    return new Group(outputshapes);
}

function renderComment(node){
    var bounds = node.bounds;
    var commentGroup = new Group();
    commentText = new PointText(bounds.x + 10, bounds.y + viewProperties.lineHeight * viewProperties.zoomFactor);
    commentText.content = node.parameters.comment || '';
    commentText.name = "comment";
    commentText.fillColor = viewProperties.nodeFontColor;
    commentText.fontSize = viewProperties.fontSize * viewProperties.zoomFactor;
    commentText.paragraphStyle.justification = 'left';
    bounds.width = Math.max(commentText.bounds.width, bounds.width);
    bounds.height = Math.max(commentText.bounds.height, bounds.height);
    commentText.position.x = bounds.x + 10;
    commentText.position.y = bounds.y + 10;
    bounds.x = bounds.x - bounds.width/2;
    bounds.y = bounds.y - bounds.height/2;
    var commentBox = new Path.Rectangle(bounds.x, bounds.y, bounds.width+20, bounds.height +20);
    commentBox.fillColor = new Color('white');
    commentBox.strokeColor = viewProperties.selectionColor;
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
    } else if(node.type in flow_modules){
        var skeleton = createCompactNodeSkeleton(node);
        var activations = createCompactNodeActivations(node);
        var label = createCompactNodeLabel(node);
        var inputs = createFlowInputs(node);
        var outputs = createFlowOutputs(node, true);
        nodeItem = new Group([activations, skeleton, inputs, outputs]);
        if (label){
            nodeItem.addChild(label);
        }
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
    } else {
        width = height = viewProperties.compactNodeWidth * viewProperties.zoomFactor;
    }
    if(node.type in flow_modules){
        def = flow_modules[node.type];
        width = Math.max(def.inputs.length, def.outputs.length) * viewProperties.flowModuleWidth * viewProperties.zoomFactor;
        height += viewProperties.lineHeight * viewProperties.zoomFactor;
    }
    return new Rectangle(node.x*viewProperties.zoomFactor - width/2,
        node.y*viewProperties.zoomFactor - height/2, // center node on origin
        width, height);
}

// determine shape of a full node
function createFullNodeShape(node) {
    if (node.type == "Comment"){
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
        case "Actuator":
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
        case "LSTM": // draw circle
        case "Concept": // draw circle
        case "Pipe": // draw circle
        case "Script": // draw circle
        case "Neuron":
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

function createGateAnnotation(node){
    var labels = [];
    for (i = 0; i< node.gateIndexes.length; i++){
        var g = node.gateIndexes[i];
        var gatebounds = getGateBounds(node, i);
        if (node.gates[g].gatefunction && node.gates[g].gatefunction != 'identity'){
            var gatefuncHint = new PointText(new Point(gatebounds.right-(8*viewProperties.zoomFactor),gatebounds.center.y - 2*viewProperties.zoomFactor));
            gatefuncHint.content = gatefunction_icons[node.gates[g].gatefunction];
            gatefuncHint.fillColor = viewProperties.nodeForegroundColor;
            gatefuncHint.fontSize = (viewProperties.fontSize-2) * viewProperties.zoomFactor;
            labels.push(gatefuncHint);
        }
    }
    var g = new Group(labels);
    return g;
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
    var pos = new Point(bounds.x+bounds.width/2,
        bounds.y+bounds.height/2+viewProperties.symbolSize/2*viewProperties.zoomFactor);
    var symbolText = new PointText(pos);
    symbolText.fillColor = viewProperties.nodeForegroundColor;
    symbolText.content = node.symbol;
    symbolText.fontSize = viewProperties.symbolSize*viewProperties.zoomFactor;
    symbolText.paragraphStyle.justification = 'center';
    pos.x += 1 * viewProperties.zoomFactor;
    pos.y -= 5 * viewProperties.zoomFactor;
    gatefuncHint = new PointText(pos);
    gatefuncHint.content = '';
    gatefuncHint.fillColor = viewProperties.nodeForegroundColor;
    gatefuncHint.fontSize = viewProperties.fontSize*viewProperties.zoomFactor;
    var non_standard_gatefunc = [];
    for (var g in node.gates){
        if(node.gates[g].gatefunction && node.gates[g].gatefunction != 'identity'){
            if(non_standard_gatefunc.indexOf(node.gates[g].gatefunction) < 0){
                non_standard_gatefunc.push(node.gates[g].gatefunction);
            }
        }
    }
    if(non_standard_gatefunc.length > 0){
        if(non_standard_gatefunc.length == 1){
            gatefuncHint.content = gatefunction_icons[non_standard_gatefunc[0]];
        } else {
            gatefuncHint.content = '*';
        }
    }
    if(gatefuncHint.content){
        symbolText.point.x -= 3 * viewProperties.zoomFactor;
        symbolText.fontSize = viewProperties.fontSize*viewProperties.zoomFactor;
    }
    var g = new Group([symbolText, gatefuncHint]);
    return g;
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
        labelText.content = node.name || '';
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
        if((nodespaceProperties[currentNodeSpace].activation_display != 'alpha') || node.activation > 0.5){
            node.fillColor = nodeItem.children["activation"].children["body"].fillColor =
                activationColor(node.activation, viewProperties.nodeColor);
        }
        if(nodespaceProperties[currentNodeSpace].activation_display == 'alpha'){
            for(var i in nodeItem.children){
                if(nodeItem.children[i].name == 'labelText'){
                    nodeItem.children[i].opacity = 0;
                    if (node.activation > 0.5){
                        nodeItem.children[i].opacity = node.activation;
                    }
                } else {
                    nodeItem.children[i].opacity = Math.max(0.1, node.activation)
                }
            }
        }

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
    }
}

// mark node as selected, and add it to the selected nodes
function selectNode(nodeUid, redraw) {
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
    if (redraw !== false)
        redrawNode(nodes[nodeUid], true);
}

// remove selection marking of node, and remove if from the set of selected nodes
function deselectNode(nodeUid) {
    if (nodeUid in selection) {
        delete selection[nodeUid];
        nodes[nodeUid].renderCompact = null;
        if(nodeUid in nodeLayer.children){
            var outline;
            if(nodes[nodeUid].type == 'Comment'){
                outline = nodeLayer.children[nodeUid].children["body"];
            } else {
                outline = nodeLayer.children[nodeUid].children["activation"].children["body"];
            }
            outline.strokeColor = null;
            outline.strokeWidth = viewProperties.outlineWidth;
            redrawNode(nodes[nodeUid], true);
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
            if(nodespaceProperties[currentNodeSpace].renderlinks == 'no' || nodespaceProperties[currentNodeSpace].renderlinks == 'selection'){
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
function deselectAll(except) {
    for (var uid in selection){
        if (except && except.indexOf(uid) > -1) continue;
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
                    clickType = "node";
                    openMultipleNodesContextMenu(event.event);
                    return;
                }
                else if (!linkCreationStart) {
                    selectNode(nodeUid);
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
                    node.renderCompact = false;
                    selectNode(node.uid);
                    selectGate(node, gate);
                    showGateForm(node, gate);
                    if (isRightClick(event)) {
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
                    path = null;
                    movePath = false;
                    return;
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
                if (!event.modifiers.shift && !event.modifiers.command) {
                    var except = [];
                    if(isRightClick(event)){
                        // if rightclicking a link, nodes need not be deselected
                        for(uid in selection){
                            if(uid in nodes){
                                except.push(uid);
                            }
                        }
                    }
                    deselectAll(except);
                }
                if (event.modifiers.command && path.name in selection) deselectLink(path.name); // toggle
                else selectLink(path.name);
                clickType = "link";
                clickOriginUid = path.name;
                if (isRightClick(event)) {
                    openContextMenu("#link_menu", event.event);
                } else {
                    showLinkForm(path.name);
                }
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
                    if(linkCreationStart){
                        nodes[oldHover].renderCompact = null;
                        redrawNode(nodes[oldHover], true);
                    }
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
                    if(linkCreationStart){
                        nodes[nodeUid].renderCompact = false;
                        redrawNode(nodes[nodeUid], true);
                    }
                }
                return;
            }
        }
    }
    if(hoverNode && hoverNode.uid in nodes){
        var oldHover = hoverNode.uid;
        hoverNode = null;
        if(linkCreationStart){
            nodes[oldHover].renderCompact = null;
            redrawNode(nodes[oldHover], true);
        }
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
            if(node.bounds.contains(p)){
                if(isCompact(nodeUid)){
                    nodes[nodeUid].renderCompact = false;
                    redrawNode(nodes[nodeUid], true);
                    view.draw();
                }
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
    function moveNode(uid, snap, offset){
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
        var oldpos = {
            'x': node.x,
            'y': node.y
        };
        if(snap){
            if(offset){
                node.x += offset.x;
                node.y += offset.y;
            } else {
                node.x = rounded.x / viewProperties.zoomFactor;
                node.y = rounded.y / viewProperties.zoomFactor;
            }
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
        return {
            'x': node.x - oldpos.x,
            'y': node.y - oldpos.y
        };
    }
    if (movePath) {
        path.nodeMoved = true;
        if(dragMultiples){
            var offset = null;
            if(nodenet_data.snap_to_grid){
                offset = moveNode(path.name, true);
            }
            for(var uid in selection){
                if(uid in nodes && (!nodenet_data.snap_to_grid || uid != path.name)){
                    moveNode(uid, nodenet_data.snap_to_grid, offset);
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
            movedNodes = {};
            if(dragMultiples){
                for(var uid in selection){
                    if(uid in nodes){
                        movedNodes[uid] = [nodes[uid].x, nodes[uid].y];
                    }
                }
            } else {
                movedNodes[path.name] = [nodes[path.name].x, nodes[path.name].y];
            }
            moveNodesOnServer(movedNodes);
            movePath = false;
            updateViewSize();
        } else if(!event.modifiers.shift && !event.modifiers.control && !event.modifiers.command && event.event.button != 2){
            if(path.name in nodes){
                var except = [path.name];
                deselectAll(except);
                selectNode(path.name);
                showNodeForm(path.name, true);
            }
        }
    }
    if(selectionStart){
        selectionStart = null;
        selectionRectangle.x = selectionRectangle.y = 1;
        selectionRectangle.width = selectionRectangle.height = 1;
        selectionBox.setBounds(selectionRectangle);
    }
    if(currentNodenet && nodenet_data){
        loadLinksForSelection(null, false, true);
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
    prerenderLayer.removeChildren();
    redrawNodeNet(currentNodeSpace);
}

function zoomOut(event){
    event.preventDefault();
    if (viewProperties.zoomFactor > 0.2) viewProperties.zoomFactor -= 0.1;
    $.cookie('zoom_factor', viewProperties.zoomFactor, { expires: 7, path: '/' });
    prerenderLayer.removeChildren();
    redrawNodeNet(currentNodeSpace);
}

function onResize(event) {
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

function loadLinksForSelection(callback, force_load, show_node_form){
    var skiploading = false;
    if(nodespaceProperties[currentNodeSpace].renderlinks == 'none'){
        skiploading = true;
    }
    var uids = [];
    var skipped = [];
    var load_links = false;
    for(var uid in selection){
        if(uid in nodes && (force_load || nodes[uid].inlinks < viewProperties.load_link_threshold && nodes[uid].outlinks < viewProperties.load_link_threshold)){
            uids.push(uid)
        } else {
            skipped.push(uid)
        }
        if(skipped.indexOf(uid) < 0 && (nodes[uid].inlinks > 0 || nodes[uid].outlinks > 0)){
            load_links = true;
        }
    }
    if(nodespaceProperties[currentNodeSpace].renderlinks == 'always' && !load_links){
        skiploading = true;
    }
    if(!skiploading && uids.length){
        api.call('get_links_for_nodes',
            {'nodenet_uid': currentNodenet,
             'node_uids': uids },
              function(data){
                for(var i=0; i < uids.length; i++){
                    // all links loaded
                    nodes[uids[i]].outlinks = 0
                    nodes[uids[i]].inlinks = 0
                }
                if(callback){
                    callback(data);
                } else {
                    for(var uid in data.nodes){
                        addNode(new Node(uid, data.nodes[uid]['position'][0], data.nodes[uid]['position'][1], data.nodes[uid].parent_nodespace, data.nodes[uid].name, data.nodes[uid].type, data.nodes[uid].activation, data.nodes[uid].state, data.nodes[uid].parameters, data.nodes[uid].gate_activations, data.nodes[uid].gate_configuration, data.nodes[uid].is_highdimensional, data.nodes[uid].inlinks, data.nodes[uid].outlinks));
                    }
                    var linkdict = {};
                    for(var i = 0; i < data.links.length; i++){
                        luid = data.links[i]['source_node_uid'] + ":" + data.links[i]['source_gate_name'] + ":" + data.links[i]['target_slot_name'] + ":" + data.links[i]['target_node_uid'];
                        linkdict[luid] = data.links[i];
                    }
                    addLinks(linkdict);
                    if(uids.length == 1 && uids[0] in selection && clickType != "gate" && show_node_form){
                        showNodeForm(uids[0]);
                    }
                }
                view.draw(true);
            }
        );
    } else if(skipped.length == 1 && skipped[0] in nodes && skipped[0] in selection && clickType != "gate" && show_node_form){
        showNodeForm(skipped[0]);
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
    $("#edit_link_modal .btn-primary").on('click', handleEditLink);
    $("#edit_link_modal form").on('submit', handleEditLink);
    $("#nodenet").on('dblclick', onDoubleClick);
    $("#nodespace_up").on('click', handleNodespaceUp);
    $("#nodespace_add").on('click', createNodespace);
    gate_form_trigger = $('.gate_additional_trigger');
}

function initializeControls(){
    $('#zoomOut').on('click', zoomOut);
    $('#zoomIn').on('click', zoomIn);
    $('#nodespace_control').on('click', ['data-nodespace'] ,function(event){
        event.preventDefault();
        var nodespace = $(event.target).attr('data-nodespace');
        if(nodespace && nodespace != currentNodeSpace){
            refreshNodespace(nodespace, -1);
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
    $('#paste_mode_selection_modal .btn-primary').on('click', function(event){
        event.preventDefault();
        var form = $('#paste_mode_selection_modal form');
        handlePasteNodes(form.serializeArray()[0].value);
        $('#paste_mode_selection_modal').modal('hide');
    });
}

var clickPosition = null;

function buildRecursiveDropdown(cat, html, current_category, generate_items){
    if(!current_category){
        current_category='';
    }
    var catentries = []
    for(var key in cat){
        catentries.push(key);
    }
    catentries.sort();
    for(var i = 0; i < catentries.length; i++){
        if(catentries[i] == ''){
            continue;
        }
        var newcategory = current_category || '';
        if(current_category == ''){
            newcategory += catentries[i]
        }
        else {
            newcategory += '/'+catentries[i];
        }
        html += '<li class="noop"><a>'+catentries[i]+'<i class="icon-chevron-right"></i></a>';
        html += '<ul class="sub-menu dropdown-menu">'
        html += buildRecursiveDropdown(cat[catentries[i]], '', newcategory, generate_items);
        html += '</ul></li>';
    }

    html += generate_items(current_category);

    return html
}

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
            html += '<li class="divider"></li><li class="noop"><a>Create Native Module<i class="icon-chevron-right"></i></a>';
            html += '<ul class="sub-menu dropdown-menu">';
            html += buildRecursiveDropdown(native_module_categories, '', '', function(current_category){
                items = '';
                for(var idx in sorted_native_modules){
                    key = sorted_native_modules[idx];
                    if(native_modules[key].category == current_category){
                        items += '<li><a data-create-node="' + key + '">'+ native_modules[key].name +'</a></li>';
                    }
                }
                return items;
            });
            html += '</ul></li>';
        }
        if(Object.keys(flow_modules).length){
            html += '<li class="divider"></li><li class="noop"><a>Create Flow Module<i class="icon-chevron-right"></i></a>';
            html += '<ul class="sub-menu dropdown-menu">';
            html += buildRecursiveDropdown(flow_module_categories, '', '', function(current_category){
                items = '';
                for(var idx in sorted_flow_modules){
                    key = sorted_flow_modules[idx];
                    if(flow_modules[key].category == current_category){
                        items += '<li><a data-create-node="' + key + '">'+ flow_modules[key].name +'</a></li>';
                    }
                }
                return items;
            });
            html += '</ul></li>';
        }
        html += '<li class="divider"></li><li data-paste-nodes';
        if(Object.keys(clipboard).length === 0){
            html += ' class="disabled"';
        }
        html += '><a href="#">Paste nodes</a></li>';
        html += getOperationsDropdownHTML(["Nodespace"], 1);
        list.html(html);
    }
    $(menu_id+" .dropdown-toggle").dropdown("toggle");
    $(menu_id+" li.noop > a").on('click', function(event){event.stopPropagation();})
}

function openMultipleNodesContextMenu(event){
    var node = null;
    var compact = false;
    var nodetypes = [];
    var count = 0
    for(var uid in selection){
        if(!node) node = nodes[uid];
        if(isCompact(nodes[uid])) {
            compact = true;
        }
        if(nodetypes.indexOf(nodes[uid].type) == -1){
            nodetypes.push(nodes[uid].type);
        }
        count += 1;
    }
    var menu = $('#multi_node_menu .nodenet_menu');
    var html = '';
    if(compact){
        html += '<li><a href="">Expand</a></li><li class="divider"></li>';
    }
    html += '<li data-copy-nodes><a href="#">Copy nodes</a></li>'+
        '<li data-paste-nodes><a href="#">Paste nodes</a></li>'+
        '<li><a href="#">Delete nodes</a></li>';

    html += getOperationsDropdownHTML(nodetypes, count);

    if(nodetypes.length == 1){
        html += '<li class="divider"></li>' + getNodeLinkageContextMenuHTML(node);
    }
    html += '<li data-generate-fragment><a href="#">Generate netapi fragment</a></li>';
    menu.html(html);
    if(Object.keys(clipboard).length === 0){
        $('#multi_node_menu li[data-paste-nodes]').addClass('disabled');
    } else {
        $('#multi_node_menu li[data-paste-nodes]').removeClass('disabled');
    }
    openContextMenu('#multi_node_menu', event);
}

function getOperationsDropdownHTML(nodetypes, count){
    operation_categories = {};
    sorted_operations = [];

    applicable_operations = {};
    for(var key in available_operations){
        var conditions = available_operations[key].selection;
        for(var i in conditions){
            if((conditions[i].nodetypes.length == 0 || $(nodetypes).not(conditions[i].nodetypes).get().length == 0) &&
               (count >= conditions[i].mincount) &&
               (conditions[i].maxcount < 0 || count <= conditions[i].maxcount)){
                    applicable_operations[key] = available_operations[key];
            }
        }
    }

    categories = [];
    for(var key in applicable_operations){
        categories.push(applicable_operations[key].category.split('/'));
    }
    operation_categories = {}
    for(var i =0; i < categories.length; i++){
        buildCategoryTree(operation_categories, categories[i], 0);
    }
    sorted_operations = Object.keys(applicable_operations).sort();

    var html = '';
    if(sorted_operations.length){
        html += '<li class="divider"></li><li class="noop"><a>Operations<i class="icon-chevron-right"></i></a><ul class="sub-menu dropdown-menu">';
        html += buildRecursiveDropdown(operation_categories, '', '', function(current_category){
            items = '';
            for(var idx in sorted_operations){
                key = sorted_operations[idx];
                if(applicable_operations[key].category == current_category){
                    items += '<li><a title="'+applicable_operations[key].docstring+'" data-run-operation="' + key + '">'+ key +'</a></li>';
                }
            }
            return items;
        });
        html += '</ul></li>';
    } else {
        html += '<li class="divider"></li><li class="noop disabled"><a>Operations</a></li>';
    }
    return html;
}

function getNodeLinkageContextMenuHTML(node){
    var html = '';
    if (node.gateIndexes.length) {
        for (var gateName in node.gates) {
            if(node.type == "LSTM" && gateName == "por"){
                html += ('<li><a href="#" data-link-type="lstmpor">Draw lstm por links</a></li>');
            }
            else if(gateName in inverse_link_map){
                var compound = gateName+'/'+inverse_link_map[gateName];
                html += ('<li><a data-link-type="'+compound+'">Draw '+compound+' link</a></li>');
            }
            else if(inverse_link_targets.indexOf(gateName) == -1){
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
    var html = '';
    if(isCompact(node)){
        html += '<li><a href="">Expand</a></li><li class="divider"></li>';
    }
    html += getNodeLinkageContextMenuHTML(node);
    if(node.type == "Sensor"){
        html += '<li><a href="#">Select datasource</li>';
    }
    if(node.type == "Actuator"){
        html += '<li><a href="#">Select datatarget</li>';
    }
    html += '<li><a href="#">Add Monitor</a></li>' +
            '<li class="divider"></li>' +
             '<li><a href="#">Rename node</a></li>' +
             '<li><a href="#">Delete node</a></li>' +
             '<li data-copy-nodes><a href="#">Copy node</a></li>';

    html += getOperationsDropdownHTML([node.type], 1);
    menu.html(html);
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
    } else if($el.parent().attr('data-generate-fragment') === ""){
        generateFragment();
        return;
    } else if($el.parent().attr('data-paste-nodes') === ""){
        pasteNodes(clickPosition);
        $el.parentsUntil('.dropdown-menu').dropdown('toggle');
        return;
    }
    switch (clickType) {
        case null: // create nodes
            var type = $el.attr("data-create-node");
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
                case "Actuator":
                    callback = function(data){
                        clickOriginUid = data;
                        dialogs.notification('Please Select a datatarget for this actuator');
                        var target_select = $('#select_datatarget_modal select');
                        target_select.html('');
                        $("#select_datatarget_modal").modal("show");
                        var html = get_datatarget_options(currentWorldadapter);
                        target_select.html(html);
                        target_select.val(nodes[clickOriginUid].parameters['datatarget']).select().focus();
                    };
                    break;
            }
            if(type) {
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
            } else{
                if($el.attr('data-run-operation')){
                    selectOperation($el.attr('data-run-operation'));
                    break;
                }
                return false;
            }
            break;
        case "node":
            switch (menuText) {
                case "Delete nodes":
                    deleteNodeHandler(clickOriginUid);
                    break;
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
                case "Add Monitor":
                    addMonitor("node", nodes[clickOriginUid]);
                    break;
                case "Expand":
                    for(uid in selection){
                        nodes[uid].renderCompact = false;
                        redrawNode(nodes[uid], true);
                    }
                    break;
                default:
                    if($el.attr('data-run-operation')){
                        selectOperation($el.attr('data-run-operation'));
                    } else {
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
                    }
            }
            break;
        case "slot":
            switch (menuText) {
                case "Add monitor to slot":
                    var target = nodes[clickOriginUid];
                    addMonitor('slot', target, target.slotIndexes[clickIndex])
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
                    var target = nodes[clickOriginUid];
                    addMonitor('gate', target, target.gateIndexes[clickIndex]);
                    break;
                case "Remove monitor from gate":
                    removeMonitor(nodes[clickOriginUid], nodes[clickOriginUid].gateIndexes[clickIndex], 'gate');
                    break;
            }
            break;
        case "link":
            switch (menuText) {
                case "Add link-weight monitor":
                    addMonitor('link', links[clickOriginUid]);
                    break;
                case "Delete link":
                    deleteLinkHandler(clickOriginUid);
                    break;
                case "Edit link":
                    var linkUid = clickOriginUid;
                    if (linkUid in links) {
                        $("#link_weight_input").val(links[linkUid].weight);
                        $("#link_weight_input").focus();
                    }
                    break;
            }
    }
    view.draw();
}

function selectOperation(name){
    var modal = $('#operations-modal');
    if(available_operations[name].parameters.length){
        $('#recipe_modal .docstring').html(available_operations[name].docstring);
        var html = '';
        for(var i in available_operations[name].parameters){
            var param = available_operations[name].parameters[i];
            html += '' +
            '<div class="control-group">'+
                '<label class="control-label" for="op_'+param.name+'_input">'+param.name+'</label>'+
                '<div class="controls">'+
                    '<input type="text" name="'+param.name+'" class="input-xlarge" id="op_'+param.name+'_input" value="'+((param.default == null) ? '' : param.default)+'"/>'+
                '</div>'+
            '</div>';
        }
        $('fieldset', modal).html(html);
        var run = function(event){
            event.preventDefault();
            data = $('form', modal).serializeArray();
            parameters = {};
            for(var i=0; i < data.length; i++){
                parameters[data[i].name] = data[i].value
            }
            modal.modal('hide');
            runOperation(name, parameters);
        };
        $('form', modal).off().on('submit', run);
        $('.btn-primary', modal).off().on('click', run);
        modal.modal('show');
    } else {
        runOperation(name);
    }
}

function runOperation(name, params){
    var selection_uids = Object.keys(selection);
    if(selection_uids.length == 0){
        selection_uids = [currentNodeSpace];
    }
    api.call('run_operation', {
        'nodenet_uid': currentNodenet,
        'name': $el.attr('data-run-operation'),
        'parameters': params || {},
        'selection_uids': selection_uids}, function(data){
            refreshNodespace();
            $(document).trigger('runner_stepped')
            if(!$.isEmptyObject(data)){
                html = '';
                if(data.content_type && data.content_type.indexOf("image") > -1){
                    html += '<p><img src="'+data.content_type+','+data.data+'" /></p>';
                    delete data.content_type
                    delete data.data
                }
                if(Object.keys(data).length){
                    html += '<dl>';
                    for(var key in data){
                        html += '<dt>'+key+':</dt>';
                        if(typeof data[key] == 'string'){
                            html += '<dd>'+data[key]+'</dd>';
                        } else {
                            html += '<dd>'+JSON.stringify(data[key])+'</dd>';
                        }
                    }
                    html += '</dl>';
                }
                if(html){
                    $('#recipe_result .modal-body').html(html);
                    $('#recipe_result').modal('show');
                    $('#recipe_result button').off();
                }
            }
        }
    );
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
    var html = '';
    if(worldadapter){
        var sources = worldadapters[worldadapter].datasources;
        html += '<optgroup label="Datasources">';
        for(var i in sources){
            html += '<option value="'+sources[i]+'"'+ ((value && value==sources[i]) ? ' selected="selected"':'') +'>'+sources[i]+'</option>';
        }
        if(value && sources.indexOf(value) < 0) {
            html += '<option value="'+value+'"selected="selected">'+value+'</option>';
        }
        html += '</optgroup>';
    }
    if(globalDataSources.length){
        html += '<optgroup label="Nodenet Globals">';
        for(var i in globalDataSources){
            html += '<option value="'+globalDataSources[i]+'"'+ ((value && value==globalDataSources[i]) ? ' selected="selected"':'') +'>'+globalDataSources[i]+'</option>';
        }
        html += '</optgroup>';
    }
    return html;
}

function get_datatarget_options(worldadapter, value){
    var html = '';
    if(worldadapter){
        var targets = worldadapters[worldadapter].datatargets;
        html += '<optgroup label="Datatargets">';
        for(var i in targets){
            html += '<option value="'+targets[i]+'"'+ ((value && value==targets[i]) ? ' selected="selected"':'') +'>'+targets[i]+'</option>';
        }
        if(value && targets.indexOf(value) < 0) {
            html += '<option value="'+value+'"selected="selected">'+value+'</option>';
        }
        html += '</optgroup>';
    }
    if(globalDataTargets.length){
        html += '<optgroup label="Nodenet Globals">';
        for(var i in globalDataTargets){
            html += '<option value="'+globalDataTargets[i]+'"'+ ((value && value==globalDataTargets[i]) ? ' selected="selected"':'') +'>'+globalDataTargets[i]+'</option>';
        }
        html += '</optgroup>';
    }
    return html;
}

function createNodespace(event){
    event.preventDefault();
    api.call("add_nodespace", {
        'nodenet_uid': currentNodenet,
        'nodespace': null,
        'name': 'new nodespace'
    }, success=function(data) {
        var uid = data;
        nodespaceProperties[uid] = nodespace_property_defaults
        nodespaces[uid] = {
            'name': 'new nodespace',
            'parent': currentNodeSpace
        };
        handleEnterNodespace(uid, function(){
            dialogs.notification('Nodespace created', 'success');
            $('#nodespace_name').select().focus();
        });

    });
}

// let user create a new node
function createNodeHandler(x, y, name, type, parameters, callback) {
    params = {};
    if (!parameters) parameters = {};
    if (nodetypes[type]){
        for (var i in nodetypes[type].parameters){
            var param = nodetypes[type].parameters[i];
            var def = '';
            if(nodetypes[type].parameter_defaults){
                def = nodetypes[type].parameter_defaults[param] || '';
            }
            parameters[param] = parameters[param] || def;
        }
    }
    var method = "";
    var params = {
        nodenet_uid: currentNodenet,
        nodespace: currentNodeSpace,
        name: name}
    method = "add_node"
    params.type = type;
    params.position = [x,y,0];
    params.parameters = parameters;
    api.call(method, params,
        success=function(uid){
            addNode(new Node(uid, x, y, currentNodeSpace, name || '', type, null, null, parameters));
            selectNode(uid);
            if(callback) callback(uid);
            view.draw();
            showNodeForm(uid);
            getNodespaceList();
        }
    );
}

function generateFragment(){
    api.call("generate_netapi_fragment",
        {nodenet_uid:currentNodenet, node_uids: selection},
        success=function(data){
            var modal = $('#copy_paste_modal');
            $('#copy_paste_modal .title').html("Netapi code fragment");
            $('#copy_paste_text').val(data);
            modal.modal("show");
            $('#copy_paste_text').select();
        }
    );
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
        offset = [(clickPosition.x / viewProperties.zoomFactor) - (copyPosition.x), (clickPosition.y / viewProperties.zoomFactor) - (copyPosition.y), 0];
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
        var links_data = {};
        for(var key in data){
            var n = data[key];
            addNode(new Node(n.uid, n.position[0], n.position[1], n.parent_nodespace, n.name, n.type, null, null, n.parameters));
            if(n.parent_nodespace == currentNodeSpace){
                selectNode(n.uid);
            }
            for(gate in n.links){
                for(var i = 0; i < n.links[gate].length; i++){
                    luid = uid + ":" + gate + ":" + n.links[gate][i]['target_slot_name'] + ":" + n.links[gate][i]['target_node_uid']
                    links_data[luid] = n.links[gate][i]
                    links_data[luid].source_node_uid = uid
                    links_data[luid].source_gate_name = gate
                }
            }
        }
        addLinks(links_data);
        view.draw();
    });
}

// let user delete the current node, or all selected nodes
function deleteNodespace(event, nodespace_uid){
    if(!nodespace_uid){
        nodespace_uid = currentNodeSpace;
    }
    var params = {
        nodenet_uid: currentNodenet,
        nodespace: nodespace_uid
    }
    var parent = nodespaces[nodespace_uid].parent;
    api.call("delete_nodespace", params,
        success=function(data){
            dialogs.notification('nodespace deleted', 'success');
            getNodespaceList();
            refreshNodespace(parent, -1);
        }
    );
}

function deleteNodeHandler(nodeUid) {
    var deletedNodes = [];
    for (var selected in selection) {
        if(selection[selected].constructor == Node){
            deletedNodes.push(selected);
            removeNode(nodes[selected]);
            delete selection[selected];
        }
    }
    if(deletedNodes.length){
        api.call('delete_nodes', {nodenet_uid: currentNodenet, node_uids: deletedNodes}, function(){
            dialogs.notification('nodes deleted', 'success');
        });
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
    links[linkUid].weight = weight;
    redrawLink(links[linkUid], true);
    view.draw();
    api.call("set_link_weight", {
        nodenet_uid:currentNodenet,
        source_node_uid: links[linkUid].sourceNodeUid,
        gate_type: links[linkUid].gateName,
        target_node_uid: links[linkUid].targetNodeUid,
        slot_type: links[linkUid].slotName,
        weight: weight,
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
                    nodes[targetUid] = new Node(data.uid, data.position[0], data.position[1], data.parent_nodespace, data.name, data.type, data.activation, data.state, data.parameters, data.gate_activations, data.gate_configuration, data.is_highdimensional, data.inlinks, data.outlinks);
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
                            nodes[targetUid] = new Node(data.uid, data.position[0], data.position[1], data.parent_nodespace, data.name, data.type, data.activation, data.state, data.parameters, data.gate_activations, data.gate_configuration, data.is_highdimensional, data.inlinks, data.outlinks);
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

    targetNode.renderCompact = null;
    redrawNode(targetNode, true);
    deselectAll();

    for(var i=0; i < linkCreationStart.length; i++){
        var sourceNode = linkCreationStart[i].sourceNode;
        var sourceUid = linkCreationStart[i].sourceNode.uid;
        selectNode(sourceUid);
        var gateIndex = linkCreationStart[i].gateIndex;

        if (!slotIndex || slotIndex < 0) slotIndex = 0;

        if ((targetUid in nodes) &&
            nodes[targetUid].slots && (nodes[targetUid].slotIndexes.length > slotIndex)) {

            var targetGates = nodes[targetUid].gates ? nodes[targetUid].gateIndexes.length : 0;
            var targetSlots = nodes[targetUid].slots ? nodes[targetUid].slotIndexes.length : 0;
            var sourceSlots = sourceNode.slots ? sourceNode.slotIndexes.length : 0;

            var newlinks = [];

            switch (linkCreationStart[i].creationType) {
                case "lstmpor":
                    if (targetNode.type == "LSTM"){
                        newlinks.push(createLinkIfNotExists(sourceNode, "por", targetNode, "por", 1, 1));
                        newlinks.push(createLinkIfNotExists(sourceNode, "por", targetNode, "gin", 1, 1));
                        newlinks.push(createLinkIfNotExists(sourceNode, "por", targetNode, "gou", 1, 1));
                        newlinks.push(createLinkIfNotExists(sourceNode, "por", targetNode, "gfg", 1, 1));
                    }
                    break;
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
                        if(!(link.sourceNodeUid in nodes) || nodes[link.sourceNodeUid].parent != currentNodeSpace){
                            if(link.targetNodeUid in nodes) {
                                nodes[link.targetNodeUid].linksFromOutside.push(link.uid);
                            }
                            if(link.sourceNodeUid in nodes){
                                nodes[link.sourceNodeUid].linksToOutside.push(link.uid);
                            }
                        }
                        if(nodespaceProperties[currentNodeSpace].renderlinks == 'always'){
                            addLink(link);
                        }
                    });
                }
            });
        }
    }
    cancelLinkCreationHandler();
}

function createLinkIfNotExists(sourceNode, sourceGate, targetNode, targetSlot, weight){
    for(var uid in sourceNode.gates[sourceGate].outgoing){
        var link = sourceNode.gates[sourceGate].outgoing[uid];
        if(link.targetNodeUid == targetNode.uid && link.slotName == targetSlot){
            return false;
        }
    }
    var newlink = new Link('tmp', sourceNode.uid, sourceGate, targetNode.uid, targetSlot, weight || 1);
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

function moveNodesOnServer(position_data){
    api.call("set_node_positions", {
        nodenet_uid: currentNodenet,
        positions: position_data
    });
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
    var form = $(event.target);
    if(clickType == 'gate'){
        // click on gate in editor
        node = nodes[clickOriginUid];
        gate = node.gates[node.gateIndexes[clickIndex]];
    } else {
        // click on gate in sidebar
        node = nodes[form.attr('data-node')];
        gate = node.gates[form.attr('data-gate')];
    }
    if(gate.is_highdim) {
        return false;
    }
    var data = form.serializeArray();
    params = {
        nodenet_uid: currentNodenet,
        node_uid: node.uid,
        gate_type: gate.name,
        gatefunction: 'identity',
        gatefunction_parameters: {}
    }
    for(var i=0; i < data.length; i++){
        if(data[i].name == 'gate_gatefunction'){
            params.gatefunction = data[i].value;
        } else {
            params.gatefunction_parameters[data[i].name] = data[i].value
        }
    }
    api.call('set_gate_configuration', params, function(data){
        config = {
            'gatefunction': params.gatefunction,
            'gatefunction_parameters': params.gatefunction_parameters
        }
        node.gate_configuration[gate.name] = config;
        gate.gatefunction = params.gatefunction;
        gate.gatefunction_parameters = params.gatefunction_parameters;
        api.defaultSuccessCallback();
        redrawNode(node, true);
        view.draw();
    }, api.defaultErrorCallback);
}

function setNodeActivation(nodeUid, activation){
    activation = activation || 0;
    nodes[nodeUid].activation = activation;
    //TODO not sure this is generic enough, should probably just take the 0th
    if(nodes[nodeUid].gates["gen"]) {
        nodes[nodeUid].gates["gen"].activation = activation;
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
    }, api.defaultSuccessCallback, api.defaultErrorCallback);
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
    nodes[nodeUid].parameters['datasource'] = value;
    showNodeForm(nodeUid);
    api.call("bind_datasource_to_sensor", {
        nodenet_uid: currentNodenet,
        sensor_uid: nodeUid,
        datasource: value
    }, function(data){
        showNodeForm(nodeUid, true);
    });
}

function handleSelectDatatargetModal(event){
    var nodeUid = clickOriginUid;
    var value = $('#select_datatarget_modal select').val();
    $("#select_datatarget_modal").modal("hide");
    nodes[nodeUid].parameters['datatarget'] = value;
    showNodeForm(nodeUid);
    api.call("bind_datatarget_to_actuator", {
        nodenet_uid: currentNodenet,
        actuator_uid: nodeUid,
        datatarget: value
    }, function(data){
        showNodeForm(nodeUid, true);
    });
}

// handler for entering a nodespace
function handleEnterNodespace(nodespaceUid, callback) {
    if (nodespaceUid in nodespaces) {
        deselectAll();
        refreshNodespace(nodespaceUid, -1, callback);
    }
}

// handler for entering parent nodespace
function handleNodespaceUp() {
    deselectAll();
    if (nodespaces[currentNodeSpace].parent) { // not yet root nodespace
        refreshNodespace(nodespaces[currentNodeSpace].parent, -1);
    }
}

function handleEditNodenet(event){
    event.preventDefault();
    var form = $(event.target);
    var reload = false;
    var data = {
        "nodenet_uid": currentNodenet,
        "worldadapter_config": {}
    }
    var formvalues = form.serializeArray();

    for(var i = 0; i < formvalues.length; i++){
        var field = formvalues[i];
        if(field.name.substr(0, 11) == "nodenet_wa_"){
            data.worldadapter_config[field.name.substr(11)] = field.value;
        } else if(field.name.substr(0, 8) == "nodenet_") {
            data[field.name.substr(8)] = field.value;
        }
    }
    if(data.world != nodenet_data.world){
        if(typeof currentWorld != 'undefined' && (nodenet_data.world == currentWorld || data.world == currentWorld)){
            reload = true;
        }
    }
    nodenet_data.snap_to_grid = $('#ui_snap').attr('checked');
    $.cookie('snap_to_grid', nodenet_data.snap_to_grid || '', {path: '/', expires: 7})
    api.call("set_nodenet_properties", data,
        success=function(data){
            dialogs.notification('Nodenet data saved', 'success');
            if(reload){
                window.location.reload();
            } else {
                setCurrentNodenet(currentNodenet, currentNodeSpace, true);
                // refreshNodespace();
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
    properties = {};
    properties['renderlinks'] = $('#nodespace_renderlinks').val();
    properties['activation_display'] = $('#nodespace_activation_display').val();
    var update = false;
    for(var key in properties){
        if(properties[key] != nodespaceProperties[currentNodeSpace][key]){
            update = true;
            nodespaceProperties[currentNodeSpace][key] = properties[key];
        } else {
            delete properties[key];
        }
    }
    if(update){
        params = {nodenet_uid: currentNodenet, nodespace_uid: currentNodeSpace, properties: properties}
        api.call('set_nodespace_properties', params);
        if ('renderlinks' in properties){
            refreshNodespace();
        } else {
            redrawNodeNet();
        }
    }
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
        refreshNodespace(node.parent, -1, function(){
            deselectAll();
            canvas_container.scrollTop(y);
            canvas_container.scrollLeft(x);
            selectNode(node.uid);
            view.draw();
            if(node.uid in nodes && doShowNodeForm) {
                loadLinksForSelection(null, false, true);
            }
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
    $('#gate_gatefunction').on('change', updateGatefunctionParams);
    $('#edit_nodenet_form').submit(handleEditNodenet);
    $('#edit_nodespace_form').submit(handleEditNodespace);
    $('#edit_nodespace_form #delete_nodespace').on('click', deleteNodespace);
    $('#native_add_param').click(function(){
        $('#native_parameters').append('<tr><td><input name="param_name" type="text" class="inplace"/></td><td><input name="param_value" type="text"  class="inplace" /></td></tr>');
    });
    var world_selector = $("#nodenet_world_uid");
    var worldadapter_selector = $("#nodenet_worldadapter");
    var update_worldadapter_params = function(data){
        var html = [];
        var wa = worldadapters[worldadapter_selector.val()];
        if(!wa) return ;
        for(var i in wa.config_options){
            var op = wa.config_options[i]
            var param = '<tr><td><label for="nodenet_wa_'+op.name+'">'+op.name+'</td>';
            if(op.options){
                param += '<td><select name="nodenet_wa_'+op.name+'" id="nodenet_wa_'+op.name+'">';
                param += '<option>' + op.options.join("</option><option>") + '<option>';
                param += '</select></td>';
            } else {
                param += '<td><input type="text" name="nodenet_wa_'+op.name+'" id="nodenet_wa_'+op.name+'"></td>';
            }
            html.push(param +'</tr>')
        }
        $('#nodenet_editor .worldadapter_config').html('<table>' + html.join('') + '</table>');
        for(var i in wa.config_options){
            var op = wa.config_options[i];
            $('#nodenet_wa_' + op.name).val((wa.config && wa.config[op.name]) ? wa.config[op.name] : op.default);
        }
    };
    world_selector.on('change', function(){
        get_available_worldadapters(world_selector.val(), function(data){
            worldadapter_selector.val(nodenet_data.worldadapter);
            update_worldadapter_params(data);
        });
    });
    worldadapter_selector.on('change', function(){
        update_worldadapter_params();
    });
}

function showLinkForm(linkUid){
    $('#nodenet_forms .form-horizontal').hide();
    $('#edit_link_form').show();
    $('#link_weight_input').val(links[linkUid].weight);
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

function showNodeForm(nodeUid, refresh){
    if(refresh){
        api.call('get_node', {
            nodenet_uid:currentNodenet,
            node_uid: nodeUid
        }, function(data){
            item = new Node(nodeUid, data['position'][0], data['position'][1], data.parent_nodespace, data.name, data.type, data.activation, data.state, data.parameters, data.gate_activations, data.gate_configuration, data.is_highdimensional, data.inlinks, data.outlinks);
            redrawNode(item);
            nodes[nodeUid].update(item);
            if(clickType == 'gate'){
                showGateForm(nodes[nodeUid], nodes[nodeUid].gates[nodes[nodeUid].gateIndexes[clickIndex]]);
            } else {
                showNodeForm(nodeUid);
            }
        });
        return;
    }
    $('#nodenet_forms .form-horizontal').hide();
    var form = $('#edit_node_form');
    form.show();
    $('#node_name_input', form).val(nodes[nodeUid].name);
    $('#node_uid_input', form).val(nodeUid);
    $('#node_type_input', form).val(nodes[nodeUid].type);
    if(nodes[nodeUid].type == "Comment"){
        $('tr.comment', form).show();
        $('tr.node', form).hide();
        $('#node_comment_input').val(nodes[nodeUid].parameters.comment || '');
    } else {
        $('tr.node', form).show();
        $('tr.comment', form).hide();
        $('#node_activation_input').val(nodes[nodeUid].activation);
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
            if(nodes[nodeUid].inlinks > viewProperties.load_link_threshold){
                link_list += '<tr><td colspan="2">'+nodes[nodeUid].inlinks+' invisible links from outside nodespaces. <a href="#loadlinks" class="loadLinks">Load all links</a></td></tr>';
            } else if (nodes[nodeUid].inlinks > 0) {
                link_list += '<tr><td colspan="2">'+nodes[nodeUid].inlinks+' invisible links from outside nodespaces</td></tr>';
            }
            for(key in nodes[nodeUid].slots){
                link_list += "<tr><td>" + key + "</td><td><ul>";
                for(id in nodes[nodeUid].slots[key].incoming){
                    if(links[id].sourceNodeUid in nodes){
                        var n = nodes[links[id].sourceNodeUid];
                        var ns = '';
                        if(n.parent != currentNodeSpace){
                            ns = nodespaces[n.parent].name+"/";
                        }
                        link_list += '<li><a href="#followlink" data="'+id+'" class="followlink">&lt;-</a> &nbsp;<a href="#followNode" data="'+n.uid+'" class="follownode">'+ns+(n.name || n.uid.substr(0,8)+'&hellip;')+':'+links[id].gateName+'</a></li>';
                    }
                }
            }
        }
        $('#node_slots').html(link_list || "<tr><td>None</td></tr>");
        if(nodes[nodeUid].outlinks > viewProperties.load_link_threshold){
            content += '<tr><td colspan="2">'+nodes[nodeUid].outlinks+' invisible links to outside nodespaces. <a href="#loadlinks" class="loadLinks">Load all links</a></td></tr>';
        } else if(nodes[nodeUid].outlinks > 0){
            content += '<tr><td colspan="2">'+nodes[nodeUid].outlinks+' invisible links to outside nodespaces</td></tr>';
        }
        for(name in nodes[nodeUid].gates){
            link_list = "";
            for(id in nodes[nodeUid].gates[name].outgoing){
                if(links[id].targetNodeUid in nodes){
                    var n = nodes[links[id].targetNodeUid];
                    var ns = '';
                    if(n.parent != currentNodeSpace){
                        ns = nodespaces[n.parent].name+"/";
                    }
                    link_list += '<li><a href="#followlink" data="'+id+'" class="followlink">-&gt;</a> &nbsp;<a href="#followNode" data="'+n.uid+'" class="follownode">'+ns+(n.name || n.uid.substr(0,8)+'&hellip;')+'</a></li>';
                }
            }
            content += '<tr><td><a href="#followgate" class="followgate" data-node="'+nodeUid+'" data-gate="'+name+'">'+name+'</td>';
            if(link_list){
                content += "<td><ul>"+link_list+"<ul></td>";
            }
            content += "</tr>";
        }
        $('#node_gates').html(content || "<tr><td>None</td></tr>");
        $('a.loadLinks', form).on('click', function(evt){
            evt.preventDefault();
            loadLinksForSelection(null, true, true);
        });
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
        var sorted_parameters = parameters;
        if(!is_array) {
            sorted_parameters = [];
            for(var param in parameters) {
                sorted_parameters.push(param);
            }
        }
        sorted_parameters.sort();
        html = '';
        sorted_parameters.forEach(function(param) {
            input = '';
            var name = (is_array) ? parameters[param] : param;
            var value = (is_array) ? '' : parameters[param];
            var i;
            switch(name){
                case "datatarget":
                    var opts = get_datatarget_options(currentWorldadapter, value);
                    input = "<select name=\"datatarget\" class=\"inplace\" id=\"node_datatarget\">"+opts+"</select>";
                    break;
                case "datasource":
                    var opts = get_datasource_options(currentWorldadapter, value);
                    input = "<select name=\"datasource\" class=\"inplace\" id=\"node_datasource\">"+opts+"</select>";
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
        });
    }
    return html;
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
    $('#gate_gatefunction').val(gate.gatefunction);
    $.each($('input, select, textarea', form), function(index, el){
        el = $(el);
        if(el.attr('name') == 'activation'){
            el.val(gate.activation || '0');
        } else if(el.attr('name').substr(0, 23) == "gatefunction_parameter_"){
            if(gate.gatefunction_parameters){
                el.val(gate.gatefunction_parameters[el.attr('name').substr(23)]);
            }
        }
        if(gate.is_highdim){
            el.attr('disabled', 'disabled');
        } else if(el.attr('name') != 'activation'){
            el.removeAttr('disabled');
        }
    });
    if(gate.is_highdim){
        $('.highdim', form).text("This is a high-dimensional gate with " + nodetypes[node.type].dimensionality.gates[gate.name] + " dimensions").show();
    } else {
        $('.highdim', form).hide();
    }
    updateGatefunctionParams(gate);

    form.attr('data-node', node.uid);
    form.attr('data-gate', gate.name);
    form.show();
}

function updateGatefunctionParams(gate){
    if(!gate && clickType == 'gate'){
        node = nodes[clickOriginUid];
        gate = node.gates[node.gateIndexes[clickIndex]];
    } else if(!gate) {
        // click on gate in sidebar
        node = nodes[form.attr('data-node')];
        gate = node.gates[form.attr('data-gate')];
    }
    var selected_gatefunc = $('#gate_gatefunction').val();
    var container = $('#gatefunction_param_container');
    var html = '';
    foo = gate;
    for(var param in available_gatefunctions[selected_gatefunc]){
        var val = available_gatefunctions[selected_gatefunc][param];
        if(selected_gatefunc == gate.gatefunction && param in gate.gatefunction_parameters){
            val = gate.gatefunction_parameters[param]
        }
        html += '<tr>' +
            '<td><label for="gatefunction_param_'+param+'">'+param.charAt(0).toUpperCase()+param.slice(1)+'</label></td>'+
            '<td><input type="text" id="gatefunction_param_'+param+'" name="'+param+'" value="'+val+'" /></td>'+
            '</tr>';
    }
    container.html(html)
}

function updateNodespaceForm(){
    if(Object.keys(nodespaces).length){
        $('#nodespace_uid').val(currentNodeSpace);
        $('#nodespace_name').val(nodespaces[currentNodeSpace].name);
        if(nodespaces[currentNodeSpace].name == 'Root'){
            $('#nodespace_name').attr('disabled', 'disabled');
            $('#delete_nodespace').hide();
        } else {
            $('#nodespace_name').removeAttr('disabled');
            $('#delete_nodespace').show();
        }
        $('#nodespace_renderlinks').val(nodespaceProperties[currentNodeSpace].renderlinks);
        $('#nodespace_activation_display').val(nodespaceProperties[currentNodeSpace].activation_display);
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
        view.draw(true);
    }
}


/* todo:

 - get diffs
 - handle connection problems
 - multiple viewports
 - exporting and importing with own dialogs
 - edit native modules
 */
