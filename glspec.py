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
# - 'subcategory': Other GL version or extension defining this
#                  function, or None if none specified.
# - 'alias': canonical function that this function is an alias for, if
#            any.  None if no alias is listed.
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

# Known bugs in gl.spec: some functions have a "deprecated" annotation
# but shouldn't.
FUNCTIONS_ERRONEOUSLY_DEPRECATED = frozenset([
        'VertexAttrib1d',
        'VertexAttrib1dv',
        'VertexAttrib1f',
        'VertexAttrib1fv',
        'VertexAttrib1s',
        'VertexAttrib1sv',
        'VertexAttrib2d',
        'VertexAttrib2dv',
        'VertexAttrib2f',
        'VertexAttrib2fv',
        'VertexAttrib2s',
        'VertexAttrib2sv',
        'VertexAttrib3d',
        'VertexAttrib3dv',
        'VertexAttrib3f',
        'VertexAttrib3fv',
        'VertexAttrib3s',
        'VertexAttrib3sv',
        'VertexAttrib4Nbv',
        'VertexAttrib4Niv',
        'VertexAttrib4Nsv',
        'VertexAttrib4Nub',
        'VertexAttrib4Nubv',
        'VertexAttrib4Nuiv',
        'VertexAttrib4Nusv',
        'VertexAttrib4bv',
        'VertexAttrib4d',
        'VertexAttrib4dv',
        'VertexAttrib4f',
        'VertexAttrib4fv',
        'VertexAttrib4iv',
        'VertexAttrib4s',
        'VertexAttrib4sv',
        'VertexAttrib4ubv',
        'VertexAttrib4uiv',
        'VertexAttrib4usv',
        'VertexAttribI1i',
        'VertexAttribI2i',
        'VertexAttribI3i',
        'VertexAttribI4i',
        'VertexAttribI1ui',
        'VertexAttribI2ui',
        'VertexAttribI3ui',
        'VertexAttribI4ui',
        'VertexAttribI1iv',
        'VertexAttribI2iv',
        'VertexAttribI3iv',
        'VertexAttribI4iv',
        'VertexAttribI1uiv',
        'VertexAttribI2uiv',
        'VertexAttribI3uiv',
        'VertexAttribI4uiv',
        'VertexAttribI4bv',
        'VertexAttribI4sv',
        'VertexAttribI4ubv',
        'VertexAttribI4usv',
        'TexImage3D',
        ])

# Known bugs in gl.spec: some functions list an incorrect alias (or
# don't list an alias when one is required).
FUNCTION_ALIAS_FIXES = {
    'GenVertexArraysAPPLE': 'GenVertexArrays',
    'AreTexturesResidentEXT': 'AreTexturesResident',
    'BlendEquationIndexedAMD': 'BlendEquationi',
    'BlendEquationSeparateIndexedAMD': 'BlendEquationSeparatei',
    'BlendFuncIndexedAMD': 'BlendFunci',
    'BlendFuncSeparateIndexedAMD': 'BlendFuncSeparatei',
    'DeleteTexturesEXT': 'DeleteTextures',
    'GenTexturesEXT': 'GenTextures',
    'GetColorTableEXT': 'GetColorTable',
    'GetColorTableParameterfvEXT': 'GetColorTableParameterfv',
    'GetColorTableParameterivEXT': 'GetColorTableParameteriv',
    'GetColorTableSGI': 'GetColorTable',
    'GetColorTableParameterfvSGI': 'GetColorTableParameterfv',
    'GetColorTableParameterivSGI': 'GetColorTableParameteriv',
    'GetConvolutionFilterEXT': 'GetConvolutionFilter',
    'GetConvolutionParameterfvEXT': 'GetConvolutionParameterfv',
    'GetConvolutionParameterivEXT': 'GetConvolutionParameteriv',
    'GetHistogramEXT': 'GetHistogram',
    'GetHistogramParameterfvEXT': 'GetHistogramParameterfv',
    'GetHistogramParameterivEXT': 'GetHistogramParameteriv',
    'GetMinmaxEXT': 'GetMinmax',
    'GetMinmaxParameterfvEXT': 'GetMinmaxParameterfv',
    'GetMinmaxParameterivEXT': 'GetMinmaxParameteriv',
    'GetQueryObjecti64vEXT': 'GetQueryObjecti64v',
    'GetQueryObjectui64vEXT': 'GetQueryObjectui64v',
    'GetSeparableFilterEXT': 'GetSeparableFilter',
    'GetVertexAttribdvARB': 'GetVertexAttribdv',
    'GetVertexAttribfvARB': 'GetVertexAttribfv',
    'GetVertexAttribivARB': 'GetVertexAttribiv',
    'IsTextureEXT': 'IsTexture',
    'MultiTexCoord1dARB': 'MultiTexCoord1d',
    'MultiTexCoord1fARB': 'MultiTexCoord1f',
    'MultiTexCoord1iARB': 'MultiTexCoord1i',
    'MultiTexCoord1sARB': 'MultiTexCoord1s',
    'MultiTexCoord2dARB': 'MultiTexCoord2d',
    'MultiTexCoord2fARB': 'MultiTexCoord2f',
    'MultiTexCoord2iARB': 'MultiTexCoord2i',
    'MultiTexCoord2sARB': 'MultiTexCoord2s',
    'MultiTexCoord3dARB': 'MultiTexCoord3d',
    'MultiTexCoord3fARB': 'MultiTexCoord3f',
    'MultiTexCoord3iARB': 'MultiTexCoord3i',
    'MultiTexCoord3sARB': 'MultiTexCoord3s',
    'MultiTexCoord4dARB': 'MultiTexCoord4d',
    'MultiTexCoord4fARB': 'MultiTexCoord4f',
    'MultiTexCoord4iARB': 'MultiTexCoord4i',
    'MultiTexCoord4sARB': 'MultiTexCoord4s',
    'ProgramParameter4dNV': 'ProgramEnvParameter4dARB',
    'ProgramParameter4dvNV': 'ProgramEnvParameter4dvARB',
    'ProgramParameter4fNV': 'ProgramEnvParameter4fARB',
    'ProgramParameter4fvNV': 'ProgramEnvParameter4fvARB',
    'ProvokingVertexEXT': 'ProvokingVertex',
    'VertexAttrib1dNV': None,
    'VertexAttrib1dvNV': None,
    'VertexAttrib1fNV': None,
    'VertexAttrib1fvNV': None,
    'VertexAttrib1sNV': None,
    'VertexAttrib1svNV': None,
    'VertexAttrib2dNV': None,
    'VertexAttrib2dvNV': None,
    'VertexAttrib2fNV': None,
    'VertexAttrib2fvNV': None,
    'VertexAttrib2sNV': None,
    'VertexAttrib2svNV': None,
    'VertexAttrib3dNV': None,
    'VertexAttrib3dvNV': None,
    'VertexAttrib3fNV': None,
    'VertexAttrib3fvNV': None,
    'VertexAttrib3sNV': None,
    'VertexAttrib3svNV': None,
    'VertexAttrib4ubNV': None,
    'VertexAttrib4ubvNV': None,
    'VertexAttrib4dNV': None,
    'VertexAttrib4dvNV': None,
    'VertexAttrib4fNV': None,
    'VertexAttrib4fvNV': None,
    'VertexAttrib4sNV': None,
    'VertexAttrib4svNV': None,
    'GetVertexAttribdvNV': None,
    'GetVertexAttribfvNV': None,
    'GetVertexAttribivNV': None,
    'BindVertexArrayAPPLE': None,
    'StencilFuncSeparateATI': None,
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
        if name in FUNCTION_ALIAS_FIXES:
            alias = FUNCTION_ALIAS_FIXES[name]
        if deprecated is None and name in FUNCTIONS_MISSING_DEPRECATION:
            deprecated = FUNCTIONS_MISSING_DEPRECATION[name]
        if deprecated is not None and name in FUNCTIONS_ERRONEOUSLY_DEPRECATED:
            deprecated = None
        assert all(param_infos)
        params = [decode_param(name, type)
                  for name, type in zip(param_names, param_infos)]
        FUNCTIONS[name] = {'abstract_return': return_type, 'params': params,
                           'deprecated': deprecated, 'category': category,
                           'subcategory': subcategory, 'alias': alias}


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
