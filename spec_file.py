import hashcomments
import re


# Parse a gl.spec file, performing the given corrections along the
# way.  Return a map from function name to a hash with key/value pairs
# indicating the properties of the functions.
#
# See glspec.py for additional documentation.
def parse_spec_file(filename,
                    functions_missing_deprecation = {},
                    functions_erroneously_deprecated = {},
                    function_alias_fixes = {}):
    functions = {}
    with open(filename, 'r') as f:
        for func in group_functions(f):
            name, param_names = parse_signature(func[0])
            if name in functions:
                raise Exception('Function {0} seen twice'.format(name))
            param_infos = [None for p in param_names]
            return_type = None
            deprecated = None
            category = None
            subcategory = None
            alias = None
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
                elif key == 'subcategory':
                    if subcategory is not None:
                        raise Exception('Function {0} has multiple subcategories')
                    subcategory = value
                elif key == 'alias':
                    alias = value
            if name in function_alias_fixes:
                alias = function_alias_fixes[name]
            if deprecated is None and name in functions_missing_deprecation:
                deprecated = functions_missing_deprecation[name]
            if deprecated is not None and name in functions_erroneously_deprecated:
                deprecated = None
            assert all(param_infos)
            params = [decode_param(name, type)
                      for name, type in zip(param_names, param_infos)]
            functions[name] = {'abstract_return': return_type, 'params': params,
                               'deprecated': deprecated, 'category': category,
                               'subcategory': subcategory, 'alias': alias}
    return functions


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
