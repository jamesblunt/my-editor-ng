from gi.repository import Gtk

class Move:
  def __init__(self):

    self.emit('bind-command-key', 'j', lambda view, n: self.move_line(view, n))
    self.emit('bind-command-key', 'k', lambda view, n: self.move_line(view, n, backward = True))
    self.emit('bind-command-key', 'h', lambda view, n: self.move_char(view, n, backward = True))
    self.emit('bind-command-key', 'l', lambda view, n: self.move_char(view, n))
    self.emit('bind-command-key', 'f', self.make_char_locator())
    self.emit('bind-command-key', 'F', self.make_char_locator(backward = True))
    self.emit('bind-command-key', ';', self.locate_last)
    self.emit('bind-command-key', 's', lambda view: self.make_two_char_locator(view))
    self.emit('bind-command-key', 'S', lambda view: self.make_two_char_locator(view, backward = True))
    self.emit('bind-command-key', 'g g', self.move_to_line)
    self.emit('bind-command-key', 'G', self.move_to_end)
    self.emit('bind-command-key', 'r', self.move_to_line_end)
    self.emit('bind-command-key', 'R', self.move_to_line_start)
    self.emit('bind-command-key', '[', lambda view: self.move_to_empty_line(view, backward = True))
    self.emit('bind-command-key', ']', lambda view: self.move_to_empty_line(view))

    self.connect('buffer-created',
        lambda _, buf: buf.connect('notify::cursor-position', 
          lambda buf, _: self.update_offset(buf)))

  def update_offset(self, buf):
    if buf.attr.get('freeze', False): return
    buf.attr['current_offset'] = buf.get_iter_at_mark(buf.get_insert()).get_line_offset()

  def move_mark(self, buf, it):
    if self.selection_mode == self.NONE:
      buf.place_cursor(it)
    else:
      buf.move_mark(buf.get_insert(), it)

  def move_line(self, view, n, backward = False):
    if n == 0: n = 1
    buf = view.get_buffer()
    it = buf.get_iter_at_mark(buf.get_insert())
    if not backward:
      for i in range(n): view.forward_display_line(it)
    else:
      for i in range(n): view.backward_display_line(it)
    bytes_in_line = it.get_bytes_in_line()
    offset = buf.attr['current_offset']
    if bytes_in_line <= buf.attr['current_offset']:
      offset = bytes_in_line - 1
    if offset > 0:
      it.set_line_offset(offset)
    buf.attr['freeze'] = True
    self.move_mark(buf, it)
    view.scroll_mark_onscreen(buf.get_insert())
    buf.attr['freeze'] = False

  def move_char(self, view, n, backward = False):
    if n == 0: n = 1
    buf = view.get_buffer()
    it = buf.get_iter_at_mark(buf.get_insert())
    if not backward:
      for i in range(n): it.forward_char()
    else:
      for i in range(n): it.backward_char()
    self.move_mark(buf, it)
    view.scroll_mark_onscreen(buf.get_insert())

  def locate_last(self, view):
    if 'last_locate_func' in view.attr:
      view.attr['last_locate_func'](view)

  def locate_search(self, view, s, backward = False):
    buf = view.get_buffer()
    it = buf.get_iter_at_mark(buf.get_insert())
    orig = it.copy()
    if backward:
      it = it.backward_search(s, 0, buf.get_start_iter())
    else:
      it.forward_char()
      it = it.forward_search(s, 0, buf.get_end_iter())
    if it: 
      self.move_mark(buf, it[0])
      view.scroll_mark_onscreen(buf.get_insert())
      return True
    else: 
      self.move_mark(buf, orig)

  def make_char_locator(self, backward = False):
    handler = {}
    def make(c):
      if backward:
        def f(view):
          if self.locate_search(view, c, backward = True):
            view.attr['last_locate_func'] = f
        return f
      else:
        def f(view):
          if self.locate_search(view, c):
            view.attr['last_locate_func'] = f
        return f
    for i in range(0x20, 0x7F):
      handler[chr(i)] = make(chr(i))
    return handler

  def make_two_char_locator(self, view, backward = False):
    def step1(ev):
      s1 = chr(ev.get_keyval()[1])
      def step2(ev):
        s = s1 + chr(ev.get_keyval()[1])
        if backward:
          def f(view):
            if self.locate_search(view, s, backward = True):
              view.attr['last_locate_func'] = f
          f(view)
        else:
          def f(view):
            if self.locate_search(view, s):
              view.attr['last_locate_func'] = f
          f(view)
      return step2
    return step1

  def move_to_line(self, view, n):
    buf = view.get_buffer()
    it = buf.get_start_iter()
    if n > 0:
      it.set_line(n - 1)
    self.move_mark(buf, it)
    view.scroll_mark_onscreen(buf.get_insert())

  def move_to_end(self, view):
    buf = view.get_buffer()
    self.move_mark(buf, buf.get_end_iter())
    view.scroll_mark_onscreen(buf.get_insert())

  def move_to_line_start(self, view):
    buf = view.get_buffer()
    it = buf.get_iter_at_mark(buf.get_insert())
    it.set_line_offset(0)
    self.move_mark(buf, it)
    view.scroll_mark_onscreen(buf.get_insert())

  def move_to_line_end(self, view):
    buf = view.get_buffer()
    it = buf.get_iter_at_mark(buf.get_insert())
    it.forward_to_line_end()
    self.move_mark(buf, it)
    view.scroll_mark_onscreen(buf.get_insert())

  def move_to_empty_line(self, view, backward = False):
    buf = view.get_buffer()
    it = buf.get_iter_at_mark(buf.get_insert())
    if backward: f = it.backward_line
    else: f = it.forward_line
    ret = f()
    while ret and it.get_bytes_in_line() != 1:
      ret = f()
    self.move_mark(buf, it)
    view.scroll_mark_onscreen(buf.get_insert())
