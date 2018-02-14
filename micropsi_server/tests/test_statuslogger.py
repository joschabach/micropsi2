

def test_nodenet_statuslogger(app, runtime, test_nodenet):
    net = runtime.get_nodenet(test_nodenet)
    sl = net.netapi.statuslogger
    sl.info("Learning.Foo", sl.ACTIVE, progress=(5, 23))
    logs = runtime.get_logger_messages(sl.name)
    assert "Learning.Foo" in logs['logs'][1]['msg']
    result = app.get_json('/rpc/get_status_tree?nodenet_uid=%s' % test_nodenet)
    tree = result.json_body['data']
    assert tree['Learning']['level'] == "info"
    assert tree['Learning']['children']['Foo']['level'] == "info"
    assert tree['Learning']['children']['Foo']['state'] == sl.ACTIVE
    assert tree['Learning']['children']['Foo']['progress'] == [5, 23]
    result = app.get_json('/rpc/get_status_tree?nodenet_uid=%s&level=warning' % test_nodenet)
    tree = result.json_body['data']
    assert tree == {}
