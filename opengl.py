import glspec
import gltm


# Same as glspec.py's FUNCTIONS hash, except with additional key/value
# pairs:
# - 'return': C return type of the function
#
# And with additional key/value pairs for each function parameter:
# - 'type': C type of the parameter
FUNCTIONS = {}


# Map from extension name to a list of functions defined by that
# extension.  Gleaned from the "category" annotation.
FUNCTIONS_BY_EXTENSION = {}


# Function->extension mappings missing from gl.spec
FUNCTION_BY_EXTENSION_ADDITIONS = {
    'ARB_uniform_buffer_object':
        ['BindBufferRange', 'GetIntegeri_v', 'BindBufferBase'],
    'EXT_transform_feedback':
        ['GetIntegerIndexedvEXT', 'GetBooleanIndexedvEXT'],
    'ARB_vertex_shader':
        ['VertexAttrib1fARB', 'VertexAttrib1sARB', 'VertexAttrib1dARB',
         'VertexAttrib2fARB', 'VertexAttrib2sARB', 'VertexAttrib2dARB',
         'VertexAttrib3fARB', 'VertexAttrib3sARB', 'VertexAttrib3dARB',
         'VertexAttrib4fARB', 'VertexAttrib4sARB', 'VertexAttrib4dARB',
         'VertexAttrib4NubARB', 'VertexAttrib1fvARB', 'VertexAttrib1svARB',
         'VertexAttrib1dvARB', 'VertexAttrib2fvARB', 'VertexAttrib2svARB',
         'VertexAttrib2dvARB', 'VertexAttrib3fvARB', 'VertexAttrib3svARB',
         'VertexAttrib3dvARB', 'VertexAttrib4fvARB', 'VertexAttrib4svARB',
         'VertexAttrib4dvARB', 'VertexAttrib4ivARB', 'VertexAttrib4bvARB',
         'VertexAttrib4ubvARB', 'VertexAttrib4usvARB', 'VertexAttrib4uivARB',
         'VertexAttrib4NbvARB', 'VertexAttrib4NsvARB', 'VertexAttrib4NivARB',
         'VertexAttrib4NubvARB', 'VertexAttrib4NusvARB',
         'VertexAttrib4NuivARB', 'VertexAttribPointerARB',
         'EnableVertexAttribArrayARB', 'DisableVertexAttribArrayARB',
         'GetVertexAttribdvARB', 'GetVertexAttribfvARB',
         'GetVertexAttribivARB', 'GetVertexAttribPointervARB'],
    'ARB_debug_output': ['GetPointerv'],
    'ARB_separate_shader_objects': ['ProgramParameteri'],
    'ARB_vertex_attrib_64bit': ['VertexArrayVertexAttribLOffsetEXT'],
    'ARB_viewport_array':
        ['GetIntegerIndexedvEXT', 'EnableIndexedEXT', 'DisableIndexedEXT',
         'IsEnabledIndexedEXT'],
    'EXT_geometry_shader4':
        ['FramebufferTextureEXT', 'FramebufferTextureLayerEXT',
         'FramebufferTextureFaceEXT'],
    'EXT_gpu_shader4':
        ['VertexAttribI1iEXT', 'VertexAttribI2iEXT', 'VertexAttribI3iEXT',
         'VertexAttribI4iEXT', 'VertexAttribI1uiEXT', 'VertexAttribI2uiEXT',
         'VertexAttribI3uiEXT', 'VertexAttribI4uiEXT', 'VertexAttribI1ivEXT',
         'VertexAttribI2ivEXT', 'VertexAttribI3ivEXT', 'VertexAttribI4ivEXT',
         'VertexAttribI1uivEXT', 'VertexAttribI2uivEXT',
         'VertexAttribI3uivEXT', 'VertexAttribI4uivEXT', 'VertexAttribI4bvEXT',
         'VertexAttribI4svEXT', 'VertexAttribI4ubvEXT', 'VertexAttribI4usvEXT',
         'VertexAttribIPointerEXT', 'GetVertexAttribIivEXT',
         'GetVertexAttribIuivEXT'],
    'EXT_paletted_texture': ['ColorSubTableEXT'],
    'EXT_subtexture': ['TexSubImage3DEXT'],
    'KHR_debug': ['GetPointerv'],
    'NV_explicit_multisample':
        ['GetBooleanIndexedvEXT', 'GetIntegerIndexedvEXT'],
    'NV_fragment_program':
        ['ProgramLocalParameter4dARB', 'ProgramLocalParameter4dvARB',
         'ProgramLocalParameter4fARB', 'ProgramLocalParameter4fvARB',
         'GetProgramLocalParameterdvARB', 'GetProgramLocalParameterfvARB'],
    'NV_gpu_shader5': ['GetUniformui64vNV'],
    'NV_parameter_buffer_object':
        ['BindBufferRangeNV', 'BindBufferOffsetNV', 'BindBufferBaseNV',
         'GetIntegerIndexedvEXT'],
    'NV_transform_feedback':
        ['GetIntegerIndexedvEXT', 'GetBooleanIndexedvEXT'],
    }


# Function->extension mappings that should be removed from gl.spec
FUNCTION_BY_EXTENSION_SUBTRACTIONS = {
    'EXT_texture3D': ['TexSubImage3DEXT'],
    }


def convert_function(func):
    func = dict(func)
    func['return'] = convert_type(func['abstract_return'], 'value', 'in')
    func['params'] = [convert_param(p) for p in func['params']]
    return func


def convert_param(param):
    param = dict(param)
    param['type'] = convert_type(param['abstract_type'], param['pointer_type'],
                                 param['direction'])
    return param


def convert_type(type, pointer_type, direction):
    type = gltm.TYPE_MAP[type]
    if type == '*':
        type = 'void'
    if pointer_type != 'value':
        if direction == 'in':
            if '*' in type:
                # Technically, this should be:
                #
                #     type = '{0} const *'.format(type)
                #
                # However, the de facto standard used by existing GL
                # headers is
                #
                #     type = 'const {0} *'.format(type)
                #
                # So we follow that.
                type = 'const {0} *'.format(type)
            else:
                type = 'const {0} *'.format(type)
        else:
            type = '{0} *'.format(type)
    return type


def add_func_to_extension(func_name, ext_name):
    if ext_name not in FUNCTIONS_BY_EXTENSION:
        FUNCTIONS_BY_EXTENSION[ext_name] = []
    assert func_name not in FUNCTIONS_BY_EXTENSION[ext_name]
    FUNCTIONS_BY_EXTENSION[ext_name].append(func_name)


def remove_func_from_extension(func_name, ext_name):
    assert func_name in FUNCTIONS_BY_EXTENSION[ext_name]
    del FUNCTIONS_BY_EXTENSION[ext_name][
        FUNCTIONS_BY_EXTENSION[ext_name].index(func_name)]


for name, func in glspec.FUNCTIONS.items():
    if not func['category'].startswith('VERSION_'):
        add_func_to_extension(name, func['category'])
    FUNCTIONS[name] = convert_function(func)


for ext, funcs in FUNCTION_BY_EXTENSION_ADDITIONS.items():
    for func in funcs:
        add_func_to_extension(func, ext)

for ext, funcs in FUNCTION_BY_EXTENSION_SUBTRACTIONS.items():
    for func in funcs:
        remove_func_from_extension(func, ext)
