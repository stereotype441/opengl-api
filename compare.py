def diff_keys(a_keys, b_keys, a_name, b_name, entities_name):
    key_diff = a_keys - b_keys
    if key_diff:
        print('{0} in {1} but not {2}:'.format(entities_name, a_name, b_name))
        for key in key_diff:
            print('  {0}'.format(key))
