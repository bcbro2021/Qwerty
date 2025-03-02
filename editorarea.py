from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QFontMetricsF

		
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.line_number_area = LineNumberArea(self)
        
        # Connect events to update the line numbers dynamically
        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_number_area_on_scroll)
        self.cursorPositionChanged.connect(self.viewport().update)

        # Adjust margins initially
        self.update_line_number_width()

    def line_number_width(self):
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().width('9') * digits
    
    def update_tab_size(self):
        """ Dynamically update tab size based on font size """
        metrics = QFontMetricsF(self.font())
        tab_width = metrics.horizontalAdvance(" ") * 4
        self.setTabStopDistance(tab_width)

    def update_line_number_width(self):
        """Adjust the left margin to make space for line numbers."""
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)
        self.line_number_area.update()

    def resizeEvent(self, event):
        """Update line number area when resizing the editor."""
        super().resizeEvent(event)
        rect = self.contentsRect()
        self.line_number_area.setGeometry(QRect(rect.left(), rect.top(), self.line_number_width(), rect.height()))

    def update_line_number_area_on_scroll(self, rect, dy):
        """Keep line numbers in sync with scrolling."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update()

    def line_number_paint_event(self, event):
        """Paint the line numbers in the margin."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e2127"))  # Background color for the line number area

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#abb2bf"))  # Line number color
                painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
