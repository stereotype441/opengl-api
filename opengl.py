import glspec
import gltm


# Same as glspec.py's FUNCTIONS hash, except with additional key/value
# pairs:
# - 'return': C return type of the function
#
# And with additional key/value pairs for each function parameter:
# - 'type': C type of the parameter
FUNCTIONS = {}


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


for name, func in glspec.FUNCTIONS.items():
    FUNCTIONS[name] = convert_function(func)
