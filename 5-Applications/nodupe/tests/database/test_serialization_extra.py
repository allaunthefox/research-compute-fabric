from nodupe.tools.databases.serialization import DatabaseSerialization


def test_serialize_deserialize_and_safe():
    ser = DatabaseSerialization(None)

    data = {"a": 1}
    s = ser.serialize(data)
    assert '"a"' in s

    # bytes input
    obj = ser.deserialize(b'{"x": 2}')
    assert obj == {"x": 2}

    # None should return None
    assert ser.deserialize(None) is None

    # invalid json raises ValueError
    try:
        ser.deserialize('not json')
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass

    # non-serializable returns '{}' via serialize_safe
    class X:
        pass

    assert ser.serialize_safe(X()) == '{}'
    assert ser.deserialize_safe('not json') == 'not json'
