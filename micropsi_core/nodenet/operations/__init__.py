

def selectioninfo(nodetypes=[], mincount=0, maxcount=-1):
    def _decorator(func):
        func.selectioninfo = {
            'nodetypes': nodetypes if type(nodetypes) == list else [nodetypes],
            'mincount': mincount,
            'maxcount': maxcount
        }
        return func
    return _decorator
