import sys
import os
import shutil
import threading

import highlighter
import editorarea
import rpc

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFileDialog, QTreeView, QSplitter, QFileSystemModel, QShortcut, QMenu, QAction, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt, QDir, QSettings
from PyQt5.QtGui import QIcon, QFontMetricsF

class TextEditorApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("logo.ico"))

        self.setWindowTitle("Qwerty")
        self.setGeometry(100, 100, 800, 600)

        # Create the main layout and set it to a vertical layout
        layout = QVBoxLayout(self)

        # Create the main text editor
        self.text_edit = editorarea.CodeEditor()
        self.text_edit.setPlaceholderText("Code Something.")

        # Create the folder hierarchy view
        self.folder_model = QFileSystemModel()
        self.folder_model.setRootPath(QDir.rootPath())

        # Create the file explorer tree view (initially empty)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.folder_model)
        self.tree_view.setHeaderHidden(True)

        self.tree_view.doubleClicked.connect(self.open_file)

        # Set up the context menu for the tree view
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        # Add the text editor and tree view to the layout
        splitter = QSplitter()
        splitter.addWidget(self.tree_view)
        splitter.addWidget(self.text_edit)
        splitter.setSizes([200, 600])
        layout.addWidget(splitter)

        self.setLayout(layout)

        # Apply dark theme (One Dark background style)
        with open("style.qss", "r") as file:
            data = file.read()
            self.setStyleSheet(data)

        # Set keyboard shortcuts
        self.set_shortcuts()
        self.installEventFilter(self)

        # Set up the Python highlighter for the text editor
        self.highlighter = None

        self.settings = QSettings("lolguy", "Qwerty")  # Use an identifier for your app
        last_folder = self.settings.value("lastOpenedFolder", QDir.homePath())  # Default to home directory
        self.tree_view.setRootIndex(self.folder_model.index(last_folder))

        # discord rpc
        if rpc.rpc_enable:
            rpc.update()

    def closeEvent(self, event):
        if rpc.rpc_enable:
            rpc.close()

    def set_shortcuts(self):
        # Ctrl+F for opening folder
        self.ctrl_f_shortcut = QShortcut(Qt.CTRL + Qt.Key_F, self)
        self.ctrl_f_shortcut.activated.connect(self.open_folder)

        # Ctrl+S for saving file
        self.ctrl_s_shortcut = QShortcut(Qt.CTRL + Qt.Key_S, self)
        self.ctrl_s_shortcut.activated.connect(self.save_file)

        # Ctrl+R for deleting file/folder
        self.ctrl_r_shortcut = QShortcut(Qt.CTRL + Qt.Key_R, self)
        self.ctrl_r_shortcut.activated.connect(self.delete_selected_file)

        # Ctrl+N creating a new file shortcut
        self.ctrl_n_shortcut = QShortcut(Qt.CTRL + Qt.Key_N, self)
        self.ctrl_n_shortcut.activated.connect(self.create_file)
        
        # Ctrl+B for running a file
        self.ctrl_b_shortcut = QShortcut(Qt.CTRL + Qt.Key_B, self)
        self.ctrl_b_shortcut.activated.connect(self.run_file)

    def eventFilter(self, obj, event):
        """Capture keyboard events for font resizing manually."""
        if event.type() == event.KeyPress and event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:  # Handle Ctrl+Plus (including Shift variations)
                self.adjust_font_size(2)
                return True
            elif event.key() == Qt.Key_Minus:  # Handle Ctrl+Minus
                self.adjust_font_size(-2)
                return True
        return super().eventFilter(obj, event)

    def adjust_font_size(self, change):
        """Adjust the font size of QTextEdit dynamically."""
        current_font = self.text_edit.font()
        new_size = max(8, current_font.pointSize() + change)  # Prevent font size going below 8
        current_font.setPointSize(new_size)
        self.text_edit.setFont(current_font)

    def run_file(self):
        if self.current_file.endswith(".py"):
            threading.Thread(target=os.system, args=(f'python "{self.current_file}"',), daemon=True).start()
        else:
            QMessageBox.warning(self, "Error", "No Python file selected to run.")

    def open_folder(self):
        # Open a folder dialog and set the root directory of the tree view
        folder = QFileDialog.getExistingDirectory(self, "Choose Folder", QDir.rootPath())
        if folder:
            # Set the root index to the chosen folder
            self.tree_view.setRootIndex(self.folder_model.index(folder))
            self.settings.setValue("lastOpenedFolder", folder)

    def open_file(self, index):
        # Get the file path from the index clicked
        file_path = self.folder_model.filePath(index)

        if os.path.isfile(file_path):
            # Open the file and read its content
            with open(file_path, "r") as file:
                content = ""
                try:
                    content = file.read()
                except UnicodeDecodeError:
                    QMessageBox.warning(self, "Error: ", f"incorrect unicode format")
                self.text_edit.setPlainText(content)

            # Apply Python syntax highlighting if it's a Python file
            if file_path.endswith(".py"):
                self.highlighter = highlighter.PythonHighlighter(self.text_edit.document())

            # Save changes when closing the application or a save button (not yet added, but can be done)
            self.current_file = file_path

    def save_file(self):
        # Save the current file with the content from QTextEdit
        if hasattr(self, 'current_file') and self.current_file:
            with open(self.current_file, "w") as file:
                file.write(self.text_edit.toPlainText())
        else:
            # If no file is selected, show a file dialog to save
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
            if file_path:
                with open(file_path, "w") as file:
                    file.write(self.text_edit.toPlainText())
                self.current_file = file_path  # Store the file path for future saves

    def show_context_menu(self, position):
        # Create context menu
        context_menu = QMenu(self)

        # Get the clicked index in the tree view
        index = self.tree_view.indexAt(position)
        if index.isValid():
            # If a file or folder is clicked, add delete option
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_file(index))
            context_menu.addAction(delete_action)
        else:
            # If the empty space in the tree view is clicked, add create options
            create_file_action = QAction("Create File", self)
            create_file_action.triggered.connect(self.create_file)
            context_menu.addAction(create_file_action)

            create_folder_action = QAction("Create Folder", self)
            create_folder_action.triggered.connect(self.create_folder)
            context_menu.addAction(create_folder_action)

        # Show the context menu
        context_menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def delete_selected_file(self):
        # Get the currently selected file or folder
        index = self.tree_view.selectedIndexes()
        if not index:
            return  # No file selected

        # Delete the file
        self.delete_file(index[0])

    def delete_file(self, index):
        # Get the file path from the selected index
        file_path = self.folder_model.filePath(index)

        try:
            # Use shutil.rmtree to delete non-empty directories
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)  # This deletes the folder and all its contents
            else:
                os.remove(file_path)  # Remove file
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete the file: {e}")

    def create_file(self):
        # Get the directory path for creating a file
        selected_indexes = self.tree_view.selectedIndexes()

        # If no directory is selected, get the root path from the current tree view
        folder_path = self.get_parent_directory(selected_indexes)

        if folder_path is None:
            return  # Exit if no valid folder path is returned

        # Prompt the user to enter a file name
        file_name, ok = QInputDialog.getText(self, "Create File", "Enter the file name:")

        if ok and file_name:
            file_path = os.path.join(folder_path, file_name)

            # Create the file
            try:
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as file:
                        file.write("")  # Create an empty file
                else:
                    QMessageBox.warning(self, "Error", "File already exists!")
            except OSError:
                QMessageBox.warning(self, "Error", "Cant have special characters in filename!")

    def create_folder(self):
        # Get the directory path for creating a folder
        selected_indexes = self.tree_view.selectedIndexes()

        # If no directory is selected, get the root path from the current tree view
        folder_path = self.get_parent_directory(selected_indexes)

        if folder_path is None:
            return  # Exit if no valid folder path is returned

        # Prompt the user to enter a folder name
        folder_name, ok = QInputDialog.getText(self, "Create Folder", "Enter the folder name:")

        if ok and folder_name:
            new_folder_path = os.path.join(folder_path, folder_name)

            # Create the folder
            if not os.path.exists(new_folder_path):
                os.mkdir(new_folder_path)
            else:
                QMessageBox.warning(self, "Error", "Folder already exists!")

    def get_parent_directory(self, selected_indexes):
        # If no folder is selected, use the root path from the tree view
        if not selected_indexes:
            current_index = self.tree_view.rootIndex()
            return self.folder_model.filePath(current_index)

        file_path = self.folder_model.filePath(selected_indexes[0])

        if os.path.isfile(file_path):  # If it's a file, get the parent directory
            return os.path.dirname(file_path)
        elif os.path.isdir(file_path):  # If it's a directory, return the directory path
            return file_path
        else:
            # If for some reason the item isn't a file or directory, return None
            return None


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("logo.ico"))

    editor = TextEditorApp()
    editor.show()
    sys.exit(app.exec_())
