

def test_statuslogger_does_not_overwrite_children(runtime, test_nodenet):
    net = runtime.get_nodenet(test_nodenet)
    sl = net.netapi.statuslogger
    sl.info("Learning.Foo", sl.ACTIVE, progress=(5, 23))
    sl.info("Learning", sl.SUCCESS, "Learning complete")
    res, tree = runtime.get_status_tree(test_nodenet)
    assert tree['Learning']['level'] == "info"
    assert tree['Learning']['state'] == "success"
    assert tree['Learning']['msg'] == "Learning complete"
    assert tree['Learning']['children']['Foo']['level'] == "info"
    assert tree['Learning']['children']['Foo']['state'] == "active"
    sl.remove("Learning.Foo")
    res, tree = runtime.get_status_tree(test_nodenet)
    assert 'Foo' not in tree['Learning']['children']
