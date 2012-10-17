import os
import os.path
import re
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
#
# Each function parameter is a hash with key/value pairs:
# - 'name': name of the parameter.
# - 'type': C type of the parameter.
FUNCTIONS = {}


# Map from extension name to a list of functions defined by that
# extension.  Gleaned from the category each function appears in.
FUNCTIONS_BY_EXTENSION = {}


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
                   'es2', 'deprecated'])
    name = elem.attrib['name']
    return_type = 'void'
    deprecated = elem.attrib.get('deprecated', 'none')
    if deprecated == 'none':
        deprecated = None
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
    function_dict = {'return': return_type, 'params': params}
    for attr in ('deprecated', 'es1', 'es2'):
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

def main():
    xml_dir = '/home/pberry/mesa/src/mapi/glapi/gen'
    xml_files = [file for file in os.listdir(xml_dir) if file.endswith('.xml')]
    for file in xml_files:
        tree = etree.parse(os.path.join(xml_dir, file))
        assert tree.getroot().tag == 'OpenGLAPI'
        process_OpenGLAPI(tree.getroot())

main()
