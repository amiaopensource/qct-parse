from qct_parse import qct_parse

def test_dts2ts():
    assert qct_parse.dts2ts("0.0330000") == '00:00:00.0330'
