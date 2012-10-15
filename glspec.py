import hashcomments
import os.path
import re


# Map from function name to a hash with key/value pairs:
# - 'abstract_return': return type of the function (as defined in
#                      gl.tm).
# - 'params': list of function parameters.
# - 'deprecated': For deprecated functions, GL version in which
#                 function no longer appeared, otherwise None.
# - 'category': GL version or extension defining this function.  E.g.
#               'VERSION_1_0' or 'ARB_multitexture'.
#
# Each function parameter is a hash with key/value pairs:
# - 'name': name of the parameter.
# - 'abstract_type': type of the parameter (as defined in gl.tm).
# - 'direction': direction of the parameter ('in' or 'out')
# - 'pointer_type': 'array', 'reference', or 'value'
# - 'array_size': Size expression (present only if pointer_type is
#                 'array')
# - 'array_retained': True if the array is annotated as "retained"
#                     (present only if pointer_type is 'array')
FUNCTIONS = {}


# Known bugs in gl.spec: some functions are missing "deprecated"
# annotations.
FUNCTIONS_MISSING_DEPRECATION = {
    'Indexub': '3.1',
    'Indexubv': '3.1',
    }


INITIAL_DECLARATION_REGEXP = re.compile('^[a-z-]+:')
SIGNATURE_REGEXP = re.compile(
    r'^(?P<name>[A-Za-z0-9_]+)\((?P<params>[A-Za-z0-9_, ]*)\)$')


def group_functions(lines):
    """Yield lists of lines, where each list constitutes a single
    function declaration.
    """
    current_function = []
    for line in hashcomments.filter_out_comments(lines):
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
        param_infos = [None for p in param_names]
        return_type = None
        deprecated = None
        category = None
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
                param_name, param_info = value.split(None, 1)
                i = param_names.index(param_name)
                param_infos[i] = param_info
            elif key == 'deprecated':
                deprecated = value
            elif key == 'category':
                category = value
        if deprecated is None and name in FUNCTIONS_MISSING_DEPRECATION:
            deprecated = FUNCTIONS_MISSING_DEPRECATION[name]
        assert all(param_infos)
        params = [decode_param(name, type)
                  for name, type in zip(param_names, param_infos)]
        FUNCTIONS[name] = {'abstract_return': return_type, 'params': params,
                           'deprecated': deprecated, 'category': category}


def decode_param(name, info):
    info = info.split()
    result = {}
    result['name'] = name
    result['abstract_type'] = info[0]
    result['direction'] = info[1]
    result['pointer_type'] = info[2]
    if result['pointer_type'] == 'array':
        assert info[3][0] == '['
        assert info[3][-1] == ']'
        result['array_size'] = info[3][1:-1]
        if len(info) > 4:
            assert info[4] == 'retained'
            result['array_retained'] = True
        else:
            result['array_retained'] = False
    return result


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


main()
