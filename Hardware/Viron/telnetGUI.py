from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit


class TelnetSessionGUI(QWidget):
    """
    A custom PyQt5 widget representing a Telnet terminal GUI.

    Attributes:
        laser (object): An object representing the laser connection (e.g., a TelnetLaser object).
        terminal_output (QTextEdit): A QTextEdit widget to display the terminal output.
        input_line (QLineEdit): A QLineEdit widget to take input commands from the user.
        telnet_connection: A Telnet connection object.
    """

    def __init__(self, parent=None, laser=None):
        """
        Initializes the TelnetSessionGUI widget.

        Args:
            parent (QWidget): The parent widget to which this widget will be added (default: None).
            laser (object): An object representing the laser connection (default: None).
        """
        super().__init__(parent)
        self.laser = laser
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface of the TelnetSessionGUI widget.
        Sets up the QTextEdit and QLineEdit widgets to create the terminal-like interface.
        """
        self.terminal_output = QTextEdit(self)
        self.terminal_output.setReadOnly(True)

        self.input_line = QLineEdit(self)
        self.input_line.setText("Do not use this unless you have a very good understanding of what you're doing!")
        self.input_line.returnPressed.connect(self.send_command)

        layout = QVBoxLayout(self)
        layout.addWidget(self.terminal_output)
        layout.addWidget(self.input_line)

        self.telnet_connection = None

    def set_laser(self, laser):
        """
        Sets the laser object for the TelnetSessionGUI widget.

        Args:
            laser (object): An object representing the laser connection (e.g., a TelnetLaser object).
        """
        self.laser = laser

    def print_to_terminal(self, text):
        """
        Appends the given text to the terminal output.

        Args:
            text (str): The text to be displayed in the terminal output.
        """
        self.terminal_output.append(">>>" + str(text))

    def send_command(self):
        """
        Handles the command input from the user, sends it to the laser, and displays the command in the terminal.
        """
        # Get command from input and display it, set the input to a blank line
        cmd = self.input_line.text()
        self.terminal_output.append("> " + cmd)
        self.input_line.setText("")

        # Send command to laser and request a response
        if self.laser:
            rtn = self.laser.send_command(cmd, response=True)
            self.terminal_output.append(">>> " + str(rtn).rstrip())