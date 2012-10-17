import compare
import extensions
import opengl


compare.diff_functions_by_extension(
    extensions.FUNCTIONS_BY_EXTENSION, opengl.FUNCTIONS_BY_EXTENSION,
    'extension specs', 'opengl')
