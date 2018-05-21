# -*- coding: utf-8 -*-
import pytest

# args to only use checks that raise an 'M' prefixed error
extra_args = ['--select', 'M']

four_marks_config = """
[flake8]
pytest_mark1 = name=test_id
               regex=[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}
               autofix=uuid
pytest_mark2 = name=foo
pytest_mark3 = name=test_name
pytest_mark4 = name=bla_bla
"""


def test_some_tests_marked(flake8dir):
    flake8dir.make_setup_cfg(four_marks_config)
    flake8dir.make_example_py("""
@pytest.mark.test_id('b360c12d-0d47-4cfc-9f9e-5d86c315b1e4')
def test_1():
    pass

@pytest.mark.test_name('I am a test name')
def test_2():
    pass
""")
    result = flake8dir.run_flake8(extra_args)
    observed = result.out_lines
    expected = ['./example.py:1:1: M502 test definition not marked with foo',
                './example.py:1:1: M503 test definition not marked with test_name',
                './example.py:1:1: M504 test definition not marked with bla_bla',
                './example.py:5:1: M501 test definition not marked with test_id',
                './example.py:5:1: M502 test definition not marked with foo',
                './example.py:5:1: M504 test definition not marked with bla_bla']
    pytest.helpers.assert_lines(expected, observed)


def test_no_tests_marked(flake8dir):
    flake8dir.make_setup_cfg(four_marks_config)
    flake8dir.make_example_py("""
def test_happy_path():
    pass
""")
    result = flake8dir.run_flake8(extra_args)
    expected = ['./example.py:1:1: M503 test definition not marked with test_name',
                './example.py:1:1: M502 test definition not marked with foo',
                './example.py:1:1: M504 test definition not marked with bla_bla',
                './example.py:1:1: M501 test definition not marked with test_id']
    observed = result.out_lines
    pytest.helpers.assert_lines(expected, observed)


def test_asc_517(flake8dir):
    c = """
[flake8]
pytest_mark1 = name=test_id,value_match=uuid
pytest_mark2 = name=jira,value_regex=[a-zA-Z]+-\d+

"""
    flake8dir.make_setup_cfg(c)
    flake8dir.make_example_py("""
@pytest.mark.test_id('bogus')
@pytest.mark.jira('ASC-567')
def test_my_feature(host):
    pass
""")
    result = flake8dir.run_flake8(extra_args)
    assert result.out_lines == [u"./example.py:1:1: M601 the mark values '['bogus']' do not match the configuration specified by pytest_mark1, badly formed hexadecimal UUID string"]  # noqa


def test_asc_517_both_values_bad(flake8dir):
    c = """
[flake8]
pytest_mark1 = name=test_id,value_match=uuid
pytest_mark2 = name=jira,value_regex=[a-zA-Z]+-\d+

"""
    flake8dir.make_setup_cfg(c)
    flake8dir.make_example_py("""
@pytest.mark.test_id('bogus')
@pytest.mark.jira('jira-ticket')
def test_my_feature(host):
    pass
""")
    result = flake8dir.run_flake8(extra_args)
    observed = result.out_lines
    expected = ["./example.py:1:1: M601 the mark values '['bogus']' do not match the configuration specified by pytest_mark1, badly formed hexadecimal UUID string",  # noqa
                "./example.py:1:1: M602 the mark values '['jira-ticket']' do not match the configuration specified by pytest_mark2, Configured regex: '[a-zA-Z]+-\d+'"]  # noqa
    pytest.helpers.assert_lines(expected, observed)
