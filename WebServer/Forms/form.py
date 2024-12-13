import abc
from Application.inquirer import Inquirer


class Form:
    """
    Abstract base class for creation of HTML-forms.
    It maintains a list of strings containing the HTML-data and supplies generic methods.
    Sublasses should implement a render() method.
    """

    def __init__(self, inquirer: Inquirer):
        self.inquirer = inquirer
        self.result = []  # list of strings

    @abc.abstractmethod
    def render(self):
        pass

    @staticmethod
    def get_html(html_file):
        with open(html_file) as file:
            result = file.read().splitlines()
        return result

    def handle_html(self, html_file):
        self.result = self.get_html(html_file)

    def append(self, list_of_strings):
        for line in list_of_strings:
            self.result.insert(len(self.result) - 1, line)

    def insert(self, list_of_strings, position):
        for iline, line in enumerate(list_of_strings):
            self.result.insert(position + iline, line)

    def update_element(self, element_id, element_value):
        s = ['  <script type="text/javascript">',
             f'    var element = document.getElementById("{element_id}");']
        if isinstance(element_value, bool):
            s.append(f'    element.checked = {"true" if element_value is True else "false"};')
        elif isinstance(element_value, list):  # combobox modifier
            for i, item in enumerate(element_value):
                s.append(f'    element.add(new Option("{item}","{i}"),undefined);')
        else:
            s.append(f'    element.innerHTML = "{element_value}";')
        s.append('  </script>')
        self.append(s)
