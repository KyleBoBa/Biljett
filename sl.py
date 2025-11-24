# Priser för olika biljetter
enkel = 26        # Enkelbiljett
tjugofyra_h = 110 # 24-timmarsbiljett
sju_d = 290       # 7-dagarsbiljett
tre_m = 650       # 30-dagarsbiljett
nio_m = 1880      # 90-dagarsbiljett
ars = 6830        # Årsbiljett

def sl_pris(antal_dagar):
    priser = {
        1: (1, enkel * 2),     # 1 dag: tur och retur
        3: (3, tjugofyra_h),   # 24h-biljetten — endast 1 tillåten
        7: (7, sju_d),
        30: (30, tre_m),
        90: (90, nio_m),
        365: (365, ars)
    }

    max_dur = max(d for d, _ in priser.values())
    max_days = antal_dagar + max_dur

    INF = float("inf")
    dp = [[INF] * 2 for _ in range(max_days + 1)]
    prev = [[None] * 2 for _ in range(max_days + 1)]
    dp[0][0] = 0

    for i in range(max_days + 1):
        for used3 in (0, 1):
            if dp[i][used3] == INF:
                continue
            for typ, (d, pris) in priser.items():
                if typ == 3 and used3 == 1:
                    continue
                ny_dag = i + d
                if ny_dag > max_days:
                    continue
                ny_used3 = used3 or (typ == 3)
                if dp[ny_dag][ny_used3] > dp[i][used3] + pris:
                    dp[ny_dag][ny_used3] = dp[i][used3] + pris
                    prev[ny_dag][ny_used3] = (i, used3, typ)

    best_cost = INF
    best_state = None
    for dag in range(antal_dagar, max_days + 1):
        for used3 in (0, 1):
            if dp[dag][used3] < best_cost:
                best_cost = dp[dag][used3]
                best_state = (dag, used3)

    dag, used3 = best_state
    resultat = []
    while dag > 0:
        i, used3_prev, typ = prev[dag][used3]
        resultat.append(typ)
        dag, used3 = i, used3_prev

    return best_cost, resultat


# ---- Huvudprogram ----

antal = int(input("Hur många dagar behöver du resa med SL? "))

pris, biljetter = sl_pris(antal)

print(f"\nBilligaste pris: {pris} kr")

# Summera biljetter
biljett_namn = {
    1: "1-dag (2 enkelbiljetter)",
    3: "24h-biljett",
    7: "7-dagars",
    30: "30-dagars",
    90: "90-dagars",
    365: "Årsbiljett"
}

print("\nRekommenderade biljetter:")
antal_per_typ = {}
for b in biljetter:
    antal_per_typ[b] = antal_per_typ.get(b, 0) + 1

for typ, antal_st in sorted(antal_per_typ.items()):
    print(f"- {antal_st} st {biljett_namn[typ]}")
