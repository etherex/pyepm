from pyepm.utils import unhex

def test_unhex():
    assert unhex("0x") == 0
    assert unhex("0x0") == 0
    assert unhex("0xdeadbeef") == 3735928559
    assert unhex("deadbeef") == 3735928559
