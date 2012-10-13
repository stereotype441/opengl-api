SIMPLE_TYPES = set(['GLenum', 'GLfloat', 'GLuint', 'GLclampf', 'GLclampx',
                    'GLint', 'GLbyte', 'GLdouble', 'GLshort', 'GLbitfield',
                    'GLclampd', 'GLubyte', 'GLushort', 'GLfixed', 'GLboolean',
                    'GLsizei', 'GLhandleARB'])

def is_simple_function(func):
    if func['return'] != 'void':
        return False
    for param in func['params']:
        if param['type'] not in SIMPLE_TYPES:
            return False
    return True
