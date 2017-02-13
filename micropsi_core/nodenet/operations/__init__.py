"""
Package for operations.

You can add files here, that define functions to operate on a selection of nodes or nodespaces
The filename will be used to group the operations by category.

To define an operation-function, choose a good function-name, and use the selectioninfo decorator to provide
meta-information about your operation:
* a list of nodetypes this operation can work with (or empty for all). defaults to empty
* a mincount to define the minimum amount of nodes needed for your operation. defaults to 0
* a maxcount to define the maximum amount of nodes you operation can work on, or -1 for no limit. defaults to -1

Setting a short docstring is encouraged, and will be used in the frontend to clarify what your operation does.

Operations can return a dict.
If a key "error" is set in the dict, the frontend assumes the whole operation failed.
Otherwise the result (if any) is displayed in the frontend.
To return images, that can be displayed in the frontend, base64 encode the images bytestring, and return it as data
together with a content-type: {'content_type': 'data:image/png;base64', 'data': image}

Operations that can have a mincount of one are assumed to be applicable to nodespaces, and listed in a context
menu without selection.
"""


def selectioninfo(nodetypes=[], mincount=0, maxcount=-1):
    def _decorator(func):
        if not hasattr(func, 'selectioninfo'):
            func.selectioninfo = []
        func.selectioninfo.append({
            'nodetypes': nodetypes if type(nodetypes) == list else [nodetypes],
            'mincount': mincount,
            'maxcount': maxcount
        })
        return func
    return _decorator
