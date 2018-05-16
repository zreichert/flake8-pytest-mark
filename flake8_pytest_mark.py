# -*- coding: utf-8 -*-
import ast
import re
from uuid import UUID

__author__ = 'Zach Reichert'
__email__ = 'zach.reichert@rackspace.com'
__version__ = '0.1.1'


class MarkChecker(object):
    """
    Flake8 plugin to check the presence of test marks.
    """
    name = 'flake8-pytest-mark'
    version = __version__
    pytest_marks = dict.fromkeys(["pytest_mark{}".format(x) for x in range(1, 50)], {})

    @classmethod
    def add_options(cls, parser):
        kwargs = {'action': 'store', 'default': '', 'parse_from_config': True,
                  'comma_separated_list': True}
        for num in range(1, 50):
            parser.add_option(None, "--pytest-mark{}".format(num), **kwargs)

    @classmethod
    def parse_options(cls, options):
        d = {}
        for pytest_mark, dictionary in cls.pytest_marks.items():
            # retrieve the marks from the passed options
            mark_data = getattr(options, pytest_mark)
            if len(mark_data) != 0:
                parsed_params = {}
                for single_line in mark_data:
                    a = [s.strip() for s in single_line.split('=')]
                    # whitelist the acceptable params
                    if a[0] in ['name', 'value_match', 'value_regex']:
                        parsed_params[a[0]] = a[1]
                d[pytest_mark] = parsed_params
        cls.pytest_marks.update(d)
        # delete any empty rules
        cls.pytest_marks = {x: y for x, y in cls.pytest_marks.items() if len(y) > 0}

    # noinspection PyUnusedLocal,PyUnusedLocal
    def __init__(self, tree, *args, **kwargs):
        self.tree = tree

    def run(self):
        if len(self.pytest_marks) == 0:
            message = "M401 no configuration found for {}, please provide configured marks in a flake8 config".format(self.name)  # noqa: E501
            yield (0, 0, message, type(self))
        rule_funcs = (self.rule_m5xx, self.rule_m6xx, self.rule_m7xx)
        for node in ast.walk(self.tree):
            for rule_func in rule_funcs:
                for rule_name, configured_rule in self.pytest_marks.items():
                    for err in rule_func(node, rule_name, configured_rule):
                        yield err

    def rule_m5xx(self, node, rule_name, rule_conf):
        """Read and validate the input file contents.
        A 5XX rule checks for the presence of a configured 'pytest_mark'
        Marks may be numbered up to 50, example: 'pytest_mark49'

        Args:
            node (ast.AST): A node in the ast.
            rule_name (str): The name of the rule.
            rule_conf (dict): The dictionary containing the properties of the rule

        Yields:
            tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
        """
        if isinstance(node, ast.FunctionDef):
            marked = False
            line_num = node.lineno
            code = ''.join([i for i in str(rule_name) if i.isdigit()])
            code = code.zfill(2)
            message = 'M5{} test definition not marked with {}'.format(code, rule_conf['name'])
            if re.match(r'^test_', node.name):
                for decorator in node.decorator_list:
                    try:
                        mark_key = decorator.func.attr
                        decorator_type = decorator.func.value.value.id
                        if decorator_type == 'pytest' and mark_key == rule_conf['name']:
                            marked = True
                    except (AttributeError, IndexError, KeyError):
                        pass
                if not marked:
                    yield (line_num, 0, message, type(self))

    def rule_m6xx(self, node, rule_name, rule_conf):
        """Validate a value to a given mark against a provided regex
        A 6XX requires a configured 5XX rule
        A 6XX rule will not warn if a corresponding 5XX rule validates

        Args:
            node (ast.AST): A node in the ast.
            rule_name (str): The name of the rule.
            rule_conf (dict): The dictionary containing the properties of the rule

        Yields:
            tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
        """
        if isinstance(node, ast.FunctionDef):
            configured = False
            non_matching_values = []
            detailed_error = None
            attempt_value_match = False
            line_num = node.lineno
            if re.search(r'^test_', node.name):
                for decorator in node.decorator_list:
                    try:
                        values = [arg.s for arg in decorator.args]
                        mark_key = decorator.func.attr
                        decorator_type = decorator.func.value.value.id
                        if any(k in rule_conf for k in ('value_regex', 'value_match')):
                            attempt_value_match = True

                        # must be marked and configured to match in order to match the content :)
                        if all([decorator_type == 'pytest', mark_key == rule_conf['name'], attempt_value_match]):
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

                    # this except is intended to catch errors arising from marks that are incompatible with this tool
                    except (AttributeError, IndexError, KeyError):
                        pass

                if configured and len(non_matching_values) > 0:
                    code = ''.join([i for i in str(rule_name) if i.isdigit()])
                    code = code.zfill(2)
                    message = "M6{} the mark values '{}' do not match the configuration specified by {}, {}".format(code, non_matching_values, rule_name, detailed_error)   # noqa: E501
                    yield (line_num, 0, message, type(self))

    def rule_m7xx(self, node, rule_name, rule_conf):
        """Validate types of the objects passed as args to a configured mark
        All args must be strings

        Args:
            node (ast.AST): A node in the ast.
            rule_name (str): The name of the rule.
            rule_conf (dict): The dictionary containing the properties of the rule

        Yields:
            tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
        """
        if isinstance(node, ast.FunctionDef):
            line_num = node.lineno
            code = ''.join([i for i in str(rule_name) if i.isdigit()])
            code = code.zfill(2)
            message = False
            if re.match(r'^test_', node.name):
                for decorator in node.decorator_list:
                    try:
                        mark_key = decorator.func.attr
                        decorator_type = decorator.func.value.value.id
                        if decorator_type == 'pytest' and mark_key == rule_conf['name']:
                            if any(not isinstance(arg, ast.Str) for arg in decorator.args):
                                message = 'M7{} mark values must be strings'.format(code)
                    except (AttributeError, IndexError, KeyError):
                        pass
                if message:
                    yield (line_num, 0, message, type(self))
