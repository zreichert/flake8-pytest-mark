# -*- coding: utf-8 -*-
import ast
import re
from flake8_pytest_mark import rules

__author__ = 'Zach Reichert'
__email__ = 'zach.reichert@rackspace.com'
__version__ = '0.1.1'


class MarkChecker(object):
    """
    Flake8 plugin to check the presence of test marks.
    """
    name = 'flake8-pytest-mark'
    version = __version__
    min_mark = 1
    max_mark = 50
    pytest_marks = dict.fromkeys(["pytest_mark{}".format(x) for x in range(min_mark, max_mark)], {})

    @classmethod
    def add_options(cls, parser):
        """Required by flake8
        add the possible options, called first

        parser (OptionsManager):
        """
        kwargs = {'action': 'store', 'default': '', 'parse_from_config': True,
                  'comma_separated_list': True}
        for num in range(cls.min_mark, cls.max_mark):
            parser.add_option(None, "--pytest-mark{}".format(num), **kwargs)

    @classmethod
    def parse_options(cls, options):
        """Required by flake8
        parse the options, called after add_options

        options (dict): options to be parsed
        """
        d = {}
        for pytest_mark, dictionary in cls.pytest_marks.items():
            # retrieve the marks from the passed options
            mark_data = getattr(options, pytest_mark)
            if len(mark_data) != 0:
                parsed_params = {}
                for single_line in mark_data:
                    a = [s.strip() for s in single_line.split('=')]
                    # whitelist the acceptable params
                    if a[0] in ['name', 'value_match', 'value_regex', 'allow_duplicate']:
                        parsed_params[a[0]] = a[1]
                d[pytest_mark] = parsed_params
        cls.pytest_marks.update(d)
        # delete any empty rules
        cls.pytest_marks = {x: y for x, y in cls.pytest_marks.items() if len(y) > 0}

    # noinspection PyUnusedLocal,PyUnusedLocal
    def __init__(self, tree, *args, **kwargs):
        """Required by flake8

        tree (ast.AST): an AST tree
        args:
        kwargs:
        """
        self.tree = tree

    def run(self):
        """Required by flake8
        will be called after add_options and parse_options

        Yields:
            tuple: (int, int, str, type) the tuple used by flake8 to construct a violation
        """
        if len(self.pytest_marks) == 0:
            message = "M401 no configuration found for {}, " \
                      "please provide configured marks in a flake8 config".format(self.name)
            yield (0, 0, message, type(self))
        rule_funcs = (rules.rule_m5xx, rules.rule_m6xx, rules.rule_m7xx, rules.rule_m8xx)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and re.match(r'^test_', node.name):
                for rule_func in rule_funcs:
                    for rule_name, configured_rule in self.pytest_marks.items():
                        for err in rule_func(node, rule_name, configured_rule, type(self)):
                            yield err
