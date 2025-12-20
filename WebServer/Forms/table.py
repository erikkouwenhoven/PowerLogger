from WebServer.Forms.form import Form


class HTMLTable(Form):
    """
    Creates a HTML-table
    """
    def __init__(self, hor_header: list[str], ver_header: list[str], data: list[list[str]]):
        super().__init__()
        self.hor_header = hor_header
        self.ver_header = ver_header
        self.data = data
        assert len(data) == len(ver_header)  # number of rows
        for row in data:
            assert len(row) == len(hor_header)

    def render(self):
        # Horizontal header
        self.append(["<tr>", "<th></th>"])
        for header_item in self.hor_header:
            self.append([f"<th>{header_item}</th>"])
        self.append(["<tr>"])
        # Rows with vertical header and data
        for i_row, row in enumerate(self.data):
            self.append(["<tr>", f"<th>{self.ver_header[i_row]}</th>"])
            for item in self.data[i_row]:
                self.append([f"<td>{item}</td>"])
            self.append(["<tr>"])
        #
        return self.result
