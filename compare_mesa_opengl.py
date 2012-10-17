import compare
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


def normalize_mesa_function(func):
    return {
        'return': normalize_type(func['return']),
        'params': [normalize_mesa_param(p) for p in func['params']],
        'deprecated': func['deprecated']
        }


def normalize_mesa_param(param):
    return {
        'type': normalize_type(param['type'])
        }


def normalize_opengl_function(func):
    return {
        'return': normalize_type(func['return']),
        'params': [normalize_opengl_param(p) for p in func['params']],
        'deprecated': func['deprecated']
        }


def normalize_opengl_param(param):
    return {
        'type': normalize_type(param['type'])
        }


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


def process_alias_sets(alias_sets, functions_to_keep):
    functions_to_keep = frozenset(functions_to_keep)
    result = {}
    for alias_set in alias_sets:
        functions = frozenset(alias_set['functions']) & functions_to_keep
        if len(functions) > 1:
            result[functions] = alias_set
    return result


def alias_set_printer(alias_set):
    return '({0})'.format(', '.join(sorted(alias_set)))


mesa_keys = set(mesa.FUNCTIONS.keys())
opengl_keys = set(opengl.FUNCTIONS.keys())
compare.diff_keys(mesa_keys, opengl_keys, 'mesa', 'opengl', 'functions')
compare.diff_keys(opengl_keys, mesa_keys, 'opengl', 'mesa', 'functions')
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
compare.diff_functions_by_extension(
    mesa.FUNCTIONS_BY_EXTENSION, opengl.FUNCTIONS_BY_EXTENSION,
    'mesa', 'opengl')

# To compare alias sets we first eliminate any functions from the
# alias sets that aren't known to both opengl and mesa, and reorganize
# into maps from (frozenset of function names) to the original alias
# set.
#
# NOTE: we don't care if mesa and opengl differ in which function they
# call canonical.  Also, to reduce the volume of output, we don't
# print out alias sets that contain just a single function.
mesa_alias_sets = process_alias_sets(mesa.ALIAS_SETS, common_keys)
opengl_alias_sets = process_alias_sets(opengl.ALIAS_SETS, common_keys)
mesa_alias_keys = frozenset(mesa_alias_sets.keys())
opengl_alias_sets = frozenset(opengl_alias_sets.keys())
compare.diff_keys(mesa_alias_keys, opengl_alias_sets, 'mesa', 'opengl',
                  'alias sets', alias_set_printer)
compare.diff_keys(opengl_alias_sets, mesa_alias_keys, 'opengl', 'mesa',
                  'alias sets', alias_set_printer)
