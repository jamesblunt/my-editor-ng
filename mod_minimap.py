from gi.repository import GtkSource, Pango, Gdk, Gtk

class Minimap(GtkSource.View):
  def __init__(self, editor):
    GtkSource.View.__init__(self)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    editor.connect('size-allocate', lambda _, rect:
        scroll.set_min_content_width(rect.width / 10))
    scroll.add(self)
    self.modify_font(Pango.FontDescription.from_string('Terminus 5'))
    editor.east_area.pack_start(scroll, True, True, 0)

    editor.connect('view-created', lambda _, view:
        view.connect('notify::buffer', self.switch_buffer))

  def switch_buffer(self, view, _):
    buf = view.get_buffer()
    self.set_buffer(buf)
    buf.connect('notify::cursor-position', self.scroll)

  def scroll(self, buf, _):
    self.scroll_mark_onscreen(buf.get_insert())
