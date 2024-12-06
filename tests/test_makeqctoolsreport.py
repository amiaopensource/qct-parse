import pytest
from qct_parse import makeqctoolsreport

def test_dependencies_found(monkeypatch):
    # Simulate finding application by monkeypatching the which() command with a
    # valid string
    monkeypatch.setattr(
        makeqctoolsreport.shutil,
        'which',
        lambda *path: path
    )
    assert makeqctoolsreport.dependencies() is None

def test_dependencies_not_found_calls_system_exit(monkeypatch):
    # Simulate not finding application
    monkeypatch.setattr(
        makeqctoolsreport.shutil,
        'which',
        lambda *path: None
    )

    with pytest.raises(SystemExit):
        makeqctoolsreport.dependencies()
