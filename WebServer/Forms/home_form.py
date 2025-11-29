from datetime import datetime
from WebServer.Forms.form import Form
from Application.inquirer import Inquirer
from Utils.time_format import date_time_fmt, time_ago


class HomeForm(Form):
    """
    Creates the HTML page
    """

    c_HTML_file = r"WebServer/HTML/main.html"

    def __init__(self, inquirer: Inquirer):
        super().__init__(inquirer)

    def render(self):
        # Invullen grootste deel van de HTML-pagina vanuit statische files
        self.handle_html(self.c_HTML_file)

        # intialisatie van de pagina vanuit het model
        if p1_start_time := self.inquirer.get_P1_start_time():
            self.update_element("running_since_date_time", p1_start_time.strftime(date_time_fmt))
            self.update_element("running_for", time_ago(datetime.timestamp(p1_start_time)))

        if p1_recent := self.inquirer.get_recent_data("P1", ["CURRENT_USAGE", "CURRENT_PRODUCTION"]):
            self.update_element("last_P1_meas", time_ago(p1_recent[0]))
            self.update_element("Usage", f"CURRENT_USAGE {p1_recent[1]["CURRENT_USAGE"][0]} {p1_recent[1]["CURRENT_USAGE"][1]}")
            self.update_element("Production", f"CURRENT_PRODUCTION {p1_recent[1]["CURRENT_PRODUCTION"][0]} {p1_recent[1]["CURRENT_PRODUCTION"][1]}")
        if solar_recent := self.inquirer.get_recent_data("Solar", ["SOLAR"]):
            self.update_element("last_Solar_meas", time_ago(solar_recent[0]))
            self.update_element("Solar", f"{solar_recent[1]["SOLAR"][0]} {solar_recent[1]["SOLAR"][1]}")
        self.update_element("data_stores", self.inquirer.data_holder.get_data_stores())
        return self.result
