from dataclasses import dataclass

from Utils.unit_handling import UnitHandler, Unit


@dataclass
class Grid3phases:
    current_usage: float | None
    current_production: float | None
    unit: Unit | None
    """
    Bepaalt de netto productie/consumptie.
    Positief: er wordt netto afgenomen
    Negatief: er wordt netto teruggeleverd
    """
    @property
    def net_balance(self) -> float | None:
        if self.current_usage is not None and self.current_production is not None:
            return self.current_usage - self.current_production

    @property
    def net_consumption(self) -> float | None:
        if self.net_balance is not None:
            return self.net_balance if self.net_balance > 0.0 else 0.0

    @property
    def net_production(self) -> float | None:
        if self.net_balance is not None:
            return -self.net_balance if self.net_balance < 0.0 else 0.0


def solar_efficiency(solar_value: float, solar_unit: Unit, grid_3phases: Grid3phases) -> float | None:
    """
    Geeft de fractie zon die nuttig wordt ingezet
    """
    if (prod := grid_3phases.net_production) is not None:
        try:
            solar_conv = UnitHandler.convert(solar_value, solar_unit, grid_3phases.unit)
            return (solar_conv - prod) / solar_conv
        except ZeroDivisionError:
            return None
