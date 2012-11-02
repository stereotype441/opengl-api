import compare
import mesa
import os
import os.path
import re


FUNCTION_START_REGEXP = re.compile(r'^(void )?(?P<name>[a-zA-Z0-9_]+)\(.*\)$')
IF_STATEMENT_REGEXP = re.compile(r'if \((?P<condition>.*)\)(?P<brace> {)?$')
FUNCTION_CALL_REGEXP = re.compile(r'^(?P<name>[a-zA-Z0-9_]+)\(.*\);$')
SET_REGEXP = re.compile(r'^SET_(?P<glname>[a-zA-Z0-9_]+)\((exec|dest|table|disp), (?P<funcname>[a-zA-Z0-9_]+)\);')


FUNCTIONS = {}


def remove_comments(contents):
    result_strings = []
    pos = 0
    while True:
        comment_start = contents.find('/*', pos)
        if comment_start == -1:
            result_strings.append(contents[pos:])
            break
        result_strings.append(contents[pos:comment_start])
        comment_end = contents.find('*/', comment_start + 2)
        pos = comment_end + 2
    return ' '.join(result_strings)


def kill_if_zeros(lines):
    killing = False
    for line in lines:
        if line == '#if 0':
            assert not killing
            killing = True
            continue
        if line.startswith('#if'):
            assert not killing
        if line == '#endif' and killing:
            killing = False
            continue
        if not killing:
            yield line


def is_function_of_interest(name):
    if name == '_mesa_create_exec_table':
        return True
    if name.find('_init_') == -1:
        return False
    if name.endswith('_remap_table'):
        return False
    if name.endswith('_table'):
        return True
    if name.endswith('_dispatch'):
        return True
    return False


def join_lines(lines):
    continuation = None
    for line in lines:
        if continuation:
            line = continuation + ' ' + line
            continuation = None
        if '(' in line and ')' not in line:
            continuation = line
            continue
        yield line
    assert continuation is None


class Scanner(object):
    def __init__(self, contents):
        lines = [line.strip()
                 for line in remove_comments(contents).split('\n')]
        lines = [line for line in lines if line]
        lines = list(kill_if_zeros(lines))
        self.lines = list(join_lines(lines))
        self.i = 0

    def lines_remain(self):
        return self.i < len(self.lines)

    def peek_line(self):
        return self.lines[self.i]

    def get_line(self):
        line = self.lines[self.i]
        self.i += 1
        return line

    def process_statement(self):
        line = self.get_line()
        m = IF_STATEMENT_REGEXP.match(line)
        if m:
            condition = m.group('condition')
            if m.group('brace'):
                body = self.process_block_body()
            else:
                body = self.process_statement()
                if body:
                    body = [body]
                else:
                    body = []
            return ('if', condition, body)
        m = SET_REGEXP.match(line)
        if m:
            return ('set', m.group('glname'), m.group('funcname'))
        m = FUNCTION_CALL_REGEXP.match(line)
        if m:
            return ('call', m.group('name'))
        if line.find('_mesa_alloc_dispatch_table') != -1:
            # Allocating the dispatch table (boring).
            return None
        if line in ('#if FEATURE_GL', '#endif', '#if FEATURE_ES1'):
            # Boring line--ignore.
            return None
        if line.find(';') != len(line) - 1:
            raise Exception('Confusing statement {0!r}'.format(line))
        if '{' in line or '}' in line or '(' in line or ')' in line:
            raise Exception('Confusing statement {0!r}'.format(line))
        # Otherwise it's a boring line so ignore it.
        return None

    def process_block_body(self):
        nodes = []
        while self.peek_line() != '}':
            node = self.process_statement()
            if node:
                nodes.append(node)
        self.get_line()
        return nodes

    def process_file(self, trees):
        while self.lines_remain():
            m = FUNCTION_START_REGEXP.match(self.get_line())
            if m:
                name = m.group('name')
                if is_function_of_interest(name):
                    line = self.get_line()
                    if line != '{':
                        raise Exception('Function {0} started with {1!r}, '
                                        'not {2!r}'.format(
                                name, line, '{'))
                    trees[name] = self.process_block_body()


#def process_api_exec(f):
#    default_condition = {'desktop': True, 'deprecated': None, 'es1': True, 'es2': '2.0'}
#    condition = default_condition
#    inside_condition = False
#    lines = list(f)
#    function_start = find_function_start(lines)
#    function_end = find_function_end(lines, function_start)
#    function_start = skip_prolog(lines, function_start)
#    function_end = skip_epilog(lines, function_end)
#    for line in lines[function_start:function_end]:
#        line = line.strip()
#        if line.startswith('if ('):
#            assert not inside_condition
#            inside_condition = True
#            if line == 'if (_mesa_is_desktop_gl(ctx) || _mesa_is_gles3(ctx)) {':
#                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': '3.0'}
#            elif line == 'if (_mesa_is_desktop_gl(ctx)) {':
#                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': None}
#            elif line == 'if (ctx->API != API_OPENGLES2 && ctx->API != API_OPENGL_CORE) {':
#                condition = {'desktop': True, 'deprecated': '3.1', 'es1': True, 'es2': None}
#            elif line == 'if (ctx->API != API_OPENGLES2 || _mesa_is_gles3(ctx)) {':
#                condition = {'desktop': True, 'deprecated': None, 'es1': True, 'es2': '3.0'}
#            elif line == 'if (ctx->API != API_OPENGLES2) {':
#                condition = {'desktop': True, 'deprecated': None, 'es1': True, 'es2': None}
#            elif line == 'if (ctx->API != API_OPENGL_CORE && ctx->API != API_OPENGLES2) {':
#                condition = {'desktop': True, 'deprecated': '3.1', 'es1': True, 'es2': None}
#            elif line == 'if (ctx->API == API_OPENGL || ctx->API == API_OPENGL_CORE) {':
#                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': None}
#            elif line == 'if (ctx->API == API_OPENGL) {':
#                condition = {'desktop': True, 'deprecated': '3.1', 'es1': False, 'es2': None}
#            elif line == 'if (ctx->API != API_OPENGLES) {':
#                condition = {'desktop': True, 'deprecated': None, 'es1': False, 'es2': '2.0'}
#            elif line == 'if (ctx->API == API_OPENGL || ctx->API == API_OPENGLES) {':
#                condition = {'desktop': True, 'deprecated': '3.1', 'es1': True, 'es2': None}
#            elif line == 'if (ctx->API == API_OPENGLES) {':
#                condition = {'desktop': False, 'deprecated': None, 'es1': True, 'es2': None}
#            else:
#                raise Exception('Unexpected condition {0!r}'.format(line))
#        elif line.startswith('SET_'):
#            m = SET_REGEXP.match(line)
#            if m is None:
#                raise Exception('Failed to match regexp on {0!r}'.format(line))
#            glname = m.group('glname')
#            funcname = m.group('funcname')
#            if glname in FUNCTIONS:
#                assert FUNCTIONS[glname]['mesa_function'] == funcname
#                FUNCTIONS[glname]['condition'] = combine_conditions(condition, functions[glname]['condition'])
#            else:
#                FUNCTIONS[glname] = {'mesa_function': funcname, 'condition': dict(condition)}
#        elif line == '}':
#            assert inside_condition
#            inside_condition = False
#            condition = default_condition
#        else:
#            raise Exception('Unexpected line {0!r}'.format(line))
#
#


def filter_apis(apis, condition):
    result = frozenset()
    for part in condition.split('||'):
        part = part.strip()
        sub_apis = apis
        for sub_part in part.split('&&'):
            sub_part = sub_part.strip()
            if sub_part == 'ctx->API != API_OPENGL_CORE':
                sub_apis -= frozenset(['core'])
            elif sub_part == 'ctx->API != API_OPENGLES2':
                sub_apis -= frozenset(['es2', 'es3'])
            elif sub_part == 'ctx->API != API_OPENGLES':
                sub_apis -= frozenset(['es1'])
            elif sub_part == 'ctx->API == API_OPENGL':
                sub_apis &= frozenset(['compat'])
            elif sub_part == 'ctx->API == API_OPENGL_CORE':
                sub_apis &= frozenset(['core'])
            elif sub_part == 'ctx->API == API_OPENGLES':
                sub_apis &= frozenset(['es1'])
            elif sub_part == '_mesa_is_gles3(ctx)':
                sub_apis &= frozenset(['es3'])
            elif sub_part == '_mesa_is_desktop_gl(ctx)':
                sub_apis &= frozenset(['core', 'compat'])
            else:
                raise Exception(part)
        result |= sub_apis
    return result


def interpret_trees(trees, func, apis, analysis):
    def recurse(nodes, apis):
        for node in nodes:
            if node[0] == 'if':
                if not node[2]:
                    continue
                recurse(node[2], filter_apis(apis, node[1]))
            elif node[0] == 'call':
                interpret_trees(trees, node[1], apis, analysis)
            elif node[0] == 'set':
                analysis.append((apis, node[1], node[2]))
            else:
                raise Exception(node[0])
    recurse(trees[func], apis)


def main():
    src_dir = '/home/pberry/mesa/src/mesa/main'
    src_files = [file for file in os.listdir(src_dir) if file.endswith('.c')]
    trees = {}
    for file in src_files:
        with open(os.path.join(src_dir, file), 'r') as f:
            Scanner(f.read()).process_file(trees)
    analysis = []
    interpret_trees(trees, '_mesa_create_exec_table',
                    frozenset(['es1', 'es2', 'es3', 'core', 'compat']),
                    analysis)
    for entry in analysis:
        apis = entry[0]
        if 'core' in apis:
            assert 'compat' in apis
        desktop = 'compat' in apis
        if 'compat' in apis and not 'core' in apis:
            deprecated = '3.1'
        else:
            deprecated = None
        es1 = 'es1' in apis
        if 'es2' in apis:
            assert 'es3' in apis
            es2 = '2.0'
        elif 'es3' in apis:
            es2 = '3.0'
        else:
            es2 = None
        annotations = {'desktop': desktop, 'deprecated': deprecated, 'es1': es1, 'es2': es2}
        glname = entry[1]
        funcname = entry[2]
        assert glname not in FUNCTIONS
        FUNCTIONS[glname] = {'mesa_function': funcname, 'condition': annotations}

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
