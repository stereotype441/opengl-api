import alias_sets
import os
import os.path
import re
import relation
import sanity
import xml.etree.ElementTree as etree


# Map from function name to a hash with key/value pairs:
# - 'return': C return type of the function.
# - 'params': list of function parameters.
# - 'deprecated': For deprecated functions, GL version in which
#                 function no longer appeared, otherwise None.
# - 'es1': For ES1 functions, ES version in which function appeared,
#          otherwise None.
# - 'es2': For ES2 functions, ES version in which function appeared,
#          otherwise None.
# - 'dispatch': How the function should be dispatched by api_exec.c
# - 'desktop': True for desktop functions, False otherwise.
# - 'alias': canonical function that this function is an alias for, if
#            any.  None if no alias is listed.
#
# Each function parameter is a hash with key/value pairs:
# - 'name': name of the parameter.
# - 'type': C type of the parameter.
FUNCTIONS = {}


# Map from extension name to a list of functions defined by that
# extension.  Gleaned from the category each function appears in.
FUNCTIONS_BY_EXTENSION = {}


# Map from function name to a list of extensions that define it.
EXTENSIONS_BY_FUNCTION = {}


# List of all function alias sets, each of which is a hash with
# key/value pairs:
# - 'canonical_name': canonical function name for the alias set
# - 'functions': list of names of functions in this alias set
#                (includes the canonical name).
# - 'deprecated': same as in FUNCTIONS*
# - 'es1': same as in FUNCTIONS*
# - 'es2': same as in FUNCTIONS*
# - 'dispatch': same as in FUNCTIONS*
# - 'desktop': same as in FUNCTIONS**
#
# *if all functions in the alias set have a value of None for the
#  property, this value is None.  If some functions have a value of
#  None and other functions have some other value, the other takes
#  precedence.  If some functions have one value (other than None) and
#  other functions have a different value (other than None), then this
#  value is 'inconsistent'.
#
# **This value is False iff any function in the alias set has a
#   desktop value of False.
ALIAS_SETS = []


# Map from function name to the alias set containing it.  The alias
# sets are the same objects as in the ALIAS_SETS list.
ALIAS_SETS_BY_FUNCTION = {}


GL_VERSION_NUMBER_REGEXP = re.compile(r'^[0-9]\.[0-9]$')
ES_VERSION_NUMBER_REGEXP = re.compile(r'^es[0-9]\.[0-9]$')


def check_attribs(elem, required_attribs, optional_attribs):
    attribs_present = set(elem.attrib.keys())
    required_attribs = set(required_attribs)
    optional_attribs = set(optional_attribs)
    problems = []
    missing_required_attribs = required_attribs - attribs_present
    if missing_required_attribs:
        problems.append('lacks required attribs {0}'.format(
                list(missing_required_attribs)))
    unrecognized_attribs = \
        attribs_present - required_attribs - optional_attribs
    if unrecognized_attribs:
        problems.append('contains extra attribs {0}'.format(
                list(unrecognized_attribs)))
    if problems:
        raise Exception('{0} {1} {2}'.format(elem.tag, elem.attrib,
                                             ' and '.join(problems)))

def process_OpenGLAPI(elem):
    check_attribs(elem, [], [])
    for child in elem:
        assert isinstance(child, etree.Element)
        if child.tag == 'category':
            process_category(child)
        elif child.tag == '{http://www.w3.org/2001/XInclude}include':
            process_include(child)
        else:
            raise Exception('Unexpected {0} in OpenGLAPI'.format(child.tag))

def process_include(elem):
    check_attribs(elem, ['href'], [])
    assert len(elem) == 0

def process_category(elem):
    check_attribs(elem, ['name'], ['number', 'window_system'])
    category_name = elem.attrib['name']
    window_system = elem.attrib.get('window_system', None)
    if window_system is not None:
        if window_system == 'glX':
            # Not worrying about GLX extensions/functions for now.
            return
        raise Exception(
            'Category {0} has unexpected window_system value {1!r}'.format(
                category_name, window_system))
    if category_name.startswith('GL_'):
        extension_name = category_name[3:]
    elif category_name.startswith('GLX_'):
        # We ignore these for now.
        extension_name = None
    elif GL_VERSION_NUMBER_REGEXP.match(category_name):
        # A GL version, not an extension.
        extension_name = None
    elif ES_VERSION_NUMBER_REGEXP.match(category_name):
        # An ES version, not an extension.
        extension_name = None
    elif category_name in ('NV_read_buffer', 'ANGLE_texture_compression_dxt'):
        # TODO: fix these in Mesa to use the GL_ prefix.
        extension_name = category_name
    else:
        raise Exception('Unexpected category name {0!r}'.format(category_name))
    if extension_name is not None and \
            extension_name not in FUNCTIONS_BY_EXTENSION:
        FUNCTIONS_BY_EXTENSION[extension_name] = []
    for child in elem:
        assert isinstance(child, etree.Element)
        if child.tag == 'enum':
            process_enum(child)
        elif child.tag == 'type':
            process_type(child)
        elif child.tag == 'function':
            process_function(child, extension_name)
        else:
            raise Exception('Unexpected {0} in category'.format(child.tag))

def process_function(elem, extension_name):
    check_attribs(elem, ['name'],
                  ['vectorequiv', 'offset', 'alias', 'static_dispatch', 'es1',
                   'es2', 'deprecated', 'desktop', 'dispatch'])
    name = elem.attrib['name']
    return_type = 'void'
    deprecated = elem.attrib.get('deprecated', 'none')
    if deprecated == 'none':
        deprecated = None
    alias = elem.attrib.get('alias', None)
    desktop = elem.attrib.get('desktop', 'true')
    if desktop == 'false':
        desktop = False
    elif desktop == 'true':
        desktop = True
    else:
        raise Exception(
            'Function {0} has illegal value '
            'for desktop property: {1!r}'.format(name, desktop))
    params = []
    for child in elem:
        assert isinstance(child, etree.Element)
        if child.tag == 'param':
            process_function_param(child, params)
        elif child.tag == 'glx':
            process_function_glx(child)
        elif child.tag == 'return':
            return_type = process_function_return(child)
        else:
            raise Exception('Unexpected {0} in function'.format(child.tag))
    if name in FUNCTIONS:
        raise Exception('Function {0} seen twice'.format(name))
    function_dict = {'return': return_type, 'params': params, 'alias': alias,
                     'desktop': desktop}
    for attr in ('deprecated', 'es1', 'es2', 'dispatch'):
        value = elem.attrib.get(attr, 'none')
        if value == 'none':
            value = None
        function_dict[attr] = value
    FUNCTIONS[name] = function_dict
    if extension_name is not None:
        FUNCTIONS_BY_EXTENSION[extension_name].append(name)

def process_function_return(elem):
    check_attribs(elem, ['type'], [])
    assert len(elem) == 0
    return elem.attrib['type']

def process_function_glx(elem):
    check_attribs(elem, [], ['sop', 'rop', 'large', 'handcode', 'always_array',
                             'dimensions_in_reply', 'img_reset', 'ignore',
                             'vendorpriv', 'doubles_in_order'])
    assert len(elem) == 0

def process_function_param(elem, params):
    check_attribs(elem, ['type', 'name'],
                  ['counter', 'variable_param', 'count', 'img_type',
                   'img_width', 'img_pad_dimensions', 'img_height',
                   'img_target', 'img_format', 'img_send_null', 'output',
                   'client_only', 'img_depth', 'padding', 'img_xoff',
                   'img_yoff', 'img_null_flag', 'img_zoff', 'img_extent',
                   'img_woff', 'count_scale'])
    assert len(elem) == 0
    param_type = elem.attrib['type']
    name = elem.attrib['name']
    padding = elem.attrib.get('padding', 'false') == 'true'
    if not padding:
        params.append({'type': param_type, 'name': name})

def process_type(elem):
    check_attribs(elem, ['name', 'size'],
                  ['float', 'unsigned', 'glx_name', 'pointer'])
    assert len(elem) == 0

def process_enum(elem):
    check_attribs(elem, ['name', 'value'], ['count'])
    for child in elem:
        assert isinstance(child, etree.Element)
        assert child.tag == 'size'
        process_enum_size(child)

def process_enum_size(elem):
    check_attribs(elem, ['name'], ['mode', 'count'])
    assert len(elem) == 0

def summarize_param(param):
    return '{0} {1}'.format(param['type'], param['name'])


def collect_alias_data(alias_set):
    for prop in ('deprecated', 'es1', 'es2', 'dispatch'):
        value = None
        for func in alias_set['functions']:
            if FUNCTIONS[func][prop] is not None:
                if value is None:
                    value = FUNCTIONS[func][prop]
                elif value != FUNCTIONS[func][prop]:
                    value = 'inconsistent'
        alias_set[prop] = value
    desktop = True
    for func in alias_set['functions']:
        if not FUNCTIONS[func]['desktop']:
            desktop = False
    alias_set['desktop'] = desktop


def main():
    global ALIAS_SETS, ALIAS_SETS_BY_FUNCTION, EXTENSIONS_BY_FUNCTION
    xml_dir = '/home/pberry/mesa/src/mapi/glapi/gen'
    xml_files = [file for file in os.listdir(xml_dir) if file.endswith('.xml')]
    for file in xml_files:
        tree = etree.parse(os.path.join(xml_dir, file))
        assert tree.getroot().tag == 'OpenGLAPI'
        process_OpenGLAPI(tree.getroot())
    ALIAS_SETS, ALIAS_SETS_BY_FUNCTION = alias_sets.compute_alias_sets(
        FUNCTIONS)
    for alias_set in ALIAS_SETS:
        collect_alias_data(alias_set)
    EXTENSIONS_BY_FUNCTION = relation.invert(
        FUNCTIONS_BY_EXTENSION, FUNCTIONS.keys())


main()
