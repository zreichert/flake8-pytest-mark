# -*- coding: utf-8 -*-

import ast
import re
from uuid import UUID


def rule_m5xx(node, rule_name, rule_conf, class_type):
    """Read and validate the input file contents.
    A 5XX rule checks for the presence of a configured 'pytest_mark'
    Marks may be numbered up to 50, example: 'pytest_mark49'

    Args:
        node (ast.AST): A node in the ast.
        rule_name (str): The name of the rule.
        rule_conf (dict): The dictionary containing the properties of the rule
        class_type (class): The class that this rule was called from

    Yields:
        tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
    """
    line_num = node.lineno
    code = ''.join([i for i in str(rule_name) if i.isdigit()])
    code = code.zfill(2)
    message = 'M5{} test definition not marked with {}'.format(code, rule_conf['name'])
    if not _reduce_decorators_by_mark(node.decorator_list, rule_conf['name']):
        yield (line_num, 0, message, class_type)


def rule_m6xx(node, rule_name, rule_conf, class_type):
    """Validate a value to a given mark against a provided regex
    A 6XX requires a configured 5XX rule
    A 6XX rule will not warn if a corresponding 5XX rule validates

    Args:
        node (ast.AST): A node in the ast.
        rule_name (str): The name of the rule.
        rule_conf (dict): The dictionary containing the properties of the rule
        class_type (class): The class that this rule was called from

    Yields:
        tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
    """
    configured = False
    non_matching_values = []
    detailed_error = None
    attempt_value_match = False
    line_num = node.lineno
    for decorator in _reduce_decorators_by_mark(node.decorator_list, rule_conf['name']):
        values = _get_decorator_args(decorator)
        if any(k in rule_conf for k in ('value_regex', 'value_match')):
            attempt_value_match = True

        if attempt_value_match:
            configured = True

            # iterate through values to test all for matching
            for value in values:
                if 'value_regex' in rule_conf:
                    if not re.match(rule_conf['value_regex'], value):
                        non_matching_values.append(value)
                        detailed_error = "Configured regex: '{}'".format(rule_conf['value_regex'])

                # only use match if regex is not supplied
                if 'value_match' in rule_conf and 'value_regex' not in rule_conf:
                    if rule_conf['value_match'] == 'uuid':
                        try:
                            UUID(value)
                        # excepting Exception intentionally here
                        # If UUID can't parse the value for any reason its not a valid uuid
                        except Exception as e:
                            non_matching_values.append(value)
                            detailed_error = e

    if configured and len(non_matching_values) > 0:
        code = ''.join([i for i in str(rule_name) if i.isdigit()])
        code = code.zfill(2)
        message = "M6{} the mark values '{}' do not match the configuration specified by {}, {}".format(code, non_matching_values, rule_name, detailed_error)   # noqa: E501
        yield (line_num, 0, message, class_type)


def rule_m7xx(node, rule_name, rule_conf, class_type):
    """Validate types of the objects passed as args to a configured mark
    All args must be strings

    Args:
        node (ast.AST): A node in the ast.
        rule_name (str): The name of the rule.
        rule_conf (dict): The dictionary containing the properties of the rule
        class_type (class): The class that this rule was called from

    Yields:
        tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
    """
    line_num = node.lineno
    code = ''.join([i for i in str(rule_name) if i.isdigit()])
    code = code.zfill(2)
    message = False
    for decorator in _reduce_decorators_by_mark(node.decorator_list, rule_conf['name']):
        if any(not isinstance(arg, ast.Str) for arg in decorator.args):
            message = 'M7{} mark values must be strings'.format(code)
    if message:
        yield (line_num, 0, message, class_type)


def rule_m8xx(node, rule_name, rule_conf, class_type):
    """Validates that @pytest.mark.foo() is only called once for a given test
    On by default, can be turned off with allow_duplicate=true

    Args:
        node (ast.AST): A node in the ast.
        rule_name (str): The name of the rule.
        rule_conf (dict): The dictionary containing the properties of the rule
        class_type (class): The class that this rule was called from

    Yields:
        tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
    """

    line_num = node.lineno
    code = ''.join([i for i in str(rule_name) if i.isdigit()])
    code = code.zfill(2)
    message = 'M8{} @pytest.mark.{} may only be called once for a given test'.format(code, rule_conf['name'])
    allow_duplicate = False
    if 'allow_duplicate' in rule_conf and rule_conf['allow_duplicate'].lower() == 'true':
        allow_duplicate = True
    if not allow_duplicate and len(_reduce_decorators_by_mark(node.decorator_list, rule_conf['name'])) > 1:
        yield (line_num, 0, message, class_type)


def rule_m9xx(node, rule_name, rule_conf, class_type):
    """Validates the number of arguments to @pytest.mark.foo()
    By default we validate that there is only one argument
    can configure to allow multiple with allow_multiple_args=true

    Args:
        node (ast.AST): A node in the ast.
        rule_name (str): The name of the rule.
        rule_conf (dict): The dictionary containing the properties of the rule
        class_type (class): The class that this rule was called from

    Yields:
        tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
    """
    line_num = node.lineno
    code = ''.join([i for i in str(rule_name) if i.isdigit()])
    code = code.zfill(2)
    allow_multiple_args = False
    if 'allow_multiple_args' in rule_conf and rule_conf['allow_multiple_args'].lower() == 'true':
        allow_multiple_args = True
    for decorator in _reduce_decorators_by_mark(node.decorator_list, rule_conf['name']):
        if not allow_multiple_args and len(decorator.args) > 1:
            message = 'M9{} you may only specify one argument to @pytest.mark.{}'.format(code, rule_conf['name'])
            yield (line_num, 0, message, class_type)


def _reduce_decorators_by_mark(decorators, mark):
    reduced = []
    for decorator in decorators:
        try:
            if decorator.func.attr == mark and decorator.func.value.value.id == 'pytest':
                reduced.append(decorator)
        except AttributeError:
            pass
    return reduced


def _get_decorator_args(decorator):
    args = []
    try:
        for arg in decorator.args:
            args.append(arg.s)
    except AttributeError:
        pass
    return args
