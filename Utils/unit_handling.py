from __future__ import annotations
from enum import Enum
from itertools import combinations


class Unit(Enum):

    W = 'W'
    kW = 'kW'
    Wh = 'Wh'
    kWh = 'kWh'
    m3 = 'm3'
    m3_per_hr = 'm3/h'

    def __repr__(self):
        return self.value


class UnitHandler:

    Integrated: dict[Unit, Unit] = {Unit.W: Unit.Wh, Unit.kW: Unit.kWh, Unit.m3_per_hr: Unit.m3}
    Conversions: dict[Unit, dict[Unit, float]] = {
        Unit.W: {Unit.kW: 1000.0},
        Unit.Wh: {Unit.kWh: 1000.0}
    }

    @staticmethod
    def common(units: list[Unit], strict: bool) -> list[Unit] | None:
        """Van een lijst units wordt de gemeenschappelijke teruggegeven als ze allen gelijk zijn (strict) of
        overzetbaar in elkaar (strict=False), anders None"""
        res: list[Unit] = []
        assert len(units) > 0
        for unit1, unit2 in combinations(units, 2):
            if strict:
                if unit1 != unit2:
                    return None
                else:
                    if unit1 not in res:
                        res.append(unit1)
            else:
                if UnitHandler.is_convertible(unit1, unit2) is False:
                    return None
                else:
                    if unit1 not in res:
                        res.append(unit1)
                    if unit2 not in res:
                        res.append(unit2)
        return res

    @staticmethod
    def convert_common(values: list[tuple[float, Unit]]) -> list[tuple[float, Unit]]:
        """Een lijst met waarde en eenheid wordt omgezet naar zo'n lijst met allen dezelfde eenheid"""
        if UnitHandler.common([value[1] for value in values], strict=True) is not None:
            return [(value[0], value[1]) for value in values]
        ref_units = UnitHandler.common([value[1] for value in values], strict=False)
        if ref_units is not None and len(ref_units) > 1:
            chosen_unit = None
            convert_poss: dict[Unit, list[float]] = {}
            scores: dict[Unit, int] = {}
            for ref_unit in ref_units:
                convert_poss[ref_unit] = []
                for value in values:
                    convert_poss[ref_unit].append(UnitHandler.convert(value[0], value[1], ref_unit))
                # kies de beste ref_unit
                scores[ref_unit] = 0
                for converted in convert_poss[ref_unit]:
                    if 1.0 < converted < 1000.0:
                        scores[ref_unit] += 1
            max_score = max([score for score in scores.values()])
            for unit in ref_units:
                if scores[unit] == max_score:
                    chosen_unit = unit
                    continue
            assert chosen_unit is not None
            result: list[tuple[float, Unit]] = []
            for value in values:
                result.append((UnitHandler.convert(value[0], value[1], chosen_unit), chosen_unit))
            return result
        else:  # er is maar 1 Unit, retourneer ongewijzigde kopie
            return [(value[0], value[1]) for value in values]


    @staticmethod
    def convert(value: float, from_unit: Unit, to_unit: Unit) -> float:
        if from_unit == to_unit:
            return value
        elif from_unit in UnitHandler.Conversions:
            return value / UnitHandler.Conversions[from_unit][to_unit]
        elif to_unit in UnitHandler.Conversions:
            return value * UnitHandler.Conversions[to_unit][from_unit]
        else:
            raise ValueError

    @staticmethod
    def is_convertible(unit1: Unit, unit2: Unit) -> bool:
        if unit1 == unit2 or\
                (unit1 in UnitHandler.Conversions and unit2 in UnitHandler.Conversions[unit1]) or\
                (unit2 in UnitHandler.Conversions and unit1 in UnitHandler.Conversions[unit2]):
            return True
        else:
            return False

    @staticmethod
    def smallest(units: list[Unit]) -> Unit:
        """Geeft van een lijst units degene met de kleinste eenheid. Pre-conditie is dat ze allen convertible zijn"""
        assert len(units) > 0
        ref_unit = units[0]
        selected_unit = units[0]
        smallest_fac = None
        for unit in units[1:]:
            if unit == ref_unit:
                fac = 1.0
            elif ref_unit in UnitHandler.Conversions:
                fac = UnitHandler.Conversions[ref_unit][unit]
            elif unit in UnitHandler.Conversions:
                fac = 1.0 / UnitHandler.Conversions[unit][ref_unit]
            else:
                raise ValueError
            if smallest_fac and fac < smallest_fac:
                smallest_fac = fac
                selected_unit = unit
        return selected_unit

    @staticmethod
    def integrate(unit: Unit) -> Unit | None:
        try:
            return UnitHandler.Integrated[unit]
        except KeyError:
            return None

    @staticmethod
    def integrate_str(unit: Unit) -> str:
        if res := UnitHandler.integrate(unit):
            return res.value
        else:
            return "-"

    @staticmethod
    def differentiate(unit: Unit) -> Unit | None:
        for key, value in UnitHandler.Integrated.items():
            if value == unit:
                return key
        return None

    @staticmethod
    def differentiate_str(unit: Unit) -> str:
        if res := UnitHandler.differentiate(unit):
            return res.value
        else:
            return "-"


if __name__ == "__main__":
    unit = Unit('W')
    print(f"unit = {unit}, int = {UnitHandler.integrate(unit)}")
    unit = Unit('Wh')
    print(f"unit = {unit}, diff = {UnitHandler.differentiate(unit)}")
    unit = Unit('kW')
    print(f"unit = {unit}, int = {UnitHandler.integrate(unit)}")
    unit = Unit('m3')
    print(f"unit = {unit}, diff = {UnitHandler.differentiate(unit)}")
    unit = Unit('m3/h')
    print(f"unit = {unit}, int = {UnitHandler.integrate(unit)}")

    units = [Unit('W'), Unit('W'), Unit('W')]
    print(f"units = {units}, strict common = {UnitHandler.common(units, strict=True)}")
    print(f"units = {units}, NONstrict common = {UnitHandler.common(units, strict=False)}")

    units = [Unit('W'), Unit('kW'), Unit('W')]
    print(f"units = {units}, strict common = {UnitHandler.common(units, strict=True)}")
    print(f"units = {units}, NONstrict common = {UnitHandler.common(units, strict=False)}")

    lijst = [(1.2, Unit('W')), (12, Unit('W')), (1.2, Unit('kW')), ]
    print(f"lijst = {lijst}, convert_common = {UnitHandler.convert_common(lijst)}")

    lijst = [(0.012, Unit('kW')), (12, Unit('W')), (0.002, Unit('kW')), ]
    print(f"lijst = {lijst}, convert_common = {UnitHandler.convert_common(lijst)}")

    value = 1
    from_unit = Unit('kW')
    to_unit = Unit('W')
    print(f"{value} {from_unit} = {UnitHandler.convert(value, from_unit, to_unit)} {to_unit}")
    value = 1
    from_unit = Unit('W')
    to_unit = Unit('kW')
    print(f"{value} {from_unit} = {UnitHandler.convert(value, from_unit, to_unit)} {to_unit}")

    unit1 = Unit('W')
    unit2 = Unit('kW')
    print(f"{unit1} and {unit2} convertible? {UnitHandler.is_convertible(unit1, unit2)}")
    unit1 = Unit('W')
    unit2 = Unit('W')
    print(f"{unit1} and {unit2} convertible? {UnitHandler.is_convertible(unit1, unit2)}")
    unit1 = Unit('W')
    unit2 = Unit('Wh')
    print(f"{unit1} and {unit2} convertible? {UnitHandler.is_convertible(unit1, unit2)}")

    units = [Unit('W'), Unit('kW')]
    print(f"van de units {units} is de kleinste {UnitHandler.smallest(units)}")
    units = [Unit('W'), Unit('kWh')]
    print(f"van de units {units} is de kleinste {UnitHandler.smallest(units)}")

