def compute_alias_sets(functions):
    alias_sets_by_canonical_name = {}
    alias_sets_by_function = {}
    for name in functions:
        names_seen = [name]
        canonical_name = name
        while True:
            if canonical_name not in functions:
                raise Exception(
                    'Alias chain terminates in non-function: {0}'.format(
                        ' -> '.join(names_seen)))
            if functions[canonical_name]['alias'] is None:
                break
            canonical_name = functions[canonical_name]['alias']
            names_seen.append(canonical_name)
            if canonical_name in names_seen[:-1]:
                raise Exception(
                    'Alias loop: {0}'.format(' -> '.join(names_seen)))
        if canonical_name not in alias_sets_by_canonical_name:
            alias_sets_by_canonical_name[canonical_name] = {
                'canonical_name': canonical_name, 'functions': []}
        alias_set = alias_sets_by_canonical_name[canonical_name]
        alias_set['functions'].append(name)
        alias_sets_by_function[name] = alias_set
    alias_sets = [
        alias_sets_by_canonical_name[canonical_name]
        for canonical_name in sorted(alias_sets_by_canonical_name.keys())]
    return alias_sets, alias_sets_by_function
