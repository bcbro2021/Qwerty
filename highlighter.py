from PyQt5.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtCore import QRegularExpression
import keyword
import builtins

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # One Dark Theme Colors
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#c678dd"))  # Purple for keywords
        self.keyword_format.setFontWeight(QFont.Bold)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#5c6370"))  # Grey for comments
        self.comment_format.setFontItalic(True)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#98c379"))  # Green for strings

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#d19a66"))  # Orange for numbers

        self.variable_format = QTextCharFormat()
        self.variable_format.setForeground(QColor("#e5c07b"))  # Yellow for variables

        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#61afef"))  # Blue for functions

        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor("#56b6c2"))  # Cyan for built-in functions

        self.self_format = QTextCharFormat()
        self.self_format.setForeground(QColor("#e06c75"))  # Light Red for 'self'

        # Define regex patterns
        self.keywords = set(keyword.kwlist)
        self.builtins = set(dir(builtins))  # Get built-in functions

        self.keyword_pattern = QRegularExpression(r"\b(" + "|".join(self.keywords) + r")\b")
        self.comment_pattern = QRegularExpression(r"#.*")  # Single-line comments
        self.string_pattern = QRegularExpression(r"\"\"\".*?\"\"\"|'''(.*?)'''|\"[^\"]*\"|'[^']*'")  # Multi & single-line strings
        self.number_pattern = QRegularExpression(r"\b\d+(\.\d+)?([eE][-+]?\d+)?\b|\b0x[0-9A-Fa-f]+\b|\b0b[01]+\b")  # Decimal, hex, binary

        self.variable_pattern = QRegularExpression(r"\b(?!\d)(\w+)\b(?=\s*=\s*[^=])")  # Variable assignment regex
        self.function_pattern = QRegularExpression(r"\bdef\s+(\w+)\b")  # Function definition regex
        self.builtin_pattern = QRegularExpression(r"\b(" + "|".join(self.builtins) + r")\b")  # Built-in functions regex
        self.variable_usage_pattern = QRegularExpression(r"\b(?!\d)(\w+)\b(?=\s*\()")  # Variable usage regex (e.g., var.func())
        self.self_pattern = QRegularExpression(r"\bself\b")  # 'self' keyword regex

    def highlightBlock(self, text):
        """ Applies syntax highlighting to the given block of text """

        # 1. Highlight Comments (first to prevent other highlights)
        comment_match = self.comment_pattern.match(text)
        if comment_match.hasMatch():
            self.setFormat(comment_match.capturedStart(), comment_match.capturedLength(), self.comment_format)
            return  # Skip processing other patterns in comment lines

        # 2. Highlight Strings (before everything else, so nothing inside strings gets highlighted)
        string_ranges = []
        string_match = self.string_pattern.globalMatch(text)
        while string_match.hasNext():
            match = string_match.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.string_format)
            string_ranges.append((match.capturedStart(), match.capturedEnd()))  # Store string positions

        def is_inside_string(position):
            """ Helper function to check if a position is inside a string """
            return any(start <= position < end for start, end in string_ranges)

        # 3. Highlight Keywords (ONLY if they are not inside a string)
        keyword_match = self.keyword_pattern.globalMatch(text)
        while keyword_match.hasNext():
            match = keyword_match.next()
            if not is_inside_string(match.capturedStart()):
                self.setFormat(match.capturedStart(), match.capturedLength(), self.keyword_format)

        # 4. Highlight Numbers (ONLY if they are not inside a string)
        number_match = self.number_pattern.globalMatch(text)
        while number_match.hasNext():
            match = number_match.next()
            if not is_inside_string(match.capturedStart()):
                self.setFormat(match.capturedStart(), match.capturedLength(), self.number_format)

        # 5. Highlight Function Definitions (ONLY if not inside a string)
        function_match = self.function_pattern.globalMatch(text)
        while function_match.hasNext():
            match = function_match.next()
            if not is_inside_string(match.capturedStart()):
                self.setFormat(match.capturedStart(), match.capturedLength(), self.function_format)

        # 6. Highlight Variables in Assignments (ONLY if not inside a string)
        variable_match = self.variable_pattern.globalMatch(text)
        while variable_match.hasNext():
            match = variable_match.next()
            variable_name = match.captured(1)
            if not is_inside_string(match.capturedStart()) and variable_name not in self.keywords and variable_name not in self.builtins:
                self.setFormat(match.capturedStart(), match.capturedLength(), self.variable_format)

        # 7. Highlight Built-in Functions (ONLY if not inside a string)
        builtin_match = self.builtin_pattern.globalMatch(text)
        while builtin_match.hasNext():
            match = builtin_match.next()
            if not is_inside_string(match.capturedStart()):
                self.setFormat(match.capturedStart(), match.capturedLength(), self.builtin_format)

        # 8. Highlight Variable Usage in Function Calls (ONLY if not inside a string)
        variable_usage_match = self.variable_usage_pattern.globalMatch(text)
        while variable_usage_match.hasNext():
            match = variable_usage_match.next()
            variable_name = match.captured(1)
            if not is_inside_string(match.capturedStart()) and variable_name not in self.keywords and variable_name not in self.builtins:
                self.setFormat(match.capturedStart(), match.capturedLength(), self.variable_format)

        # 9. Highlight 'self' keyword in classes (ONLY if not inside a string)
        self_match = self.self_pattern.globalMatch(text)
        while self_match.hasNext():
            match = self_match.next()
            if not is_inside_string(match.capturedStart()):
                self.setFormat(match.capturedStart(), match.capturedLength(), self.self_format)
