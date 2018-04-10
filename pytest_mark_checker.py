# -*- encoding:utf-8 -*-

import ast
import flake8
import ast
import re

__author__ = 'Zach Reichert'
__email__ = 'zach.reichert@rackspace.com'
__version__ = '0.1.0'


class MarkChecker(object):
    """
    Flake8 plugin to check the presence of test marks.
    """
    name = 'pytest-mark-checker'
    version = __version__

    message_M501 = 'M501 test definition not marked with test_id'

    def __init__(self, tree, *args, **kwargs):
        self.tree = tree

    def run(self):
        rule_funcs = (self.rule_M501,)
        for node in ast.walk(self.tree):
            for rule_func in rule_funcs:
                for err in rule_func(node):
                    yield err

    def rule_M501(self, node):
        if isinstance(node, ast.FunctionDef):
            # TODO use ast.Nodetransformer to add a UUID tag
            # this should probably be done in a new subclass
            marked = False
            line_num = node.lineno
            name = node.name
            if re.search(r'^test', name):
                for decorator in node.decorator_list:
                    # I know this is ugly but it works for now
                    try:
                        value = decorator.args[0].s
                        mark_key = decorator.func.attr
                        decorator_type = decorator.func.value.value.id
                        if decorator_type == 'pytest' and mark_key == 'test_id':
                            marked = True
                    except AttributeError:
                        pass
                if not marked:
                    yield (line_num, 0, self.message_M501, type(self))

