
import io
import os
import theano

import numpy as np
import networkx as nx

from theano import tensor as T

from micropsi_core.tools import post_mortem, OrderedSet
from micropsi_core.nodenet.node import FlowNodetype
from micropsi_core.nodenet.flow_engine import FlowEngine
from micropsi_core.nodenet.theano_engine.theano_flowmodule import TheanoFlowModule
from micropsi_core.nodenet.theano_engine.theano_stepoperators import CalculateTheanoFlowmodules
from micropsi_core.nodenet.theano_engine.theano_definitions import get_numerical_node_type, create_tensor, node_from_id, get_string_node_type, nodespace_to_id


class TheanoFlowEngine(FlowEngine):

    @property
    def engine(self):
        return "theano_engine"

    @property
    def worldadapter_instance(self):
        return self._worldadapter_instance

    @worldadapter_instance.setter
    def worldadapter_instance(self, _worldadapter_instance):
        typechange = True
        if self._worldadapter_instance and self.worldadapter == _worldadapter_instance.__class__.__name__ and \
                _worldadapter_instance.device_map == self._worldadapter_instance.device_map:
            typechange = False
        super(TheanoFlowEngine, self.__class__).worldadapter_instance.fset(self, _worldadapter_instance)
        if typechange:
            flow_io_types = self.generate_worldadapter_flow_types(delete_existing=typechange)
            self.native_module_definitions.update(flow_io_types)
            for key in flow_io_types:
                self.native_modules[key] = FlowNodetype(nodenet=self, **flow_io_types[key])
            self.update_numeric_native_module_types()
            self.generate_worldadapter_flow_instances()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thetas = {}

    def initialize_stepoperators(self):
        super().initialize_stepoperators()
        self.stepoperators.append(CalculateTheanoFlowmodules(self))
        self.stepoperators.sort(key=lambda op: op.priority)

    def save(self, base_path=None, zipfile=None):
        super().save(base_path, zipfile)
        if base_path is None:
            base_path = self.persistency_path

        for node_uid in self.thetas:
            # save thetas
            data = {}
            filename = "%s_thetas.npz" % node_uid
            for idx, name in enumerate(self.thetas[node_uid]['names']):
                data[name] = self.thetas[node_uid]['variables'][idx].get_value()
            if zipfile:
                stream = io.BytesIO()
                np.savez(stream, **data)
                stream.seek(0)
                zipfile.writestr(filename, stream.getvalue())
            else:
                np.savez(os.path.join(base_path, filename), **data)

    def load(self):
        super().load()
        for node_uid in nx.topological_sort(self.flowgraph):
            if node_uid in self.flow_module_instances:
                theta_file = os.path.join(self.persistency_path, "%s_thetas.npz" % node_uid)
                if os.path.isfile(theta_file):
                    data = np.load(theta_file)
                    for key in data:
                        self.set_theta(node_uid, key, data[key])
                    data.close()

    def merge_data(self, nodenet_data, keep_uids=False, native_module_instances_only=False):
        invalid_nodes = super().merge_data(nodenet_data, keep_uids, native_module_instances_only)
        invalid_flow_nodes = {}
        if native_module_instances_only:
            for uid, data in nodenet_data.get('nodes').items():
                if data.get('flow_module'):
                    if self.native_module_definitions.get(data['type'], {}).get('flow_module'):
                        partition = self.get_partition(uid)
                        node = TheanoFlowModule(
                            self,
                            self.get_partition(uid),
                            data['parent_nodespace'],
                            data['uid'],
                            get_numerical_node_type(data['type'], nativemodules=self.native_modules),
                            parameters=data.get('parameters', {}),
                            inputmap=data.get('inputmap', {}),
                            outputmap=data.get('outputmap', {}),
                            is_copy_of=data.get('is_copy_of'))
                        for key in data.get('state', {}):
                            node.set_state(key, data['state'][key])
                        self.flow_module_instances[node.uid] = node
                        partition.native_module_instances[node.uid] = node
                    else:
                        invalid_flow_nodes[uid] = data
            for uid in invalid_flow_nodes:
                if invalid_flow_nodes[uid].get('flow_module'):
                    self._delete_flow_module(uid)
        return invalid_nodes

    def reload_native_modules(self, native_modules):
        old_instances = self.flow_module_instances.copy()
        instances_to_delete = {}
        instances_to_recreate = {}
        super().reload_native_modules(native_modules)

        for uid in old_instances:
            instance = old_instances[uid]
            if self.native_modules[instance.type].inputs != instance.inputs or self.native_modules[instance.type].outputs != instance.outputs:
                self.logger.warning("Inputs or Outputs of flow node type %s changed, recreating instance %s" %
                                (instance.type, uid))
                instances_to_recreate[uid] = instance.get_data(complete=True, include_links=False)
                continue
            if not isinstance(instance._nodetype, type(self.native_modules[instance.type])):
                self.logger.warning("Nature of nodetype changed for node %s. Deleting" % instance)
                instances_to_delete[uid] = instance
                continue

            parameters = instance.clone_parameters()
            state = instance.clone_state()
            position = instance.position
            name = instance.name
            partition = self.get_partition(uid)
            flowdata = instance.get_flow_data(complete=True)
            new_instance = TheanoFlowModule(
                self,
                partition,
                instance.parent_nodespace,
                uid,
                get_numerical_node_type(instance.type, self.native_modules),
                inputmap=flowdata['inputmap'],
                outputmap=flowdata['outputmap'],
                parameters=parameters
            )
            new_instance.position = position
            new_instance.name = name
            for key, value in parameters.items():
                try:
                    new_instance.set_parameter(key, value)
                except NameError:
                    pass  # parameter not defined anymore
            for key, value in state.items():
                new_instance.set_state(key, value)
            self.flow_module_instances[uid] = new_instance
            partition = self.get_partition(uid)
            partition.native_module_instances[uid] = new_instance

        for uid in instances_to_delete:
            self.delete_node(uid)
        for uid in instances_to_recreate:
            self.delete_node(uid)
            new_uid = self.create_node(
                instances_to_recreate[uid]['type'],
                instances_to_recreate[uid]['parent_nodespace'],
                instances_to_recreate[uid]['position'],
                name=instances_to_recreate[uid]['name'],
                uid=uid,
                parameters=instances_to_recreate[uid]['parameters'])

        for new_uid in nx.topological_sort(self.flowgraph):
            self.get_node(new_uid).ensure_initialized()

        self.verify_flow_consistency()
        self.update_flow_graphs()

    def _create_node_proxy(self, partition, uid):
        id = node_from_id(uid)
        parent_id = partition.allocated_node_parents[id]
        nodetype = get_string_node_type(partition.allocated_nodes[id], self.native_modules)
        if type(self.get_nodetype(nodetype)) == FlowNodetype:
            node = TheanoFlowModule(self, partition, nodespace_to_id(parent_id, partition.pid), uid, partition.allocated_nodes[id])
            self.flow_module_instances[uid] = node
            partition = self.get_partition(uid)
            partition.native_module_instances[uid] = node
            self.proxycache[node.uid] = node
            return node
        else:
            return super()._create_node_proxy(partition, uid)

    def construct_native_modules_and_comments_dict(self):
        data = super().construct_native_modules_and_comments_dict()
        for node_uid in self.flow_module_instances:
            data[node_uid].update(self.flow_module_instances[node_uid].get_flow_data())
        return data

    def update_flow_graphs(self, node_uids=None):
        if self.is_flowbuilder_active:
            return
        self.flowfunctions = []
        startpoints = []
        endpoints = []
        pythonnodes = set()

        toposort = nx.topological_sort(self.flowgraph)
        self.flow_toposort = toposort
        for uid in toposort:
            node = self.flow_module_instances.get(uid)
            if node is not None:
                if node.implementation == 'python':
                    pythonnodes.add(uid)
                if node.is_input_node():
                    startpoints.append(uid)
                if node.is_output_node():
                    endpoints.append(uid)

        graphs = []
        for enduid in endpoints:
            ancestors = nx.ancestors(self.flowgraph, enduid)
            node = self.flow_module_instances[enduid]
            if ancestors or node.inputs == []:
                path = [uid for uid in toposort if uid in ancestors] + [enduid]
                if path:
                    graphs.append(path)

        # worldadapter_names = []
        # if self.worldadapter_instance is not None:
        #     worldadapter_names += self.worldadapter_instance.get_available_flow_datasources() + self.worldadapter_instance.get_available_flow_datatargets()

        flowfunctions = {}
        floworder = OrderedSet()
        for idx, graph in enumerate(graphs):
            # split graph in parts:
            # node_uids = [uid for uid in graph if uid not in worldadapter_names]
            node_uids = [uid for uid in graph]
            nodes = [self.get_node(uid) for uid in node_uids]
            paths = self.split_flow_graph_into_implementation_paths(nodes)
            for p in paths:
                floworder.add(p['hash'])
                if p['hash'] not in flowfunctions:
                    func, dang_in, dang_out = self.compile_flow_subgraph([n.uid for n in p['members']], use_unique_input_names=True)
                    if func:
                        flowfunctions[p['hash']] = {'callable': func, 'members': p['members'], 'endnodes': set([nodes[-1]]), 'inputs': dang_in, 'outputs': dang_out}
                else:
                    flowfunctions[p['hash']]['endnodes'].add(nodes[-1])
        for funcid in floworder:
            self.flowfunctions.append(flowfunctions[funcid])

        self.logger.debug("Compiled %d flowfunctions" % len(self.flowfunctions))

    def compile_flow_subgraph(self, node_uids, requested_outputs=None, use_different_thetas=False, use_unique_input_names=False):
        """ Compile and return one callable for the given flow_module_uids.
        If use_different_thetas is True, the callable expects an argument names "thetas".
        Thetas are expected to be sorted in the same way collect_thetas() would return them.

        Parameters
        ----------
        node_uids : list
            the uids of the members of this graph

        requested_outputs : list, optional
            list of tuples (node_uid, out_name) to filter the callable's return-values. defaults to None, returning all outputs

        use_different_thetas : boolean, optional
            if true, return a callable that expects a parameter "thetas" that will be used instead of existing thetas. defaults to False

        use_unique_input_names : boolen, optional
            if true, the returned callable expects input-kwargs to be prefixe by node_uid: "UID_NAME". defaults to False, using only the name of the input

        Returns
        -------
        callable : function
            the compiled function for this subgraph

        dangling_inputs : list
            list of tuples (node_uid, input) that the callable expectes as inputs

        dangling_outputs : list
            list of tuples (node_uid, input) that the callable will return as output

        """
        subgraph = [self.get_node(uid) for uid in self.flow_toposort if uid in node_uids]

        # split the nodes into symbolic/non-symbolic paths
        paths = self.split_flow_graph_into_implementation_paths(subgraph)

        dangling_inputs = []
        dangling_outputs = []

        thunks = []

        for path_idx, path in enumerate(paths):
            thunk = {
                'implementation': path['implementation'],
                'function': None,
                'node': None,
                'outputs': [],
                'input_sources': [],
                'dangling_outputs': [],
                'list_outputs': [],
                'members': path['members']
            }
            member_uids = [n.uid for n in path['members']]
            outexpressions = {}
            inputs = []
            outputs = []
            skip = False

            # index for outputs of this thunk, considering unpacked list outputs
            thunk_flattened_output_index = 0

            for node in path['members']:
                buildargs = []
                # collect the inputs for this Flowmodule:
                for in_idx, in_name in enumerate(node.inputs):
                    if not node.inputmap[in_name] or node.inputmap[in_name][0] not in member_uids:
                        # this input is not satisfied from within this path
                        in_expr = create_tensor(node.definition['inputdims'][in_idx], T.config.floatX, name="%s_%s" % (node.uid, in_name))
                        inputs.append(in_expr)
                        if not node.inputmap[in_name] or node.inputmap[in_name][0] not in node_uids:
                            # it's not even satisfied by another path within the subgraph,
                            # and needs to be provided as input to the emerging callable
                            if use_unique_input_names:
                                thunk['input_sources'].append(('kwargs', -1, "%s_%s" % (node.uid, in_name)))
                            else:
                                thunk['input_sources'].append(('kwargs', -1, in_name))
                            dangling_inputs.append((node.uid, in_name))
                        else:
                            # this input will be satisfied by another path within the subgraph
                            source_uid, source_name = node.inputmap[in_name]
                            for idx, p in enumerate(paths):
                                if self.get_node(source_uid) in p['members']:
                                    # record which thunk, and which index of its output-array satisfies this input
                                    thunk['input_sources'].append(('path', idx, thunks[idx]['outputs'].index((source_uid, source_name))))
                        buildargs.append(in_expr)
                    else:
                        # this input is satisfied within this path
                        source_uid, source_name = node.inputmap[in_name]
                        buildargs.append(outexpressions[source_uid][self.get_node(source_uid).outputs.index(source_name)])

                # build the outexpression
                try:
                    if len(node.outputs) <= 1:
                        original_outex = [node.build(*buildargs)]
                    elif node.implementation == 'python':
                        func = node.build(*buildargs)
                        original_outex = [func] * len(node.outputs)
                    else:
                        original_outex = node.build(*buildargs)
                except Exception as err:
                    import traceback as tb
                    frame = [f[0] for f in tb.walk_tb(err.__traceback__) if f[0].f_code.co_filename == node.definition.get('path', '')]
                    lineno = "<unknown>" if len(frame) == 0 else str(frame[0].f_lineno)
                    self.logger.error("Error in Flowmodule %s at line %s:  %s: %s" % (str(node), lineno, err.__class__.__name__, str(err)))
                    post_mortem()
                    skip = True
                    break

                outexpressions[node.uid] = original_outex
                flattened_outex = []
                outputlengths = []
                flattened_markers = []
                # check if this node has a list as one of its return values:
                for idx, ex in enumerate(original_outex):
                    if type(ex) == list:
                        # if so, flatten the outputs, and mark the offset and length of the flattened output
                        # so that we can later reconstruct the nested output-structure
                        flattened_markers.append((len(outputs) + idx, len(ex)))
                        outputlengths.append(len(ex))
                        for item in ex:
                            flattened_outex.append(item)
                    else:
                        flattened_outex.append(ex)
                        outputlengths.append(1)

                # offset for indexing the flattened_outexpression by output_index
                node_flattened_output_offset = 0

                # go thorugh the nodes outputs, and see how they will be used:
                for out_idx, out_name in enumerate(node.outputs):
                    dangling = ['external']
                    if node.outputmap[out_name]:
                        # if this output is used, we have to see where every connection goes
                        # iterate through every connection, and note if it's used path-internally,
                        # subgraph-internally, or will produce an output of the emerging callable
                        dangling = []
                        for pair in node.outputmap[out_name]:
                            if pair[0] in member_uids:
                                # path-internally satisfied
                                dangling.append(False)
                            elif pair[0] in node_uids:
                                # internal dangling aka subgraph-internally satisfied
                                dangling.append("internal")
                            else:
                                # externally dangling aka this will be a final output
                                dangling.append("external")
                    # now, handle internally or externally dangling outputs if there are any:
                    if set(dangling) != {False}:
                        thunk['outputs'].append((node.uid, out_name))
                        if outputlengths[out_idx] > 1:
                            # if this is output should produce a list, note this, for later de-flattenation
                            # and append the flattened output to the output-collection
                            thunk['list_outputs'].append((thunk_flattened_output_index, outputlengths[out_idx]))
                            for i in range(outputlengths[out_idx]):
                                outputs.append(flattened_outex[out_idx + node_flattened_output_offset + i])
                            node_flattened_output_offset += outputlengths[out_idx] - 1
                        else:
                            outputs.append(flattened_outex[out_idx + node_flattened_output_offset])
                        if "external" in dangling:
                            # this output will be a final one:
                            if requested_outputs is None or (node.uid, out_name) in requested_outputs:
                                dangling_outputs.append((node.uid, out_name))
                                thunk['dangling_outputs'].append(thunk_flattened_output_index)
                        thunk_flattened_output_index += outputlengths[out_idx]

            if skip:
                # thunk borked, skip
                continue

            # now, set the function of this thunk. Either compile a theano function
            # or assign the python function.
            if not use_different_thetas:
                if thunk['implementation'] == 'theano':
                    thunk['function'] = theano.function(inputs=inputs, outputs=outputs)
                else:
                    thunk['node'] = path['members'][0]
                    thunk['function'] = outexpressions[thunk['node'].uid][0]

            else:
                sharedvars = self.collect_thetas(node_uids)
                dummies = [create_tensor(var.ndim, T.config.floatX, name="Theta_%s" % var.name) for var in sharedvars]
                if thunk['implementation'] == 'theano':
                    givens = list(zip(sharedvars, dummies))
                    thunk['function'] = theano.function(inputs=inputs + dummies, outputs=outputs, givens=givens)
                else:
                    thunk['node'] = path['members'][0]
                    thunk['function'] = outexpressions[thunk['node'].uid][0]

            thunks.append(thunk)

        if not use_unique_input_names:
            # check for name collisions
            for thunk in thunks:
                if len(set(thunk['input_sources'])) != (len(thunk['input_sources'])):
                    raise RuntimeError("""
                        Name Collision in inputs detected!
                        This graph can only be compiled as callable if you use unique_input_names.
                        set use_unique_input_names to True, and give the inputs as "UID_NAME"
                        where uid is the uid of the node getting this input, and name is the input name of this node""")

        def compiled(thetas=None, **kwargs):
            """ Compiled callable for this subgraph """
            all_outputs = []  # outputs for use within this thunk
            final_outputs = []  # final, external dangling outputs
            for idx, thunk in enumerate(thunks):
                funcargs = []
                # get the inputs: Either from the kwargs, or from the already existing outputs
                for source, pidx, item in thunk['input_sources']:
                    if source == 'kwargs':
                        funcargs.append(kwargs[item])
                    elif source == 'path':
                        funcargs.append(all_outputs[pidx][item])
                if thunk['implementation'] == 'python':
                    params = thunk['node'].clone_parameters()
                    out = thunk['function'](*funcargs, netapi=self.netapi, node=thunk['node'], parameters=params)
                    if len(thunk['node'].outputs) <= 1:
                        out = [out]
                    else:
                        if type(out) != tuple:
                            raise RuntimeError("""Output mismatch!
                                Node %s returned only one output instead of %d.""" % (str(thunk['node']), len(thunk['node'].outputs)))
                        elif len(out) != len(thunk['node'].outputs):
                            raise RuntimeError("""Output mismatch!
                                Node %s returned %d outputs instead of %d.""" % (str(thunk['node']), len(out), len(thunk['node'].outputs)))
                else:
                    if thetas:
                        funcargs += thetas
                    out = thunk['function'](*funcargs)
                if thunk['list_outputs']:
                    # if we have list_outputs, we need to nest the output of this thunk again
                    # to recreate the nested structure from a flat list of outputs
                    new_out = []
                    out_iter = iter(out)
                    try:
                        for out_index in range(len(out)):
                            for offset, length in thunk['list_outputs']:
                                if offset == out_index:
                                    sublist = []
                                    for i in range(length):
                                        sublist.append(next(out_iter))
                                    new_out.append(sublist)
                                else:
                                    new_out.append(next(out_iter))
                    except StopIteration:
                        # iterator finished, we handled all items.
                        pass
                    out = new_out
                if out:
                    all_outputs.append(out)
                    for idx in thunk['dangling_outputs']:
                        if requested_outputs is None or thunk['outputs'][idx] in requested_outputs:
                            final_outputs.append(out[idx])
            return final_outputs

        compiled.__doc__ = """Compiled subgraph of nodes %s
            Inputs: %s
            Outputs: %s
        """ % (str(subgraph), str([("%s of %s" % x[::-1]) for x in dangling_inputs]), str([("%s of %s" % x[::-1]) for x in dangling_outputs]))

        return compiled, dangling_inputs, dangling_outputs

    def shadow_flowgraph(self, flow_modules):
        """ Creates shallow copies of the given flow_modules, copying instances and internal connections.
        Shallow copies will always have the parameters and shared variables of their originals
        """
        copies = []
        copymap = {}
        for node in flow_modules:
            copy_uid = self.create_node(
                node.type,
                node.parent_nodespace,
                node.position,
                name=node.name,
                parameters=node.clone_parameters())
            copy = self.get_node(copy_uid)
            copy.is_copy_of = node.uid
            copymap[node.uid] = copy
            copies.append(copy)
        for node in flow_modules:
            for in_name in node.inputmap:
                if node.inputmap[in_name]:
                    source_uid, source_name = node.inputmap[in_name]
                    if source_uid in copymap:
                        self.flow(copymap[source_uid].uid, source_name, copymap[node.uid].uid, in_name)
        return copies

    def set_theta(self, node_uid, name, val):
        if node_uid not in self.thetas:
            self.thetas[node_uid] = {
                'names': [],
                'variables': []
            }
        if name not in self.thetas[node_uid]['names']:
            new_names = sorted(self.thetas[node_uid]['names'] + [name])
            self.thetas[node_uid]['names'] = new_names
            index = self.thetas[node_uid]['names'].index(name)
            if not isinstance(val, theano.compile.sharedvalue.SharedVariable):
                val = theano.shared(value=val.astype(T.config.floatX), name=name, borrow=True)
            self.thetas[node_uid]['variables'].insert(index, val)
        else:
            if not isinstance(val, theano.compile.sharedvalue.SharedVariable):
                val = theano.shared(value=val.astype(T.config.floatX), name=name, borrow=True)
            index = self.thetas[node_uid]['names'].index(name)
            self.thetas[node_uid]['variables'][index].set_value(val.get_value(), borrow=True)

    def get_theta(self, node_uid, name):
        data = self.thetas[node_uid]
        index = data['names'].index(name)
        return data['variables'][index]

    def collect_thetas(self, node_uids):
        shared_vars = []
        for uid in node_uids:
            node = self.get_node(uid)
            if node.is_copy_of:
                uid = node.is_copy_of
            data = self.thetas.get(uid)
            if data:
                shared_vars.extend(data['variables'])
        return shared_vars
