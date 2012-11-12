import tm_file
import os.path


# Map from abstract type name to C type.
TYPE_MAP = {}


def main():
    global TYPE_MAP
    spec_dir = '/home/pberry/opengl-docs/www.opengl.org/registry/api/'
    gltm_file = os.path.join(spec_dir, 'gl.tm')
    TYPE_MAP = tm_file.parse_type_map(gltm_file)


main()
