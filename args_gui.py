"""
Create a gui from the parser object of argparse.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def get_argv(parser):
    "Show a gui associated to the parser, return the selected parameters"
    dialog = create_dialog(parser, Gtk.Window())
    dialog.connect('delete-event', Gtk.main_quit)
    dialog.connect('response', get_args_callback)
    dialog.show_all()

    # Will show the dialog and wait until "Ok" or "Cancel" is clicked,
    # in which case get_args_callback() will eventually call Gtk.main_quit().
    Gtk.main()

    return dialog.argv


def get_args_callback(widget, result):
    "Set widget.argv to the contents of all the children widgets"
    # Only if result == Gtk.ResponseType.OK. Also, it will stop Gtk's main
    # loop. It is a callback function, called when clicking in the dialog.

    if result != Gtk.ResponseType.OK:
        Gtk.main_quit()
        widget.argv = []  # used to "return" the value... nothing here
        return

    argv = []
    last_name = ''
    def append_name(w):
        if not last_name.startswith('['):
            argv.append('--%s' % last_name)

    pending = widget.get_children()
    while pending:
        w = pending.pop()

        if isinstance(w, Gtk.Label):
            last_name = w.get_text().replace(' ', '-')
        elif isinstance(w, Gtk.ToggleButton):
            if w.get_active():
                append_name(w)
        elif isinstance(w, Gtk.Entry):
            if w.name:
                append_name(w)
            argv.append(w.get_text())
        elif isinstance(w, Gtk.TextView):
            buf = w.get_buffer()
            text = buf.get_text(buf.get_start_iter(),
                                buf.get_end_iter(), True)
            if text:
                if w.name:
                    append_name(w)
                argv += text.split('\n')
        elif isinstance(w, Gtk.FileChooserButton):
            fn = w.get_filename()
            if w.name and fn:
                append_name(w)
            if fn:
                argv.append(fn)

        if hasattr(w, 'get_children'):
            pending += w.get_children()

    Gtk.main_quit()

    widget.argv = argv  # used to "return" the value


def create_dialog(parser, parent=None):
    "Return a gtk dialog with a form extracted from the args of parser"
    dialog = Gtk.Dialog(parser.prog, parent, 0,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK, Gtk.ResponseType.OK))
    dialog.name = parser.prog

    box = dialog.get_content_area()  # here it's where we will put stuff
    box.set_border_width(20)
    box.set_spacing(20)

    box.add(Gtk.Label(parser.description or ''))  # description of program
    args_info = get_args_info(parser.format_help())  # description of arguments
    box.add(create_expander('Arguments', args_info, parent=dialog))
    box.add(Gtk.Separator())  # ----
    box.add(create_grid(parser))  # options

    return dialog


def get_args_info(full_help):
    "Return string with only the description of arguments taken from full_help"
    text = ''
    include = False
    for line in full_help.splitlines(keepends=True):
        if (line.startswith('positional arguments:') or
            line.startswith('optional arguments:')):
            include = True
        if include:
            text += line
    return text


def create_expander(name, text, parent):
    "Return an expander that contains the given text"
    # It knows how to resize its parent when opened/closed too.
    expander = Gtk.Expander()
    expander.set_label(name)
    label = Gtk.Label()
    label.set_markup('<tt>%s</tt>' % text)
    expander.add(label)
    expander.connect('activate', lambda widget: parent.resize(1, 1))
    return expander


def create_grid(parser):
    "Return grid with the options"
    grid = Gtk.Grid(row_spacing=5, column_spacing=5)

    grid.row = 0
    def add(name, widget, helptxt):
        "Add a new row to the grid, that looks like: [name | widget]"
        label = Gtk.Label(name.replace('_', ' '))
        if helptxt:
            label.set_tooltip_text(helptxt)
        grid.attach(label, 0, grid.row, 1, 1)
        grid.attach(widget, 1, grid.row, 1, 1)
        grid.row += 1

    for i, action in enumerate(parser._get_positional_actions()):
        name = '[Argument %d]' % (i + 1)
        add(name, create_widget(action), action.help)

    groups_widgets = [parser._mutually_exclusive_groups, {}]
    for action in parser._get_optional_actions():
        if action.dest != 'help':
            widget = create_widget(action, groups_widgets)
            add(action.dest, widget, action.help)

    return grid


def create_widget(action, groups_widgets=None):
    "Return a widget for input, depending on the action type"
    # action is an argumentparser action object.
    name = action.dest.replace('_', ' ')

    group = get_group(action, groups_widgets[0]) if groups_widgets else None
    if group is not None:
        return create_radio_button(name, group, groups_widgets[1],
                                   active=action.default)
    if action.nargs == 0:
        return create_checkbox(name, action.default)
    elif action.nargs in [1, None]:
        if action.metavar and action.metavar.lower() == 'file':
            return create_filechooser_button(name)
        else:
            return create_text_entry(name, text=action.default)
    elif type(action.nargs) == int:
        return create_multiline(name, nlines=action.nargs)
    elif action.nargs in '?*+':
        return create_multiline(name, nlines=1)


def get_group(action, groups):
    "Return the mutually exclusive group the action belongs to"
    for group in groups:
        if action in group._group_actions:
            return group
    return None  # return None for actions that are not in such a group


def create_radio_button(name, group, widgets, active):
    "Return a radio button and update the widgets dict if appropriate"
    if group in widgets.keys():
        button = Gtk.RadioButton.new_from_widget(widgets[group])
    else:
        button = Gtk.RadioButton()
        widgets[group] = button
    button.name = name
    button.set_active(active)
    return button


def create_multiline(name, nlines):
    "Return a nice scrolling window with space for nlines of values"
    sw = Gtk.ScrolledWindow()
    tv = Gtk.TextView()
    tv.name = name
    tv.set_hexpand(True)
    tv.get_buffer().set_text('\n' * (nlines - 1))
    sw.add(tv)
    return sw


def create_text_entry(name, text):
    entry = Gtk.Entry(text=text)
    entry.name = name
    return entry


def create_checkbox(name, active):
    button = Gtk.CheckButton()
    button.set_active(active)
    button.name = name
    return button


def create_filechooser_button(name):
    "Return a button that opens a dialog to choose a file"
    dialog = Gtk.FileChooserDialog(
        'Select a file', None, Gtk.FileChooserAction.OPEN,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
    add_filter(dialog, 'Any files', patterns=['*'])
    add_filter(dialog, 'Image files', mimes=['image/jpeg', 'image/png'])
    button = Gtk.FileChooserButton('Select a file',
                                   Gtk.FileChooserAction.OPEN,
                                   dialog=dialog)
    button.set_current_folder('.')
    button.name = name
    return button


def add_filter(dialog, name, mimes=[], patterns=[]):
    "Add file filter to gtk dialog based on the given mimes and patterns"
    filter = Gtk.FileFilter()
    filter.set_name(name)
    for mime in mimes:
        filter.add_mime_type(mime)
    for pattern in patterns:
        filter.add_pattern(pattern)
    dialog.add_filter(filter)


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
    add('image', default='', help="a positional argument")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")

    # Now we don't do "args = parser.parse_args()", just write a webpage:
    #print html(parser)

    print(get_argv(parser))
