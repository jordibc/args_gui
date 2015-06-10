"""
Create a html gui from the parser object of argparse.
"""


from gi.repository import Gtk


def gtk(parser, parent=None):
    """Return a gtk dialog with a form extracted from the args of parser."""
    dialog = Gtk.Dialog(parser.prog, parent, 0,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK, Gtk.ResponseType.OK))

    dialog.name = parser.prog
    box = dialog.get_content_area()
    box.set_spacing(5)

    box.add(Gtk.Label(parser.description or ''))

    expander = Gtk.Expander()
    expander.set_label('Full help')
    label_help = Gtk.Label()
    label_help.set_markup('<tt>%s</tt>' % parser.format_help())
    expander.add(label_help)
    expander.connect('activate', lambda widget: dialog.resize(1, 1))
    box.add(expander)

    box.add(Gtk.Separator())

    grid = Gtk.Grid(row_spacing=5, column_spacing=5)

    # Helper functions.
    def add(name, value, helptxt, row):
        label = Gtk.Label(name)
        if helptxt:
            label.set_tooltip_text(helptxt)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(value, 1, row, 1, 1)

    def new_action(name, action):
        # Show entry widgets depending on the input type.
        input_type = 'number' if action.type == int else 'text'

        if action.nargs == 0:
            button = Gtk.CheckButton()
            button.set_active(action.default)
            button.name = name
            add(name, button, action.help, row)
        elif action.nargs == 1 or action.nargs is None:
            if action.metavar == 'FILE':
                button = Gtk.FileChooserButton('Select a file',
                                               Gtk.FileChooserAction.OPEN)
                button.set_current_folder('/etc')
                button.name = name
                add(name, button, action.help, row)
            else:
                entry = Gtk.Entry(text=action.default)
                entry.name = name
                add(name, entry, action.help, row)
        elif type(action.nargs) == int:
            sw = Gtk.ScrolledWindow()
            tv = Gtk.TextView()
            tv.name = name
            tv.set_hexpand(True)
            if action.default:
                for item in action.default:
                    tv.get_buffer().set_text(item + '\n')
            for i in range(action.nargs -
                           (len(action.default) if action.default else 0)):
                tv.get_buffer().set_text('\n')
            sw.add(tv)
            add(name, sw, action.help, row)
        elif action.nargs in '?*+':
            sw = Gtk.ScrolledWindow()
            tv = Gtk.TextView()
            tv.name = name
            tv.set_hexpand(True)
            if action.default:
                for item in action.default:
                    tv.get_buffer().set_text(item + '\n')
            sw.add(tv)
            add(name, sw, action.help, row)

    row = 0
    last = None  # last element on a mutually exclusive group
    lastg = None  # last mutually exclusive group
    for action in parser._get_optional_actions():
        # Get name, avoid showing the "help" option if it is there.
        name = action.dest.replace('_', ' ')
        if name == 'help':
            continue

        # Handle the case of an option in an exclusive group first.
        exclusive = False
        for g in parser._mutually_exclusive_groups:
            if action in g._group_actions:
                # Create a new radio button in the appropriate group.
                if lastg != g:
                    last = None
                last = Gtk.RadioButton.new_from_widget(last)
                last.name = name
                lastg = g

                last.set_active(action.default)
                add(name, last, action.help, row)
                exclusive = True
                break
        if exclusive:
            row += 1
            continue

        new_action(name, action)
        row += 1

    # Handle the positional arguments.
    for action in parser._get_positional_actions():
        new_action('', action)  # empty name
        row += 1

    box.add(grid)

    return dialog


def gtk_get_args(parser):
    """Show a gui associated to the parser, return the selected parameters."""
    dialog = gtk(parser, Gtk.Window())
    dialog.connect('delete-event', Gtk.main_quit)
    dialog.show_all()

    def get_args(widget, result):
        if result != Gtk.ResponseType.OK:
            Gtk.main_quit()
            widget.argv = []  # used to "return" the value... nothing here
            return

        # TODO: make this code below look nicer.

        # Get the arguments.
        argv = [widget.name]
        pending = widget.get_children()
        while True:
            if not pending:
                break
            n = pending.pop()

            if isinstance(n, Gtk.ToggleButton):
                if n.get_active():
                    argv.append('--%s' % n.name.replace(' ', '-'))
            elif isinstance(n, Gtk.Entry):
                if n.name:
                    argv.append('--%s' % n.name.replace(' ', '-'))
                argv.append(n.get_text())
            elif isinstance(n, Gtk.TextView):
                buf = n.get_buffer()
                text = buf.get_text(buf.get_start_iter(),
                                    buf.get_end_iter(), True)
                if text:
                    if n.name:
                        argv.append('--%s' % n.name.replace(' ', '-'))
                    argv += text.split('\n')
            elif isinstance(n, Gtk.FileChooserButton):
                fn = n.get_filename()
                if n.name and fn:
                    argv.append('--%s' % n.name.replace(' ', '-'))
                if fn:
                    argv.append(fn)

            if hasattr(n, 'get_children'):
                pending += n.get_children()

        Gtk.main_quit()

        widget.argv = argv  # used to "return" the value

    dialog.connect('response', get_args)

    # Will show the dialog and wait until "Ok" or "Cancel" is clicked,
    # in which case get_args() will eventually call Gtk.main_quit().
    Gtk.main()

    return dialog.argv


def html(parser):
    """Write a html page with a form extracted from the args of parser."""
    # See https://cmssdt.cern.ch/SDT/doxygen/CMSSW_5_2_7/doc/html/d5/ded/classargparse_1_1Action.html

    # TODO: treat parser._mutually_exclusive_groups[0]._group_actions[0]
    # separately

    # TODO: take parser._get_positional_actions() into account too.

    args_txt = '<ul>\n'
    for action in parser._get_optional_actions():
        name = action.dest.replace('_', ' ')
        if name == 'help':
            continue

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
    # TO DO: add the rest of options from
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
    add('--nanna', nargs=1, default='hola hola', help='whatever', metavar='FILE')
    add('--values', action='store_true',
        help='show the interest factor next to each word')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")

    # Now we don't do "args = parser.parse_args()", just write a webpage:
    #print html(parser)

    print gtk_get_args(parser)
