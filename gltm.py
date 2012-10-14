# This script outputs the following JSON information:
#
# 'type_map': type_name -> type_definition

import hashcomments
import json
import os.path
import sys


TYPE_MAP = {}


def process_gltm(f):
    for line in hashcomments.filter_out_comments(f):
        fields = line.split(',')
        fields = [field.strip() for field in fields]
        key = fields[0]
        value = fields[3]
        if key in TYPE_MAP:
            raise Exception('Type name {0} seen twice'.format(key))
        TYPE_MAP[key] = value


def main():
    spec_dir = '/home/pberry/opengl-docs/www.opengl.org/registry/api/'
    gltm_file = os.path.join(spec_dir, 'gl.tm')
    with open(gltm_file, 'r') as f:
        process_gltm(f)
    json_data = {'type_map': TYPE_MAP}
    json.dump(json_data, sys.stdout)


main()
