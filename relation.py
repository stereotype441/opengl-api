def invert(rel, extra_keys = None):
    """Invert the relation represented by a map from X to a list of Y.

    This function returns a new map, from Y to a list of X, such that:
    (x in invert(rel)[y]) == (y in rel[x])

    If extra_keys is specified, then each key it contains is
    guaranteed to appear in the resulting map, even if it maps to the
    empty list.
    """
    result = {}
    for key in sorted(rel.keys()):
        for value in rel[key]:
            if value not in result:
                result[value] = []
            result[value].append(key)
    for key in extra_keys:
        if key not in result:
            result[key] = []
    return result
