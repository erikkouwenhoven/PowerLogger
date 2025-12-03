from dataclasses import dataclass


@dataclass
class Grid3phases:
    current_usage: float
    current_production: float
    """
    Bepaalt de netto productie/consumptie.
    Positief: er wordt netto afgenomen
    Negatief: er wordt netto teruggeleverd
    """
    @property
    def net_balance(self) -> float:
        return self.current_usage - self.current_production

    @property
    def net_consumption(self) -> float:
        return self.net_balance if self.net_balance > 0.0 else 0.0

    @property
    def net_production(self) -> float:
        return -self.net_balance if self.net_balance < 0.0 else 0.0


def solar_efficiency(solar_value: float, grid_3phases: Grid3phases) -> float:
    """
    Geeft de fractie zon die nuttig wordt ingezet
    """
    return (solar_value - grid_3phases.net_production) / solar_value
