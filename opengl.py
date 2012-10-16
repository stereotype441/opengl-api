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
# extension.  Gleaned from the "category" and "subcategory"
# annotations.
FUNCTIONS_BY_EXTENSION = {}


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


for name, func in glspec.FUNCTIONS.items():
    categories = [func['category']]
    if func['subcategory'] is not None:
        categories.append(func['subcategory'])
    for cat in categories:
        if cat.startswith('VERSION_'):
            continue
        add_func_to_extension(name, cat)
    FUNCTIONS[name] = convert_function(func)
