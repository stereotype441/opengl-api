import compare
import mesa
import re


SET_REGEXP = re.compile(r'^SET_(?P<glname>[a-zA-Z0-9_]+)\(exec, (?P<funcname>[a-zA-Z0-9_]+)\);')


FUNCTIONS = {}


def find_function_start(lines):
    for i in range(len(lines) - 1):
        if lines[i].find('_mesa_create_exec_table') != -1 and lines[i+1] == '{\n':
            return i+2
    raise Exception('Where does function start?')


def find_function_end(lines, start):
    for i in range(start, len(lines)):
        if lines[i] == '}\n':
            return i
    raise Exception('Where does function end?')


def skip_prolog(lines, start):
    assert lines[start].strip() == 'struct _glapi_table *exec;'
    start += 1
    assert lines[start].strip() == 'exec = _mesa_alloc_dispatch_table(_gloffset_COUNT);'
    start += 1
    assert lines[start].strip() == 'if (exec == NULL)'
    start += 1
    assert lines[start].strip() == 'return NULL;'
    start += 1
    return start


def skip_epilog(lines, end):
    assert lines[end-1].strip() == 'return exec;'
    end -= 1
    return end


def process_api_exec(f):
    default_condition = {'desktop': True, 'deprecated': None, 'es1': True, 'es2': '2.0'}
    condition = default_condition
    inside_condition = False
    lines = list(f)
    function_start = find_function_start(lines)
    function_end = find_function_end(lines, function_start)
    function_start = skip_prolog(lines, function_start)
    function_end = skip_epilog(lines, function_end)
    for line in lines[function_start:function_end]:
        line = line.strip()
        if line.startswith('if ('):
            assert not inside_condition
            inside_condition = True
            if line == 'if (_mesa_is_desktop_gl(ctx) || _mesa_is_gles3(ctx)) {':
                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': '3.0'}
            elif line == 'if (_mesa_is_desktop_gl(ctx)) {':
                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': None}
            elif line == 'if (ctx->API != API_OPENGLES2 && ctx->API != API_OPENGL_CORE) {':
                condition = {'desktop': True, 'deprecated': '3.1', 'es1': True, 'es2': None}
            elif line == 'if (ctx->API != API_OPENGLES2 || _mesa_is_gles3(ctx)) {':
                condition = {'desktop': True, 'deprecated': None, 'es1': True, 'es2': '3.0'}
            elif line == 'if (ctx->API != API_OPENGLES2) {':
                condition = {'desktop': True, 'deprecated': None, 'es1': True, 'es2': None}
            elif line == 'if (ctx->API != API_OPENGL_CORE && ctx->API != API_OPENGLES2) {':
                condition = {'desktop': True, 'deprecated': '3.1', 'es1': True, 'es2': None}
            elif line == 'if (ctx->API == API_OPENGL || ctx->API == API_OPENGL_CORE) {':
                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': None}
            elif line == 'if (ctx->API == API_OPENGL) {':
                condition = {'desktop': True, 'deprecated': '3.1', 'es1': False, 'es2': None}
            elif line == 'if (ctx->API != API_OPENGLES) {':
                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': '2.0'}
            elif line == 'if (ctx->API == API_OPENGL || ctx->API == API_OPENGLES) {':
                condition = {'desktop': True, 'deprecated': '3.1', 'es1': True, 'es2': None}
            elif line == 'if (ctx->API == API_OPENGLES) {':
                condition = {'desktop': False, 'deprecated': None, 'es1': True, 'es2': None}
            else:
                raise Exception('Unexpected condition {0!r}'.format(line))
        elif line.startswith('SET_'):
            m = SET_REGEXP.match(line)
            if m is None:
                raise Exception('Failed to match regexp on {0!r}'.format(line))
            glname = m.group('glname')
            funcname = m.group('funcname')
            if glname in FUNCTIONS:
                assert FUNCTIONS[glname]['mesa_function'] == funcname
                FUNCTIONS[glname]['condition'] = combine_conditions(condition, functions[glname]['condition'])
            else:
                FUNCTIONS[glname] = {'mesa_function': funcname, 'condition': dict(condition)}
        elif line == '}':
            assert inside_condition
            inside_condition = False
            condition = default_condition
        else:
            raise Exception('Unexpected line {0!r}'.format(line))


def main():
    src_file = '/home/pberry/mesa/src/mesa/main/api_exec.c'
    with open(src_file, 'r') as f:
        process_api_exec(f)
    xml_keys = set(alias_set['canonical_name']
                   for alias_set in mesa.ALIAS_SETS
                   if alias_set['dispatch'] not in ('skip', 'dynamic'))
    exec_keys = set(FUNCTIONS.keys())
    compare.diff_keys(xml_keys, exec_keys, 'XML', 'api_exec.c', 'functions')
    compare.diff_keys(exec_keys, xml_keys, 'api_exec.c', 'XML', 'functions')
    common_keys = xml_keys & exec_keys
    for name in sorted(common_keys):
        mesa_alias_set = mesa.ALIAS_SETS_BY_FUNCTION[name]
        mesa_name = mesa_alias_set['mesa_name']
        dispatch = mesa_alias_set['dispatch']
        if dispatch is None:
            xml_mesa_function = '_mesa_' + mesa_name
        elif dispatch == 'loopback':
            xml_mesa_function = 'loopback_' + mesa_name
        elif dispatch == 'es':
            xml_mesa_function = '_es_' + mesa_name
        elif dispatch == 'check':
            xml_mesa_function = '_check_' + mesa_name
        else:
            raise Exception('Function {0} has unexpected dispatch {1!r}'.format(name, dispatch))
        if FUNCTIONS[name]['mesa_function'] != xml_mesa_function:
            print('{0}: XML says mesa function is {1!r}, but api_exec.c says it\'s {2!r}'.format(
                    name, xml_mesa_function, FUNCTIONS[name]['mesa_function']))
        condition = FUNCTIONS[name]['condition']
        for key in ('deprecated', 'es1', 'es2', 'desktop'):
            mesa_value = mesa_alias_set[key]
            if key == 'es1':
                mesa_value = (mesa_value is not None)
            api_exec_value = condition[key]
            if mesa_value != api_exec_value:
                print('{0}: XML says {1} is {2!r}, but api_exec.c says it\'s {3!r}'.format(
                        name, key, mesa_value, api_exec_value))

    # TODO: warn if multiple non-aliased functions dispatch to the same Mesa function.

main()
