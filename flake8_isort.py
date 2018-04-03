# -*- encoding:utf-8 -*-
import ast
from sys import stdin
import re

__author__ = 'Zach Reichert'
__email__ = 'zach.reichert@rackspace.com'
__version__ = '0.1.0'


class Flake8Isort(object):

    name = 'uuid_linter'
    version = '2.3'

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

        self.messages = {
            'U501': 'U501 Duplicate UUID found on test - test can only have one UUID mark',
            'U502': 'U502 Copied UUID found - remove copied UUID mark and re-run flake8',
            'U503': 'U503 Invalid UUID found - remove invalid UUID mark and re-run flake8',
            'U504': 'U504 test definition not marked with test_id'
        }

    def run(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # TODO use ast.Nodetransformer to add a UUID tag
                # this should probably be done in a new subclass
                marked = False
                line_num = node.lineno
                if re.search(r'^test_', node.name):
                    for decorator in node.decorator_list:
                        # I know this is ugly but it works for now
                        value = decorator.args[0].s
                        mark_key = decorator.func.attr
                        decorator_type = decorator.func.value.value.id
                        if decorator_type == 'pytest' and mark_key == 'test_id':
                            marked = True

                if not marked:
                    #print 'HELLO'
                    yield (line_num, 0, self.messages['U504'], NameError('HiThere'))

