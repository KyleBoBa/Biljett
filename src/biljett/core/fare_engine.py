from __future__ import annotations

from collections import Counter

from biljett.core.models import FareCatalog, FareProductType, FareQuote, FareSelection


def compare_fares(catalog: FareCatalog, days: int, rides_per_day: int = 2) -> FareQuote:
    if days < 1:
        raise ValueError("days must be at least 1")
    if rides_per_day < 1:
        raise ValueError("rides_per_day must be at least 1")

    product_rows: list[tuple[str, str, int, int, int, FareProductType]] = []
    for product in catalog.products:
        effective_price = product.price_sek
        if product.type == FareProductType.SINGLE:
            effective_price = product.price_sek * rides_per_day
        product_rows.append(
            (
                product.code,
                product.name,
                product.duration_days,
                effective_price,
                product.price_sek,
                product.type,
            )
        )

    max_duration = max(duration for _, _, duration, _, _, _ in product_rows)
    max_days = days + max_duration
    infinity = 10**18
    dp = [infinity] * (max_days + 1)
    previous: list[tuple[int, str] | None] = [None] * (max_days + 1)
    unit_prices = {code: unit_price for code, _, _, _, unit_price, _ in product_rows}
    names = {code: name for code, name, _, _, _, _ in product_rows}
    durations = {code: duration for code, _, duration, _, _, _ in product_rows}
    types = {code: kind for code, _, _, _, _, kind in product_rows}
    dp[0] = 0

    for day in range(max_days + 1):
        if dp[day] == infinity:
            continue
        for code, _, duration, effective_price, _, _ in product_rows:
            next_day = day + duration
            if next_day > max_days:
                continue
            candidate_price = dp[day] + effective_price
            if candidate_price < dp[next_day]:
                dp[next_day] = candidate_price
                previous[next_day] = (day, code)

    best_day = min(range(days, max_days + 1), key=lambda index: dp[index])
    chosen_codes: list[str] = []
    current_day = best_day
    while current_day > 0:
        step = previous[current_day]
        if step is None:
            raise RuntimeError("fare reconstruction failed")
        previous_day, code = step
        chosen_codes.append(code)
        current_day = previous_day

    selections: list[FareSelection] = []
    for code, quantity in sorted(Counter(chosen_codes).items()):
        total_price = (
            quantity * unit_prices[code] * rides_per_day
            if types[code] == FareProductType.SINGLE
            else quantity * unit_prices[code]
        )
        selections.append(
            FareSelection(
                code=code,
                name=names[code],
                quantity=quantity,
                unit_price_sek=unit_prices[code],
                covered_days=durations[code] * quantity,
                total_price_sek=total_price,
            )
        )

    explanation = (
        f"Biljett täcker {days} resdagar med lägsta totalpris {dp[best_day]} SEK. "
        f"Lösningen täcker {best_day} dagar totalt och räknar {rides_per_day} resor per dag."
    )

    return FareQuote(
        region=catalog.region,
        profile=catalog.profile,
        requested_days=days,
        covered_days=best_day,
        rides_per_day=rides_per_day,
        total_price_sek=dp[best_day],
        explanation=explanation,
        selections=selections,
        catalog_version=catalog.version,
    )
