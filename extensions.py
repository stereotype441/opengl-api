import os
import os.path
import re


# Map from extension name to a list of functions defined by that extension.
FUNCTIONS_BY_EXTENSION = {}


FUNC_PREFIX_PATTERN = r'^([a-zA-Z0-9_]+ +)+\**'
FUNC_NAME_PATTERN = r'([a-zA-Z0-9_]|{[a-z0-9 ,]+})+'
FUNCTION_REGEXP = re.compile(r'^{0}(?P<name>{1}) *\([a-zA-Z0-9_ ,*\[\]]*\);?$'.format(FUNC_PREFIX_PATTERN, FUNC_NAME_PATTERN))
EXPANSION_REGEXP = re.compile(r'{(?P<chars>[a-z0-9 ,]+)}')
COMPLEX_EXPANSIONS = {
    'bsifd ubusui': ('b', 's', 'i', 'f', 'd', 'ub', 'us', 'ui'),
    'ubusui': ('ub', 'us', 'ui'),
    }
FILES_TO_SKIP = frozenset([
        'ARB/get_proc_address.txt',
        'ARB/wgl_pbuffer.txt',
        'ARB/shader_atomic_counters.txt',
        'EXT/nurbs_tessellator.txt',
        'EXT/draw_range_elements.txt',
        'EXT/secondary_color.txt',
        'EXT/multi_draw_arrays.txt', # TODO: For now
        'EXT/fog_coord.txt',
        'EXT/stencil_clear_tag.txt',
        'EXT/direct_state_access.txt', # TODO: For now
        'SGIX/video_source.txt',
        'SGIX/instruments.txt',
        'SGIX/list_priority.txt',
        'SGIX/hyperpipe_group.txt',
        'HP/image_transform.txt', # TODO: For now
        'HP/occlusion_test.txt',
        'PGI/misc_hints.txt',
        'IBM/multimode_draw_arrays.txt', # TODO: For now
        'IBM/vertex_array_lists.txt', # TODO: For now
        'IBM/static_data.txt',
        'SUN/mesh_array.txt',
        'NV/present_video.txt',
        'NV/wgl_video_out.txt',
        'NV/gpu_affinity.txt',
        'NV/video_capture.txt',
        'ATI/envmap_bumpmap.txt',
        'ATI/pn_triangles.txt',
        'ATI/separate_stencil.txt',
        'OES/OES_fixed_point.txt',
        'OES/OES_query_matrix.txt', # TODO: For now
        'EXT/wgl_swap_control.txt',
        'EXT/glx_swap_control_tear.txt',
        'EXT/wgl_swap_control_tear.txt',
        'NV/glx_swap_group.txt',
        'NV/wgl_swap_group.txt',
        'OML/glx_sync_control.txt',
        'OML/wgl_sync_control.txt',
        'AMD/glx_gpu_association.txt',
        'AMD/wgl_gpu_association.txt',
        'ARB/multitexture.txt',
        'EXT/coordinate_frame.txt',
        ])

MISSING_FUNCTION_SUFFIXES = {
    'ATI/vertex_streams.txt': 'ATI',
    }


def expand_function_name(name):
    if '{' not in name:
        yield name
        return
    m = EXPANSION_REGEXP.search(name)
    if m:
        expansion = m.group('chars')
        if expansion in COMPLEX_EXPANSIONS:
            expansion = COMPLEX_EXPANSIONS[expansion]
        elif ',' in expansion:
            expansion = expansion.split(',')
        for c in expansion:
            new_name = name[:m.start()] + c + name[m.end():]
            for name2 in expand_function_name(new_name):
                yield name2
    else:
        raise Exception("Don't know how to expand {0!r}".format(name))


def process_spec_file(spec_dir, filename, f):
    full_spec_file_name = spec_dir + '/' + filename
    if full_spec_file_name in FILES_TO_SKIP:
        return
    if full_spec_file_name in MISSING_FUNCTION_SUFFIXES:
        suffix = MISSING_FUNCTION_SUFFIXES[full_spec_file_name]
    else:
        suffix = ''
    extension_name = None
    section = None
    procedures_and_functions = None
    func_start = None
    for line in f:
        line = line.rstrip()
        if line == '':
            pass
        elif line == 'Name':
            section = 'name'
        elif section == 'name':
            extension_name = line.strip()
            section = None
        elif line.lower() in ('new procedures and functions',
                              'new procedure and functions',
                              'new functions and procedures'):
            procedures_and_functions = []
            section = 'procs'
        elif section == 'procs':
            if func_start is None and line in ('New Types', 'New Tokens', 'Issues'):
                section = None
                continue
            if func_start is None and line.startswith('Additions to '):
                section = None
                continue
            if func_start is None and line.startswith('Modifications to '):
                section = None
                continue
            line = line.strip()
            if func_start is None and line in ('None', 'None.'):
                section = None
                continue
            # TODO: HACK
            if func_start is None and line == 'Note that GetIntegerIndexedvEXT, EnableIndexedEXT, DisableIndexedEXT and':
                section = None
                continue
            if func_start:
                line = func_start + ' ' + line
                func_start = None
            if '(' in line and not ')' in line:
                func_start = line
                continue
            # TODO: HACK
            if line.startswith('(All of the following'):
                continue
            if line.startswith('(note: '):
                continue
            if line.startswith('(Note: '):
                continue
            if line.startswith('(the following '):
                continue
            if line.startswith('These routines '):
                continue
            if line.startswith('The following '):
                continue
            if line.startswith('(added if '):
                continue
            if line.startswith('(The following function '):
                continue
            if line.startswith('NOTE: '):
                continue
            # TODO: HACK
            if line in ('GRAPHICS RESET DETECTION AND RECOVERY',
                        'SIZED BUFFER QUERIES',
                        'OpenGL 1.0 sized buffer queries',
                        'ARB_imaging sized buffer queries',
                        'OpenGL 1.3 sized buffer queries',
                        'OpenGL 2.0 sized buffer queries',
                        'The only allowable value for <target> at this time is',
                        'PIXEL_TRANSFORM_2D_EXT.  Allowable values for <pname> include:',
                        'PIXEL_MAG_FILTER_EXT, PIXEL_MIN_FILTER_EXT, and PIXEL_CUBIC_WEIGHT_EXT.',
                        'PATH SPECIFICATION COMMANDS',
                        'PATH NAME MANAGEMENT',
                        'PATH STENCILING',
                        'PATH COVERING',
                        'PATH QUERIES',
                        'For creating, updating, and querying object buffers:',
                        'For defining vertex arrays inside an object buffer:',
                        'For querying vertex arrays inside an object buffer:',
                        'If EXT_vertex_shader is defined, for defining variant arrays inside',
                        'an object buffer:',
                        'If EXT_vertex_shader is defined, for querying variant arrays inside',
                        ):
                continue
            m = FUNCTION_REGEXP.match(line)
            # TODO: HACK
            if m is None:
                raise Exception(
                    'Cannot parse proc/function line: {0!r}'.format(line))
            for name in expand_function_name(m.group('name')):
                if name.startswith('gl'):
                    name = name[2:]
                if suffix and not name.endswith(suffix):
                    name = name + suffix
                procedures_and_functions.append(name)
    assert extension_name is not None
    # TODO: HACK
    if os.path.join(spec_dir, filename) not in (
        'ARB/multitexture.txt', 'ARB/shading_language_100.txt',
        'ARB/half_float_pixel.txt', 'ARB/compatibility.txt',
        'ARB/shading_language_420pack.txt', 'EXT/texture_swizzle.txt'):
        assert procedures_and_functions is not None
    if procedures_and_functions is None:
        procedures_and_functions = []
    if extension_name in FUNCTIONS_BY_EXTENSION:
        raise Exception('Duplicate extension {0}'.format(extension_name))
    FUNCTIONS_BY_EXTENSION[extension_name] = procedures_and_functions


def main():
    spec_root = '/home/pberry/opengl-docs/www.opengl.org/registry/specs/'
    for spec_dir in os.listdir(spec_root):
        spec_dir_fullpath = os.path.join(spec_root, spec_dir)
        for file in os.listdir(spec_dir_fullpath):
            assert file.endswith('.txt')
            with open(os.path.join(spec_dir_fullpath, file),
                      errors='ignore') as f:
                process_spec_file(spec_dir, file, f)

main()
