def diff_keys(a_keys, b_keys, a_name, b_name, entities_name,
              key_printer = None):
    key_diff = a_keys - b_keys
    if key_diff:
        print('{0} in {1} but not {2}:'.format(entities_name, a_name, b_name))
        if key_printer is not None:
            key_diff = [key_printer(key) for key in key_diff]
        for key in sorted(key_diff):
            print('  {0}'.format(key))


def diff_functions_by_extension(a_map, b_map, a_name, b_name):
    a_exts = set(a_map.keys())
    b_exts = set(b_map.keys())
    diff_keys(a_exts, b_exts, a_name, b_name, 'extensions')
    diff_keys(b_exts, a_exts, b_name, a_name, 'extensions')
    common_exts = a_exts & b_exts
    for ext in sorted(common_exts):
        a_funcs = set(a_map[ext])
        b_funcs = set(b_map[ext])
        diff_keys(a_funcs, b_funcs, a_name, b_name,
                  '{0} functions'.format(ext))
        diff_keys(b_funcs, a_funcs, b_name, a_name,
                  '{0} functions'.format(ext))
