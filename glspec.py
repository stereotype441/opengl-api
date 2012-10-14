# This script outputs the following JSON information:
#
# 'functions': function_name -> {
#     'return': RETURN_TYPE,
#     'params': [{ 'name' -> PARAM_NAME, 'type' -> PARAM_TYPE }]
# }

import json
import os.path
import re
import sys

INITIAL_DECLARATION_REGEXP = re.compile('^[a-z-]+:')
SIGNATURE_REGEXP = re.compile(
    r'^(?P<name>[A-Za-z0-9_]+)\((?P<params>[A-Za-z0-9_, ]*)\)$')


FUNCTIONS = {}


def filter_out_comments(lines):
    for line in lines:
        # As of 10/13/2012, gl.spec contains a stray '[' at the
        # beginning of a comment line.  Filter that out.
        if line.startswith('[#'):
            continue
        comment_start = line.find('#')
        if comment_start != -1:
            line = line[:comment_start]
        line = line.rstrip()
        if line != '':
            yield line


def group_functions(lines):
    """Yield lists of lines, where each list constitutes a single
    function declaration.
    """
    current_function = []
    for line in filter_out_comments(lines):
        if INITIAL_DECLARATION_REGEXP.match(line):
            continue
        if not line[0].isspace() and current_function:
            yield current_function
            current_function = []
        current_function.append(line)
    if current_function:
        yield current_function


def process_glspec(f):
    for func in group_functions(f):
        name, param_names = parse_signature(func[0])
        if name in FUNCTIONS:
            raise Exception('Function {0} seen twice'.format(name))
        param_types = [None for p in param_names]
        return_type = None
        for line in func[1:]:
            key_value = line.lstrip().split(None, 1)
            if len(key_value) == 1:
                key = key_value[0]
                value = ''
            else:
                key, value = key_value
            if key == 'return':
                return_type = value
            elif key == 'param':
                param_name, param_type = value.split(None, 1)
                i = param_names.index(param_name)
                param_types[i] = param_type
        assert all(param_types)
        params = [{'name': name, 'type': type}
                  for name, type in zip(param_names, param_types)]
        FUNCTIONS[name] = {'return': return_type, 'params': params}


def parse_signature(sig):
    m = SIGNATURE_REGEXP.match(sig)
    name = m.group('name')
    params = m.group('params')
    if params:
        param_names = [p.strip() for p in m.group('params').split(',')]
    else:
        param_names = []
    return name, param_names


def main():
    spec_dir = '/home/pberry/opengl-docs/www.opengl.org/registry/api/'
    glspec_file = os.path.join(spec_dir, 'gl.spec')
    with open(glspec_file, 'r') as f:
        process_glspec(f)
    json_data = {'functions': FUNCTIONS}
    json.dump(json_data, sys.stdout)


main()
