import mesa
import opengl


TYPE_EQUIVALENCES = {
    'GLclampf': 'GLfloat',
    'GLchar': 'char',
    'GLcharARB': 'char',
    'GLsizei': 'GLint',
    'GLclampd': 'GLdouble',
    'GLhandleARB': 'GLuint',
    'GLbitfield': 'GLenum',
    'GLvoid': 'void',
    }


def diff_keys(a_keys, b_keys, a_name, b_name, entities_name):
    key_diff = a_keys - b_keys
    if key_diff:
        print('{0} in {1} but not {2}:'.format(entities_name, a_name, b_name))
        for key in key_diff:
            print('  {0}'.format(key))


def normalize_mesa_function(func):
    func = dict(func)
    func['return'] = normalize_type(func['return'])
    func['params'] = [normalize_mesa_param(p) for p in func['params']]
    return func


def normalize_mesa_param(param):
    param = dict(param)
    del param['name']
    param['type'] = normalize_type(param['type'])
    return param


def normalize_opengl_function(func):
    func = dict(func)
    func['return'] = normalize_type(func['return'])
    del func['abstract_return']
    del func['category']
    func['params'] = [normalize_opengl_param(p) for p in func['params']]
    return func


def normalize_opengl_param(param):
    param = dict(param)
    param['type'] = normalize_type(param['type'])
    del param['name']
    del param['direction']
    del param['abstract_type']
    del param['pointer_type']
    if 'array_retained' in param:
        del param['array_retained']
    if 'array_size' in param:
        del param['array_size']
    return param


def normalize_type(type):
    type_parts = type.replace('*', ' * ').split()
    type_parts = [TYPE_EQUIVALENCES.get(p, p) for p in type_parts]
    return ' '.join(type_parts)


def summarize_function(name, func):
    if func['deprecated']:
        deprecation_string = ' /* deprecated in GL {0} */'.format(
            func['deprecated'])
    else:
        deprecation_string = ''
    return '{0} {1}({2}){3}'.format(
        func['return'], name,
        ', '.join(summarize_param(p) for p in func['params']),
        deprecation_string)


def summarize_param(param):
    return '{0} {1}'.format(param['type'], param['name'])


mesa_keys = set(mesa.FUNCTIONS.keys())
opengl_keys = set(opengl.FUNCTIONS.keys())
diff_keys(mesa_keys, opengl_keys, 'mesa', 'opengl', 'functions')
diff_keys(opengl_keys, mesa_keys, 'opengl', 'mesa', 'functions')
common_keys = mesa_keys & opengl_keys
for key in common_keys:
    mesa_func = normalize_mesa_function(mesa.FUNCTIONS[key])
    opengl_func = normalize_opengl_function(opengl.FUNCTIONS[key])
    # TODO: temporary HACK: ignore deprecation for extension functions
    if not opengl.FUNCTIONS[key]['category'].startswith('VERSION_'):
        mesa_func['deprecated'] = None
        opengl_func['deprecated'] = None
    if mesa_func != opengl_func:
        print('Function {0} does not match:'.format(key))
        print('  mesa: {0}'.format(
                summarize_function(key, mesa.FUNCTIONS[key])))
        print('  opengl: {0}'.format(
                summarize_function(key, opengl.FUNCTIONS[key])))
