
from micropsi_core.nodenet.operations import selectioninfo


@selectioninfo(mincount=1, nodetypes=['Nodespace'])
@selectioninfo(mincount=2)
def autoalign(netapi, selection):
    """ Autoalign nodes or nodespaces."""
    if len(selection) == 1:
        # if there's only one item selected, we assume it's a nodespace
        # so we align its contents. If it's not, we return an error
        try:
            nodespace = netapi.get_nodespace(selection[0])
        except:
            return {'error': 'nothing to align'}
        netapi.autoalign_nodespace(nodespace.uid)
    else:
        # otherwise, we retrieve the parent nodespace from the first selected
        # entity, and autoalign the selected nodes in the given nodespace
        nodespace = None
        if len(selection):
            try:
                nodespace = netapi.get_node(selection[0]).parent_nodespace
            except:
                pass
                try:
                    nodespace = netapi.get_nodespace(selection[0]).parent_nodespace
                except:
                    pass
            if nodespace is None:
                return {'error': 'unknown entity in selection'}
            netapi.autoalign_entities(nodespace, selection)
