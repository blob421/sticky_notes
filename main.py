
import gi
import os 
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from db import init_db, save_note, get_notes, get_metadata, delete_note



init_db()
CURRENT_DIR = os.path.dirname(__file__)

with open(os.path.join(CURRENT_DIR, 'styles.css'), 'rb') as f:
    css = f.read()


provider = Gtk.CssProvider()
provider.load_from_data(css)

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

screen = Gdk.Screen.get_default()

screen_width = screen.get_width()
screen_height = screen.get_height()

y = (screen_height - 700) / 2
x = screen_width - 50

class StickyNotes(Gtk.Window):

    def __init__(self):
        super().__init__(title="Sticky Notes")

        self.notes, self.highest_id = get_notes()

        if not self.highest_id:
            save_note(title=" ", content=" ")
            
            self.highest_id = 1

        self.note_ids = [key for key in self.notes.keys()]
        self.locked = True
        self.current_note_id = get_metadata()
        self.set_default_size(450, 700)
        self.move(x - 450, y)
        GLib.timeout_add_seconds(20, self.auto_save)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_decorated(False)
        self.make_layout()

        current_note = self.notes.get(self.current_note_id)
        self.populate_content(current_note.get('title'), current_note.get('content'))
       # self.set_keep_below(True)
        # Overlay: background and foreground
   


    def make_layout(self):
        overlay = Gtk.Overlay()
        self.add(overlay)

        # Paper background
        self.paper = Gtk.DrawingArea()
        self.paper.connect("draw", self.draw_paper)
        overlay.add(self.paper)

        # Content layer
        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10
        )

        content.set_border_width(20)
        overlay.add_overlay(content)

        # Toolbar
        self.toolbar = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=7
        )

        content.pack_start(self.toolbar, False, False, 0)

        for idx, label in enumerate(["⬅️", f"{self.note_ids.index(self.current_note_id) + 1} / {len(self.note_ids)}", "➡️", "+", "🔒", "❌"]):
            button = Gtk.Button(label=label)
            if idx == 1:
                self.notes_counter = button
            self.toolbar.pack_start(button, False, False, 0)
            self.connect_button(idx, button)

        # Editable title
        self.title = Gtk.Entry()
        self.title.set_name("note-title")
        self.title.set_placeholder_text('Title...')

        content.pack_start(self.title, False, True, 0)

        # Text editor
        self.scrollable = Gtk.ScrolledWindow()
        
        self.editor = Gtk.TextView()
       
        self.editor.set_wrap_mode(Gtk.WrapMode.WORD)
        self.scrollable.add(self.editor)


        content.pack_start(self.scrollable, True, True, 0)

        self.connect("destroy", Gtk.main_quit)

    def create_note(self):
        self.auto_save()
        last_id = int(self.note_ids[-1])
        self.notes[last_id + 1] = {'title': " ", 'content': " "}
        self.note_ids.append(last_id + 1)
        self.current_note_id = last_id + 1
        self.title.set_text("")
        buffer = self.editor.get_buffer()
        buffer.set_text("")
        
        self.notes_counter.set_label(f"{len(self.note_ids)} / {len(self.note_ids)}")
        save_note(content=" ", title=" ", create=True, id=self.current_note_id)
     
    def auto_save(self):
        
        title = self.title.get_text()
         
        buffer = self.editor.get_buffer()
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        content = buffer.get_text(start, end, True)

        self.notes[self.current_note_id] = {'title': title, 'content': content}
        save_note(title=title, content=content, id=self.current_note_id)
        GLib.timeout_add_seconds(20, self.auto_save)
    
    def connect_button(self, idx, button):
        if idx in (0, 2):
            direction = 'l' if idx == 0 else 'r'
            button.connect("clicked", lambda btn: self.switch_note(direction=direction))

        elif idx == 3:
            button.connect("clicked", lambda *_: self.create_note())

        elif idx == 4: 
            button.connect("clicked", lambda *_ : self.toggle_lock())

        elif idx == 5:
            button.connect("clicked", lambda *_: self.delete_note())

    def delete_note(self):
        position = self.note_ids.index(self.current_note_id)
        self.note_ids.remove(self.current_note_id)
        del self.notes[self.current_note_id]
        delete_note(id=self.current_note_id)
        self.switch_note(direction='l', delete=True, position=position)


 
    def switch_note(self, direction:str, position = None, delete=False):

        if position is None:
             position = self.note_ids.index(self.current_note_id)

        if not delete:
            self.auto_save()

        if direction == 'r':
           if position == len(self.note_ids) - 1:
              self.current_note_id = self.note_ids[0]
              new_position = 1
           else:
               self.current_note_id = self.note_ids[position + 1]
               new_position = position + 2
        
        if direction == 'l':
            if position == 0:
                new_position = len(self.note_ids)
                self.current_note_id = self.note_ids[-1]
            else:
                self.current_note_id = self.note_ids[position - 1]
                new_position = position
   
        new_note = self.notes.get(self.current_note_id)

        self.notes_counter.set_label(f"{new_position} / {len(self.note_ids)}")

        self.populate_content(new_note.get('title'), new_note.get('content'))

    def populate_content(self, title, content):
        self.title.set_text(title)
        self.editor.get_buffer().set_text(content)

    def toggle_lock(self):

        self.locked = not self.locked

        if self.locked:
            self.set_decorated(False)
        else:
            self.set_decorated(True)


    def draw_paper(self, widget, cr):

        allocation = widget.get_allocation()

        width = allocation.width
        height = allocation.height

        # Yellow paper
        cr.set_source_rgb(0.965, 0.910, 0.660)
        cr.paint()

        # Horizontal ruled lines
        cr.set_source_rgba(0.55, 0.48, 0.30, 0.25)
        cr.set_line_width(1)

        for y in range(176, height, 28):
            cr.move_to(20, y)
            cr.line_to(width - 20, y)
            cr.stroke()


app = StickyNotes()
app.show_all()

Gtk.main()
