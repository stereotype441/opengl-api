# Code for parsing a tm file (e.g. the gl.tm file published by OpenGL)

import hashcomments

# Return a map from abstract type name to C type.
def parse_type_map(filename):
    type_map = {}
    with open(filename, 'r') as f:
        for line in hashcomments.filter_out_comments(f):
            fields = line.split(',')
            fields = [field.strip() for field in fields]
            key = fields[0]
            value = fields[3]
            if key in type_map:
                raise Exception('Type name {0} seen twice'.format(key))
            type_map[key] = value
    return type_map
