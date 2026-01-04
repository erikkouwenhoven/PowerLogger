from datetime import datetime

from Utils.time_delay import Period
from Utils.unit_handling import Unit
from WebServer.Forms.form import Form
from Application.inquirer import Inquirer, SolarEfficiency
from Utils.time_format import date_time_fmt, time_ago
from WebServer.Forms.table import HTMLTable


class HomeForm(Form):
    """
    Creates the HTML page
    """

    c_HTML_file = r"WebServer/HTML/main.html"

    def __init__(self, inquirer: Inquirer):
        super().__init__()
        self.inquirer = inquirer

    def render(self):
        # Invullen grootste deel van de HTML-pagina vanuit statische files
        self.handle_html(self.c_HTML_file)

        # intialisatie van de pagina vanuit het model
        if p1_start_time := self.inquirer.get_P1_start_time():
            self.update_element("running_since_date_time", p1_start_time.strftime(date_time_fmt))
            self.update_element("running_for", time_ago(datetime.timestamp(p1_start_time)))

        if p1_recent := self.inquirer.get_recent_data("P1", ["CURRENT_USAGE", "CURRENT_PRODUCTION"]):
            self.update_element("last_P1_meas", time_ago(p1_recent.timestamp))
            self.update_element("Usage", f"CURRENT_USAGE {p1_recent.get_value("CURRENT_USAGE")} {p1_recent.get_unit("CURRENT_USAGE")}")
            self.update_element("Production", f"CURRENT_PRODUCTION {p1_recent.get_value("CURRENT_PRODUCTION")} {p1_recent.get_unit("CURRENT_PRODUCTION")}")
        if solar_recent := self.inquirer.get_recent_data("Solar", ["SOLAR"]):
            self.update_element("last_Solar_meas", time_ago(solar_recent.timestamp))
            self.update_element("Solar", f"CURRENT_USAGE {solar_recent.get_value("SOLAR")} {solar_recent.get_unit("SOLAR")}")
        self.update_element("data_stores", self.inquirer.data_holder.get_data_stores())

        self.update_element("performance_table", self.inquirer.data_holder.get_data_stores())
        return self.result

    def get_performance_info(self) -> list[str]:
        """
        Geeft de volgende data
            zon
            terugleveren
            afnemen
            zon-efficientie
        van de volgende periodes
            VALUE
            SUM HOUR
            SUM TODAY
            SUM MONTH
            SUM THISYEAR
        """
        info_now: tuple[list[float | None], Unit] = self.inquirer.get_performance_info(None).get_values_unit()
        table_row_now = [f"{item:.2f} {info_now[1].value}" for item in info_now[0]]
        info_hour: tuple[list[float | None], Unit | None] = self.inquirer.get_performance_info(Period.HOUR).get_values_unit()

        table_row_hour = [f"{self.repr(item)} {info_hour[1].value if info_hour[1] else '-'}" for item in info_hour[0]]
        return HTMLTable(SolarEfficiency.get_labels(), ["Now", str(Period.HOUR)],
                         [table_row_now, table_row_hour]).render()

    @staticmethod
    def repr(value: float | None) -> str:
        return f"{value:.2f}" if value else "-"
