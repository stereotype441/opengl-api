import os
import os.path
import sanity
import xml.etree.ElementTree as etree


# Map from function name to a hash with key/value pairs:
# - 'return': C return type of the function.
# - 'params': list of function parameters.
#
# Each function parameter is a hash with key/value pairs:
# - 'name': name of the parameter.
# - 'type': C type of the parameter.
FUNCTIONS = {}


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
    for child in elem:
        assert isinstance(child, etree.Element)
        if child.tag == 'enum':
            process_enum(child)
        elif child.tag == 'type':
            process_type(child)
        elif child.tag == 'function':
            process_function(child)
        else:
            raise Exception('Unexpected {0} in category'.format(child.tag))

def process_function(elem):
    check_attribs(elem, ['name'],
                  ['vectorequiv', 'offset', 'alias', 'static_dispatch', 'es1',
                   'es2'])
    name = 'gl' + elem.attrib['name']
    return_type = 'void'
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
    FUNCTIONS[name] = {'return': return_type, 'params': params}

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
