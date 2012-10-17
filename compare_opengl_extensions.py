import compare
import extensions
import opengl


extensions_exts = set(extensions.FUNCTIONS_BY_EXTENSION.keys())
opengl_exts = set(opengl.FUNCTIONS_BY_EXTENSION.keys())
compare.diff_keys(
    extensions_exts, opengl_exts, 'extensions', 'opengl', 'extensions')
compare.diff_keys(
    opengl_exts, extensions_exts, 'opengl', 'extensions', 'extensions')
common_exts = extensions_exts & opengl_exts
for ext in sorted(common_exts):
    extension_funcs = set(extensions.FUNCTIONS_BY_EXTENSION[ext])
    opengl_funcs = set(opengl.FUNCTIONS_BY_EXTENSION[ext])
    compare.diff_keys(
        extension_funcs, opengl_funcs, 'extension spec', 'opengl',
        '{0} functions'.format(ext))
    compare.diff_keys(
        opengl_funcs, extension_funcs, 'opengl', 'extension spec',
        '{0} functions'.format(ext))
