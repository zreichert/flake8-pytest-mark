# -*- coding: utf-8 -*-
import ast
import re
from flake8_pytest_mark.rules import rule_m5xx, rule_m6xx, rule_m7xx, rule_m8xx, rule_m9xx

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
                    if a[0] in ['name', 'value_match', 'value_regex', 'allow_duplicate', 'allow_multiple_args']:
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
        rule_funcs = (rules.rule_m5xx, rules.rule_m6xx, rules.rule_m7xx, rules.rule_m8xx, rules.rule_m9xx)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and re.match(r'^test_', node.name):
                for rule_func in rule_funcs:
                    for rule_name, configured_rule in self.pytest_marks.items():
                        for err in rule_func(node, rule_name, configured_rule, type(self)):
                            yield err

