from kivy.clock import Clock
from pisole.consolewidget import SimpleConsoleWidget
# importing all command functions of the project folder into the local module namespace, so they can be executed
# as commands of the module
from commands import *

import pisole.translate as translate
import pisole.message as message
import traceback
import threading
import commands
import inspect
import time
import sys


def help(console, command="", max_column_width=30):
    """
    A function that will provide the user with information about the available commands. prints the list of all commands
    on default and the specific documentation of the command, when passed a name of func object
    :param console: -
    :param command: (string) (func) the command to be helped about
    :return:
    """
    # the functions list will contain tuples (function_name, function)
    functions_list = list(map(lambda x: list(x), inspect.getmembers(commands, inspect.isfunction)))

    # in case the string is empty the help function will print a list of all available commands
    if command == "":
        print_string_list = ["The following commands are available\n\n"]
        # since the list of functions should be properly indented, meaning there should be clearly separated columns,
        # the width of the first column must be calculated by using the length of the longest command as reference of
        # how far it is possible to go
        column_width = 0
        for function in functions_list:
            if len(function[0]) > column_width and len(function[0]) < max_column_width - 2:
                column_width = len(function[0])
        column_width += 2

        # getting the doc string (only the explanation) for every command and replacing the second item of each
        # function_list entry with this string. At this point every second item is the object of the function itself
        # but that isnt needed in this context
        for function in functions_list:
            doc_string = str(inspect.getdoc(function[1]))
            # slicing the docstring, so that it ends before the first parameter is described
            doc_string = doc_string[:doc_string.find("\n:param")]
            doc_string = doc_string.replace("\n", " ")
            function[1] = doc_string

        widget_width = int((console.get_width() / console.get_font_size()) * 1.8)
        column_indent = " " * column_width
        space_left = widget_width - column_width
        print(space_left)
        # adding the function names in bold and enough whitespaces to fill the column before adding the doc strings
        # in gray color
        for function in functions_list:
            print_string_list.append("[color=3AD126]{}[/color]{}".format(function[0], " " * (column_width - len(function[0]))))
            print_string_list.append("[color=808080]")
            print_string_list.append(function[1])
            print_string_list.append("[/color]\n\n")

        console.print_info(''.join(print_string_list))

    else:
        functions_dict = {}
        doc_string = ""
        for function in functions_list:
            functions_dict[function[0]] = function[1]
        if command in functions_dict.keys():
            print_string_list = ["\n\n[color=3AD126]", command, "[/color]\n"]
            doc_string = str(inspect.getdoc(functions_dict[command]))
        elif inspect.isfunction(command):
            print_string_list = ["\n\n[color=3AD126]", str(command.__name__), "[/color]\n"]
            doc_string = str(inspect.getdoc(command))
        else:
            raise NotImplementedError("the command '{}' does not exist".format(command))

        # adding the explanatory string to the list of string to assemble
        print_string_list.append("[color=808080]{}[/color]\n".format(doc_string[:doc_string.find("\n:param")]))

        # splitting it into lines
        doc_string_lines = doc_string.split("\n")
        first_parameter = True
        for line in doc_string_lines:
            if line[:7] == ":param ":
                if not first_parameter:
                    parameter_name = line[7:line[1:].find(":")+1]
                    print_string_list.append("-- {}\n".format(parameter_name))
                else:
                    first_parameter = False
            if line[:8] == ":return:":
                print_string_list.append("returns: [color=808080]{}[/color]".format(line.replace(":return:", "")))

        console.print_info(''.join(print_string_list))


class SimplePisoleConsole(threading.Thread):
    """
    SUMMARY
    This class is a wrapper around the SimpleConsole kivy widget. Once an instance of this class is created, the actual
    widget will bge sored within an variable of the object. The object represents a modular console, that can be
    utilized by nearly any kivy application. The Widget, whose most top layered basis is a Gridlayout, can be used and
    implemented into the application just like any other kivy native widget. The object itself though, which is a Thread
    adds the actual functionality of a console/terminal though. in its main, thread loop the program will constantly
    check for any user input and then proceed to first translate the issued command into a namespace specific python
    syntax, before executing via the python interpreter. The output of the command will then be printed into the output
    window of the console widget.

    THE WIDGET
    The Widget (SimpleConsoleWidget) consists of a input line at the bottom of the grid layout and a much larger
    plain colored output window at the top.
    The InputLine is used to enter the commands to be executed and can mostly be used just like any other input widget.
    The command can be executed by pressing enter with an already entered string. Pressing Tab will expand the input
    widget by an additional line to support multiline python input syntax. Indents must be done manually.
    The Output Window is a Scroll View Container, which gets extended by one additional label widget per separate
    issued input.

    THE SYNTAX
    The syntax os basically the original Python syntax.
    Temporary Variables can be used in the context of a single issued input.
    Python built in functions can be used
    And most importantly every function, that is defined inside a 'commands.py' module, that is located in the same
    file directory layer as the pisole package
    Multiline commands with indent are supported

    :ivar console_widget: (SimpleConsoleWidget) The actual kivy widget representing the console on screen
    """
    def __init__(self):
        # Initializing the threading.Thread super class
        super(SimplePisoleConsole, self).__init__()
        # creating the actual kivy Console Widget, that will be displayed later
        self.console_widget = SimpleConsoleWidget()

    def run(self):

        # The main loop of the Thread, continuesly checking for user input inside the buffer of the widget and executing
        # the respective command functions
        while True:
            if not self.console_widget.is_input_available():
                # just waiting in standby in case there is no input from the user available
                time.sleep(0.001)
            else:
                time.sleep(0.001)
                # saving the user input string into a separate variable to clear the buffer
                input_string = self.console_widget.pop_latest_input(blocking=False)
                self.console_widget.new_command(input_string)
                # translating the user input string, so that the first parameter of every command call is this very
                # pisole object itself, so that the command can properly interact with the ui widget
                translated_input = translate.translate(input_string, "self")
                try:
                    # compiling and then executing the translated version of the user issued input string
                    compiled_input = compile(translated_input, "<string>", "exec")
                    exec(compiled_input)
                except Exception as exception:
                    traceback.print_tb(sys.exc_info()[2])
                    self.print_error(exception)

    def get_widget(self):
        return self.console_widget

    def print_info(self, string):
        info_message = message.InfoMessage(string)
        self.console_widget.println(info_message.get_kivy())

    def print_result(self, string):
        result_message = message.ResultMessage(string)
        self.console_widget.println(result_message.get_kivy())

    def print_error(self, exception):
        error_message = message.ErrorMessage(exception)
        self.console_widget.println(error_message.get_kivy())

    # TODO: add timeout
    def prompt_input(self, prompt_string):
        input_message = message.InputPromptMessage(prompt_string)
        self.console_widget.println(input_message.get_kivy())
        starting_length_buffer = len(self.console_widget.entered_strings_list)
        while True:
            time.sleep(0.0001)
            length_buffer = len(self.console_widget.entered_strings_list)
            if length_buffer < starting_length_buffer:
                starting_length_buffer = length_buffer
            elif length_buffer > starting_length_buffer:
                return self.console_widget.pop_latest_input()

    def get_width(self):
        return self.console_widget.output_window.width

    def get_font_size(self):
        return self.console_widget.get_font_size()

    def _print(self, string):
        self.console_widget.print(string)

    def _println(self, string):
        self.console_widget.println(string)

