def unit_integrated(unit: str) -> str:
    if '/h' in unit:
        return unit.replace('/h', '')
    return unit + 'h'


def unit_differentiated(unit: str) -> str:
    if unit[-1] == 'h':
        return unit[:-1]
    return unit + '/h'


if __name__ == "__main__":
    unit = 'W'
    print(f"unit = {unit}, diff = {unit_differentiated(unit)}, int = {unit_integrated(unit)}")
    unit = 'Wh'
    print(f"unit = {unit}, diff = {unit_differentiated(unit)}, int = {unit_integrated(unit)}")
    unit = 'm3'
    print(f"unit = {unit}, diff = {unit_differentiated(unit)}, int = {unit_integrated(unit)}")
    unit = 'm3/h'
    print(f"unit = {unit}, diff = {unit_differentiated(unit)}, int = {unit_integrated(unit)}")
