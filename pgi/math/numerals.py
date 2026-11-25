"""Place-value reduction for the integer kernel.

Non-negative addition and subtraction are reconstructed from the digits.
The ring operation is a second path. The kernel refuses the step when they disagree.
"""

from __future__ import annotations

_PLACES = (
    "ones",
    "tens",
    "hundreds",
    "thousands",
    "ten-thousands",
    "hundred-thousands",
    "millions",
)


def add_lines(left: int, right: int) -> tuple[str, ...]:
    return add_from_digits(left, right)[1]


def sub_lines(left: int, right: int, result: int) -> tuple[str, ...]:
    if right < 0 or left < right:
        return (f"The result is the exact integer {result}.",)
    return sub_from_digits(left, right)[1]


def add_from_digits(left: int, right: int) -> tuple[int, tuple[str, ...]]:
    width = max(len(str(left)), len(str(right)), 1)
    carry = 0
    weight = 1
    total = 0
    lines: list[str] = []
    for place in range(width):
        digit_left = (left // 10**place) % 10
        digit_right = (right // 10**place) % 10
        summed = digit_left + digit_right + carry
        write = summed % 10
        new_carry = summed // 10
        lines.append(
            f"{_place(place)}: {digit_left}+{digit_right}+carry {carry} = {summed}; "
            f"write {write} carry {new_carry}"
        )
        total += write * weight
        weight *= 10
        carry = new_carry
    if carry:
        lines.append(f"{_place(width)}: leading carry {carry}")
        total += carry * weight
    return total, tuple(lines)


def sub_from_digits(left: int, right: int) -> tuple[int, tuple[str, ...]]:
    width = max(len(str(left)), 1)
    borrow = 0
    weight = 1
    total = 0
    lines: list[str] = []
    for place in range(width):
        digit_left = (left // 10**place) % 10
        digit_right = (right // 10**place) % 10
        available = digit_left - borrow
        took = False
        if available < digit_right:
            available += 10
            took = True
        write = available - digit_right
        next_borrow = 1 if took else 0
        note = " borrow 10" if took else ""
        lines.append(
            f"{_place(place)}: {digit_left}-{digit_right} with incoming borrow {borrow}{note}; "
            f"write {write}"
        )
        total += write * weight
        weight *= 10
        borrow = next_borrow
    if borrow:
        raise ValueError("borrow left the top place")
    return total, tuple(lines)


def mul_from_places(left: int, right: int) -> tuple[int, tuple[str, ...]]:
    if right == 0:
        return 0, (f"Int.mul: {left} * 0 = 0",)
    total = 0
    shift = 1
    rest = right
    place = 0
    lines: list[str] = []
    while rest:
        digit = rest % 10
        rest //= 10
        partial = 0
        for _ in range(digit):
            grown, _ = add_from_digits(partial, left)
            partial = grown
        placed = partial * shift
        lines.append(
            f"{_place(place)} partial: {left}*{digit} = {partial}, shift {place} -> {placed}"
        )
        total, _ = add_from_digits(total, placed)
        shift *= 10
        place += 1
    lines.append(f"Int.mul sum of partials = {total}")
    return total, tuple(lines)


def _place(index: int) -> str:
    if index < len(_PLACES):
        return _PLACES[index]
    return f"10^{index}"
