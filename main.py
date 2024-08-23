import sys
import json
import datetime
from PyQt5.QtWidgets import ( # type: ignore
    QApplication, QMainWindow, QTextEdit, QAction, QFileDialog,
    QPlainTextEdit, QWidget, QVBoxLayout, QPushButton, QToolBar, QMessageBox
)
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QPainter, QFont # type: ignore
from PyQt5.QtCore import Qt, QRegExp, QRect, QRectF, QSize # type: ignore
import subprocess


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        self.create_rule(['def', 'class', 'import', 'from', 'as', 'return', 'if', 'elif', 'else', 
                          'while', 'for', 'break', 'continue', 'try', 'except', 'finally', 
                          'raise', 'with', 'lambda', 'yield'], QColor("blue"))

        self.create_rule([r'#.*'], QColor("green"))

        self.create_rule([r'"[^"]*"', r"'[^']*'"], QColor("red"))

        self.create_rule([r'\b\d+(\.\d*)?\b'], QColor("orange"))

        self.create_rule([r'\bdef\s+\w+', r'\bclass\s+\w+'], QColor("cyan"))

    def create_rule(self, patterns, color):
        format = QTextCharFormat()
        format.setForeground(color)
        for pattern in patterns:
            self.highlighting_rules.append((QRegExp(pattern), format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(40)

    def sizeHint(self):
        return QSize(self.width(), self.editor.fontMetrics().height() * self.editor.blockCount())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(40, 40, 40))
        block = self.editor.firstVisibleBlock()
        while block.isValid():
            block_rect = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset())
            if not block_rect.intersects(QRectF(event.rect())):
                block = block.next()
                continue
            block_number = block.blockNumber() + 1
            painter.setPen(QColor(160, 160, 160))
            painter.drawText(QRect(0, int(block_rect.top()), self.width(), int(block_rect.height())),
                             Qt.AlignRight, str(block_number))
            block = block.next()






class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = PythonSyntaxHighlighter(self)
        self.line_number_area = LineNumberArea(self)
        self.setStyleSheet("background-color: #2e2e2e; color: #dcdcdc;")
        self.set_font_properties()
        self.setLayoutMargins()
        self.blockCountChanged.connect(self.update_line_number_area)
        self.updateRequest.connect(self.handle_update_request) 

    def set_font_properties(self):
        font = QFont('Consolas', 12)
        self.setFont(font)

    def setLayoutMargins(self):

        self.setViewportMargins(40, 0, 0, 0) 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_line_number_area()

    def handle_update_request(self, rect):

        if isinstance(rect, (QRect, QRectF)):
            self.update_line_number_area(rect)
        else:
            print(f"Unexpected type for rect in updateRequest: {type(rect)}")

            print(f"Value of rect: {rect}")

    def update_line_number_area(self, rect=None):
        if rect is None:

            cr = self.contentsRect()
            self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), 40, cr.height()))
            self.line_number_area.update()
        else:

            if isinstance(rect, QRect):
                rect = QRectF(rect) 
            elif not isinstance(rect, QRectF):
                pass # xddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
                return 
            self.line_number_area.update(0, int(rect.y()), self.line_number_area.width(), int(rect.height()))







class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('CoolCode')
        self.setGeometry(100, 100, 800, 600)
        self.editor = CodeEditor()
        self.editor.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF;")  # Dark mode
        self.setCentralWidget(self.editor)
        self.create_actions()
        self.create_toolbar()

        self.highlighter = PythonSyntaxHighlighter(self.editor.document())

    def create_actions(self):
        self.run_action = QAction('Run', self)
        self.run_action.triggered.connect(self.run_code)
        
        self.save_action = QAction('Save', self)
        self.save_action.triggered.connect(self.save_file)
        
        self.open_action = QAction('Open', self)
        self.open_action.triggered.connect(self.open_file)
        
        self.undo_action = QAction('Undo', self)
        self.undo_action.triggered.connect(self.editor.undo)
        
        self.redo_action = QAction('Redo', self)
        self.redo_action.triggered.connect(self.editor.redo)
        
        self.about_action = QAction('About', self)
        self.about_action.triggered.connect(self.show_credits)

    def create_toolbar(self):
        toolbar = self.addToolBar('Main Toolbar')
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addAction(self.about_action) 

    def run_code(self):
        code = self.editor.toPlainText()
        try:
            output = subprocess.check_output(['python', '-c', code], stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output

        output_window = QMainWindow(self)
        output_window.setWindowTitle('Output')
        output_widget = QTextEdit()
        output_widget.setPlainText(output)
        output_widget.setReadOnly(True)
        output_window.setCentralWidget(output_widget)
        output_window.show()

    def save_file(self):
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save File', f'{current_time}.py', 'Python Files (*.py)')
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.editor.toPlainText())

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Python Files (*.py);;Text Files (*.txt)')
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    self.editor.setPlainText(file.read())
            except UnicodeDecodeError:
                try:
                    with open(file_name, 'r', encoding='latin-1') as file:
                        self.editor.setPlainText(file.read())
                except Exception as e:
                    print(f"Error opening file: {e}")

    def show_credits(self):
        QMessageBox.information(self, 'About', 'CoolCode Editor\n\nVersion 1.0\nCreated by Sabisa324\n\nsory if something no wok im jus tryin me best\nhttps://discord.gg/ATUM87pqKG')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())