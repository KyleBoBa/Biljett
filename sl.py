def get_prices(typ):
    typ = typ.lower()
    if typ == "vuxen":
        return {
            "enkel": 43,        # Enkelbiljett
            "tjugofyra_h": 180, # 24-timmarsbiljett
            "sjutva_h": 360,    # 72-timmarsbiljett (används ej i DP ännu)
            "sju_d": 470,       # 7-dagarsbiljett
            "tre_m": 1060,      # 30-dagarsbiljett
            "nio_m": 3070,      # 90-dagarsbiljett
            "ars": 11130,       # Årsbiljett
        }
    elif typ == "discount":
        return {
            "enkel": 26,
            "tjugofyra_h": 110,
            "sjutva_h": 220,
            "sju_d": 290,
            "tre_m": 650,
            "nio_m": 1880,
            "ars": 6830,
        }
    else:
        raise ValueError("Ogiltig biljett typ. Välj 'vuxen' eller 'discount'.")


def sl_pris(antal_dagar, typ):
    """
    Beräkna billigaste pris och biljettkombination för 'antal_dagar'
    för vald typ: 'vuxen' eller 'discount'.
    Logiken är samma som tidigare: 24h-biljetten kan bara användas max en gång.
    """
    p = get_prices(typ)

    # mappar "biljetttyp-nyckel" -> (antal dagar den täcker, pris)
    priser = {
        1: (1, p["enkel"] * 2),      # 1 dag: tur och retur med enkelbiljetter
        3: (3, p["tjugofyra_h"]),    # 24h-biljett (begränsas till max 1 st)
        7: (7, p["sju_d"]),
        30: (30, p["tre_m"]),
        90: (90, p["nio_m"]),
        365: (365, p["ars"])
        # p["sjutva_h"] är definierad men används inte i denna modell ännu
    }

    max_dur = max(d for d, _ in priser.values())
    max_days = antal_dagar + max_dur

    INF = float("inf")
    # dp[dag][used3] – minsta pris för att täcka 'dag' dagar, used3=1 om 24h-biljett redan används
    dp = [[INF] * 2 for _ in range(max_days + 1)]
    prev = [[None] * 2 for _ in range(max_days + 1)]
    dp[0][0] = 0

    for i in range(max_days + 1):
        for used3 in (0, 1):
            if dp[i][used3] == INF:
                continue
            for biljetttyp, (d, pris) in priser.items():
                # Tillåt bara 24h-biljetten (typ == 3) en gång
                if biljetttyp == 3 and used3 == 1:
                    continue
                ny_dag = i + d
                if ny_dag > max_days:
                    continue
                ny_used3 = used3 or (biljetttyp == 3)
                if dp[ny_dag][ny_used3] > dp[i][used3] + pris:
                    dp[ny_dag][ny_used3] = dp[i][used3] + pris
                    prev[ny_dag][ny_used3] = (i, used3, biljetttyp)

    # Hitta billigaste lösning som täcker minst antal_dagar
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
        i, used3_prev, biljetttyp = prev[dag][used3]
        resultat.append(biljetttyp)
        dag, used3 = i, used3_prev

    return best_cost, resultat


def main():
    print("=== SL-biljettkalkylator ===")
    print("Välj biljettyp:")
    print("  1) vuxen")
    print("  2) discount (student, pensionär etc.)")

    typ_val = input("Ange 1 eller 2: ").strip()
    if typ_val == "1":
        typ = "vuxen"
    elif typ_val == "2":
        typ = "discount"
    else:
        print("Ogiltigt val, avslutar.")
        return

    try:
        antal = int(input("Hur många dagar behöver du resa med SL? ").strip())
        if antal <= 0:
            print("Antalet dagar måste vara minst 1.")
            return
    except ValueError:
        print("Du måste skriva ett heltal för antal dagar.")
        return

    pris, biljetter = sl_pris(antal, typ)
    print(f"\nBiljettyp: {typ}")
    print(f"Antal dagar: {antal}")
    print(f"Billigaste pris: {pris} kr")

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

    for typ_id, antal_st in sorted(antal_per_typ.items()):
        print(f"- {antal_st} st {biljett_namn[typ_id]}")

    # Extra: visa hur många dagar som faktiskt täcks
    total_dagar = sum({
        1: 1,
        3: 3,
        7: 7,
        30: 30,
        90: 90,
        365: 365
    }[b] for b in biljetter)
    print(f"\nBiljetterna täcker totalt {total_dagar} dagar (du behöver {antal}).")


if __name__ == "__main__":
    main()
