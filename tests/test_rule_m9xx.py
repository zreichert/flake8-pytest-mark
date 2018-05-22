# -*- coding: utf-8 -*-

# args to only use checks that raise an 'M' prefixed error
extra_args = ['--select', 'M']

config = """
[flake8]
pytest_mark1 = name=test_id,

"""


def test_with_duplicate_marks(flake8dir):
    flake8dir.make_setup_cfg(config)
    flake8dir.make_example_py("""
@pytest.mark.test_id('too', 'many', 'args')
def test_happy_path():
    pass
    """)
    result = flake8dir.run_flake8(extra_args)
    assert result.out_lines == [u'./example.py:1:1: M901 you may only specify one argument to @pytest.mark.test_id']

