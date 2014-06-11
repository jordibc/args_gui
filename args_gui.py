"""
Create a html gui from the parser object of argparse.
"""


def html(parser):
    "Write a html page with a form extracted from the args of parser"

    # See https://cmssdt.cern.ch/SDT/doxygen/CMSSW_5_2_7/doc/html/d5/ded/classargparse_1_1Action.html

    args_txt = '<ul>\n'
    for action in parser._get_optional_actions():
        name = action.dest.replace('_', ' ')
        input_type = 'number' if action.type == int else 'text'

        args_txt += '  <li>%s: ' % name

        if action.nargs == 0:
            args_txt += ('<input type="checkbox" name="%s" %s>' %
                         (name, 'checked' if action.default == True else ''))
        elif action.nargs == 1:
            args_txt += ('<input type="%s" name="%s" value="%s">' % 
                         (input_type, name, action.default))
        elif type(action.nargs) == int:
            args_txt += '<textarea name="%s" rows="%d">' % (name, action.nargs)
            for item in action.default:
                args_txt += item + '\n'
            args_txt += '</textarea>'
        elif action.nargs in '?*+':
            args_txt += '<textarea name="%s">' % name
            for item in action.default:
                args_txt += item + '\n'
            args_txt += '</textarea>'

        if action.help:
            args_txt += (' <a onclick="alert(\'%s\')" title="%s">[?]</a>' %
                         (action.help, action.help))

        args_txt += '</li>\n'
    args_txt += '</ul>\n'

    return """\
<!DOCTYPE html>
<html>
<head>
  <title>%(title)s</title>
</head>
<body>

<h1>%(title)s</h1>

%(description)s

%(args_txt)s

<pre>
%(usage)s
</pre>

%(epilog)s

</body>
</html>
""" % {'title': parser.prog,
       'description': ('<p>%s</p>' % parser.description if parser.description
                       else ''),
       'args_txt': args_txt,
       'usage': parser.format_usage(),
       'epilog': '<p>%s</p>' % parser.epilog if parser.epilog else ''}
    # TO DO: add the rest of option from
    # http://www.w3schools.com/html/html_forms.asp
    # (label, fieldset, legend, optgroup, etc)



if __name__ == '__main__':
    # Run a simple test.

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('--process', metavar='FILE', nargs='+', default=[], required=True,
        help='text files to scan')
    add('--learn-from', metavar='FILE', nargs='+', default=[],
        help='text files to learn from')
    add('--values', action='store_true',
        help='show the interest factor next to each word')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")

    # Now we don't do "args = parser.parse_args()", just write a webpage:
    print html(parser)
