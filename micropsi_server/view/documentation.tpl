%include menu.tpl version = version

<div class="row-fluid">
    <h3>This is the psi cortex user api.</h3>

    <div class="row-fluid">
        <p>
            <h4>Documentation</h4>
        </p>
        <p>
            The API methods can be reached under
            <code>/rpc/METHOD_NAME(param1=foo,param2=bar)</code>
        </p>
        <p>
            The following methods are available:
            <ul>

<li><code>def get_available_blueprints(user, owner = None):</code>
    <pre class="description">Returns a dict of uids: names of available (running and stored) blueprints.
    Arguments:
        owner (optional): when submitted, the list is filtered by this owner

    </pre></li>
<li><code>new_blueprint(user, blueprint_name, blueprint_type, owner = "", domain_uid = None)</code>
    <pre class="description">Creates a new node net and registers it.
    
    Arguments:
        blueprint_type: the type of the domain adapter supported by this blueprint. Also used to determine the set of
            gate types supported for directional activation spreading of this blueprint, and the initial node types
        owner (optional): the creator of this blueprint
        domain_id (optional): if submitted, attempts to bind the blueprint to this domain

    Returns
        blueprint_uid if successful,
        None if failure
    
    </pre></li>

<li><code>delete_blueprint(user, blueprint_uid)</code>
    <pre class="description">Unloads the given blueprint from memory and deletes it from the storage.

    Simple unloading is maintained automatically when an blueprint is suspended and another one is accessed.
    </pre></li>
<li><code>set_blueprint_data(user, blueprint_uid, blueprint_name = None, blueprint_type = None, domain_uid = None, owner = None)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>revert_blueprint(user, blueprint_uid)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>save_blueprint(user, blueprint_uid)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>export_blueprint(user, blueprint_uid)</code>
    <pre class="description">Exports the blueprint, so it can be viewed and mailed etc.

    Returns a file that contains the blueprint in a suitable format.
    </pre>

<li><code>merge_blueprint(user, blueprint1_uid, blueprint2_uid)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>get_blueprint_suggesation(user, searchphrase)</code>
    <pre class="description">Returns a suggested blueprint/stencil with a max depth of 3 for the given searchphrase</pre></li>

<li><code>get_suggestions(user, blueprint_uid, nodes = None, searchphrase = "", depth = 1)</code>
    <pre class="description">Amend the given blueprint with suggested blueprint fragments.
    
    Arguments:
        blueprint_uid: the current blueprint
        nodes (optional): the points where the blueprint should be extended by suggestions
        searchphrase (optional): a search string or a space separated list of keywords that are used for the
            suggestions
        depth (optional): a parameter that specifies the level of detail
    
    </pre></li>

<li><code>fold_blueprint(user, blueprint_uid, nodes = None)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>expand_blueprint(user, blueprint_uid, nodes = None, depth = 1)</code>
    <pre class="description">Expand a set of nodes.

    Arguments:
        blueprint_uid: current blueprint
        nodes (optional): the points where the blueprint should be expanded
        depth (optional): the level of detail
    
    </pre></li>

<li><code>get_blueprint(user, blueprint_uid, state = -1)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>get_node(user, blueprint_uid, node_uid)</code>
    <pre class="description">Returns a dictionary with all node parameters, if node exists, or None if it does not. The dict is
    structured as follows:
    
        {
            uid: unique identifier,
            name (optional): display name,
            type: node type,
            screenposition (optional): a value to determine its position in the UI
            activation: activation value, defining the main state of the node,
            symbol (optional): a short string for compact display purposes,
            slots (optional): a list of lists [slot_type, {activation: activation_value,
                                                           links (optional): [link_uids]} (optional)]
            gates (optional): a list of lists [gate_type, {activation: activation_value,
                                                           links (optional): [link_uids]} (optional)]
            parameters (optional): a dict of arbitrary parameters that can make nodes stateful
        }
    
     </pre></li>

<li><code>add_node(user, blueprint_uid, type, screenposition = None, uid = None, name = "", parameters = None)</code>
    <pre class="description">Creates a new node. (Including nodespace, native module.)
    
    Arguments:
        blueprint_uid: uid of the nodespace manager
        type: type of the node
        x, y (optional): position of the node in the current nodespace
        nodespace: uid of the nodespace
        uid (optional): if not supplied, a uid will be generated
        name (optional): if not supplied, the uid will be used instead of a display name
        parameters (optional): a dict of arbitrary parameters that can make nodes stateful

    Returns:
        node_uid if successful,
        None if failure.
    
    </pre></li>

<li><code>set_node_position(user, blueprint_uid, node_uid, screenposition)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>set_node_name(user, blueprint_uid, node_uid, name)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>delete_node(user, blueprint_uid, node_uid)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>get_available_node_types(user, blueprint_uid = None)</code>
    <pre class="description">Returns an ordered list of node types available.
    If an blueprint uid is supplied, filter for node types allowed within this blueprint.</pre></li>

<li><code>set_node_parameters(user, blueprint_uid, node_uid, parameters = None)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>set_gate_parameters(user, blueprint_uid, node_uid, gate_type, parameters = None)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>get_available_datasources(user, blueprint_uid)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>get_available_datatargets(user, blueprint_uid)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>bind_datasource_to_node(user, blueprint_uid, sensor_uid, datasource)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>bind_datatarget_to_node(user, blueprint_uid, actor_uid, datatarget)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>add_link(user, blueprint_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty = 1, uid = None)</code>
    <pre class="description">Creates a new link.
    
    Arguments.
        source_node_uid: uid of the origin node
        gate_type: type of the origin gate (usually defines the link type)
        target_node_uid: uid of the target node
        slot_type: type of the target slot
        weight: the weight of the link (a float)
        certainty (optional): a probabilistic parameter for the link
        uid (option): if none is supplied, a uid will be generated

    Returns:
        link_uid if successful,
        None if failure
    
    </pre></li>

<li><code>set_link_weight(user, blueprint_uid, link_uid, weight, certainty = 1)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>get_link(user, blueprint_uid, link_uid)</code>
    <pre class="description">Returns a dictionary of the parameters of the given link, or None if it does not exist. It is
    structured as follows:
        
        {
            uid: unique identifier,
            source_node_uid: uid of source node,
            gate_type: type of source gate (amounts to link type),
            target_node_uid: uid of target node,
            gate_type: type of target gate,
            weight: weight of the link (float value),
            certainty: probabilistic weight of the link (float value),
        }
        
    </pre></li>

<li><code>delete_link(user, blueprint_uid, link_uid)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>

<li><code>get_domain_view(user, domain_uid, state = -1)</code>
    <pre class="description">Returns the current state of the domain for UI purposes, if current state is newer than the supplied one.</pre></li>


            </ul>
        </p>
    </div>
    <!--
    <div class="row-fluid">
        <a class="btn btn-small" href="/">Back</a>
    </div>
    -->
</div>


%rebase boilerplate title = "Documentation"
