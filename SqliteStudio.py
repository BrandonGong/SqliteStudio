from os import path

import kivy
from kivy.app import App
from kivy.factory import Factory

from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

import sqlite3

class LoadDialog(BoxLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    default_path = StringProperty(".")

class ObjectExplorer(BoxLayout):
    database_name = StringProperty(None)
    con = ObjectProperty(None)
    def set_connection(self, database_name, connection):
        if self.con is None:
            self.database_name = database_name
            self.con = connection

    def load_schema(self):
        if self.con is None:
            return
            
        self.clear_widgets()
        tv = TreeView(root_options={'text':self.database_name})
        # Get list of tables
        for table in self.get_tables():
            table_node = tv.add_node(TreeViewLabel(text=table))
            col_node = tv.add_node(TreeViewLabel(text="Columns"),table_node)
            for column in self.get_columns(table):
                tv.add_node(TreeViewLabel(text=column),col_node)

        self.add_widget(tv)

    def get_tables(self):
        try:
            r = self.con.execute("SELECT name FROM sqlite_schema WHERE type = 'table'")
            return (t[0] for t in r.fetchall())
        except Exception as ex:
            print(ex)
            return []

    def get_columns(self,table):
        try:
            r = self.con.execute(f"SELECT * FROM {table} LIMIT 0")
            return (c[0] for c in r.description)
        except Exception as ex:
            print(ex)
            return []
class TableHeader(Label):
    pass
class TableRow(TextInput):
    pass
class Results(BoxLayout):
    grid = ObjectProperty(None)

    def populate_results(self,results):
        columns = results.description
        data = results.fetchall()
        self.grid.cols = len(results.description)
        self.grid.rows = len(data) + 1
        self.grid.clear_widgets()
        for col in columns:
            self.grid.add_widget(TableHeader(text=col[0]))
        
        for row in data:
            for value in row:
                self.grid.add_widget(TableRow(text= value and str(value) or 'Null'))

class MainWindow(Widget):
    sql_text = StringProperty(None) # SQL text
    object_explorer = ObjectProperty(None) # Object explorer widget
    results = ObjectProperty(None)
    connection = ObjectProperty(None) # Sqlite Connection

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content  = LoadDialog(load=self.load_database, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load_database(self,file):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        try:
            # connect to database        
            self.connection = sqlite3.connect(file)
            # Populate table and columns list
            self.object_explorer.set_connection(path.basename(file),self.connection)
            self.object_explorer.load_schema()
        except Exception as ex:
            self.connection.close()
            self.connection = None
            print(ex)

        self.dismiss_popup()

    def run_query(self): 
        if not self.connection:
            return
        try:
            results = self.connection.execute(self.sql_text)
            self.results.populate_results(results)
            self.connection.commit()
        except Exception as ex:
            self.connection.rollback()
            print(ex)

    def _keyboard_closed(self):
         pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'f5':
            self.run_query()
        return True

class SqliteStudioApp(App):
    def build(self):
        return MainWindow()


if __name__ == '__main__':
    Factory.register('LoadDialog',cls=LoadDialog)
    SqliteStudioApp().run()