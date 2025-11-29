from dataclasses import dataclass


@dataclass
class Grid3phases:
    usage_1: float
    usage_2: float
    usage_3: float
    prod_1: float
    prod_2: float
    prod_3: float

    """
    Bepaalt de netto productie/consumptie.
    Positief: er wordt netto afgenomen
    Negatief: er wordt netto teruggeleverd
    """
    @property
    def net_balance(self) -> float:
        return self.usage_1 + self.usage_2 + self.usage_3 - self.prod_1 - self.prod_2 - self.prod_3

    @property
    def net_consumption(self) -> float:
        return self.net_balance if self.net_balance > 0.0 else 0.0

    @property
    def net_production(self) -> float:
        return -self.net_balance if self.net_balance < 0.0 else 0.0


def solar_efficiency(solar_value: float, net_balance: float) -> float:
    """
    Geeft de fractie zon die nuttig wordt ingezet
    """
    production = 0.0 if net_balance >= 0.0 else -net_balance
    return (solar_value - production) / solar_value
