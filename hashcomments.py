def filter_out_comments(lines):
    for line in lines:
        # As of 10/13/2012, gl.spec contains a stray '[' at the
        # beginning of a comment line.  Filter that out.
        if line.startswith('[#'):
            continue
        comment_start = line.find('#')
        if comment_start != -1:
            line = line[:comment_start]
        line = line.rstrip()
        if line != '':
            yield line
