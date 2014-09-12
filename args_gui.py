"""
Create a html gui from the parser object of argparse.
"""


from gi.repository import Gtk, Gdk, GLib


def gtk(parser, parent=None):
    "Show a gtk dialog with a form extracted from the args of parser"

    dialog = Gtk.Dialog(parser.prog, parent, 0,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK, Gtk.ResponseType.OK))

    box = dialog.get_content_area()
#    box.set_spacing(10)

    box.add(Gtk.Label(parser.description or ''))

    hbox = Gtk.HBox()
    box_names = Gtk.VBox()
    box_values = Gtk.VBox()

    # TODO: take parser._get_positional_actions() into account too.

    for action in parser._get_optional_actions():
        name = action.dest.replace('_', ' ')
        if name == 'help':
            continue
        if any(action in g._group_actions
               for g in parser._mutually_exclusive_groups):
            continue

        input_type = 'number' if action.type == int else 'text'

        if action.nargs == 0:
            button = Gtk.CheckButton(name)
            button.set_active(action.default)
            if action.help:
                button.set_tooltip_text(action.help)
            box.add(button)
        elif action.nargs == 1:
            box2 = Gtk.Box(Gtk.Orientation.HORIZONTAL, 10)
            box2.add(Gtk.Label(name))
            if action.metavar == 'FILE':
                button = Gtk.FileChooserButton('Select a file',
                                               Gtk.FileChooserAction.OPEN)
                button.set_current_folder('/etc')
                box2.add(button)
            else:
                box2.add(Gtk.Entry(text=action.default))
            if action.help:
                box2.set_tooltip_text(action.help)
            box.add(box2)
        elif type(action.nargs) == int:
            box2 = Gtk.Box(Gtk.Orientation.HORIZONTAL, 10)
            box2.add(Gtk.Label(name))
            sw = Gtk.ScrolledWindow()
            tv = Gtk.TextView()
            tv.set_hexpand(True)
            for item in action.default:
                tv.get_buffer().set_text(item + '\n')
            for i in range(action.nargs - len(action.default)):
                tv.get_buffer().set_text('\n')
            sw.add(tv)
            box2.add(sw)
            if action.help:
                box2.set_tooltip_text(action.help)
            box.add(box2)
        elif action.nargs in '?*+':
            box2 = Gtk.Box(Gtk.Orientation.HORIZONTAL, 10)
            box2.add(Gtk.Label(name))
            sw = Gtk.ScrolledWindow()
            tv = Gtk.TextView()
            tv.set_hexpand(True)
            for item in action.default:
                tv.get_buffer().set_text(item + '\n')
            sw.add(tv)
            box2.add(sw)
            if action.help:
                box2.set_tooltip_text(action.help)
            box.add(box2)

    for group in parser._mutually_exclusive_groups:
        last = None
        for action in group._group_actions:
            name = action.dest.replace('_', ' ')
            last = Gtk.RadioButton.new_with_label_from_widget(last, label=name)
            last.set_active(False) #action.default)
            if action.help:
                last.set_tooltip_text(action.help)
            box.add(last) #(last, True, True, 2)

    box.add(Gtk.Separator())
#    box.add(Gtk.Label(parser.format_usage()))
#    if parser.epilog:
#        box.add(Gtk.Label(parser.epilog))

    expander = Gtk.Expander()
    expander.set_label('Full help')
    expander.add(Gtk.Label(parser.format_help()))
    box.add(expander)

    hbox.add(box_names)
    hbox.add(box_values)
    box.add(hbox)

    return dialog


def html(parser):
    "Write a html page with a form extracted from the args of parser"

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

    window = Gtk.Window(title="Scipioncito example")
    window.connect('delete-event', Gtk.main_quit)
    button = Gtk.Button('Open dialog')
    dialog = gtk(parser, window)
    def f(widget):
        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print 'Ok buddy'
        elif response == Gtk.ResponseType.CANCEL:
            print 'No worries'
        dialog.hide()
    button.connect('clicked', f)
    window.add(button)
    window.show_all()
    Gtk.main()
