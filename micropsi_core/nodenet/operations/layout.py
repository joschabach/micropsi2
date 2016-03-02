
from micropsi_core.nodenet.operations import selectioninfo


@selectioninfo(mincount=2)
def autoalign(netapi, selection):
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
