import datetime as dt

def get_prices(typ):
    typ = typ.lower()
    if typ == "vuxen":
        return {
            "enkel": 43,        # Enkelbiljett
            "tjugofyra_h": 180, # 24-timmarsbiljett
            "sjutva_h": 360,    # 72-timmarsbiljett
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
    och biljettyp 'vuxen' eller 'discount'.
    """
    priser = get_prices(typ)

    # biljettyp -> (antal dagar den täcker, pris)
    biljetter = {
        "enkel": (1, priser["enkel"] * 2),      # 2 enkelresor per dag (tur/retur)
        "24h":   (1, priser["tjugofyra_h"]),    # 24-timmarsbiljett
        "72h":   (3, priser["sjutva_h"]),       # 72-timmarsbiljett
        "7d":    (7, priser["sju_d"]),
        "30d":   (30, priser["tre_m"]),
        "90d":   (90, priser["nio_m"]),
        "365d":  (365, priser["ars"]),
    }

    max_dur = max(d for d, _ in biljetter.values())
    max_days = antal_dagar + max_dur  # tillåt att vi täcker lite mer än n dagar

    INF = float("inf")
    dp = [INF] * (max_days + 1)
    prev = [None] * (max_days + 1)   # för rekonstruktion (föregående dag, biljett-nyckel)
    dp[0] = 0

    for i in range(max_days + 1):
        if dp[i] == INF:
            continue
        for key, (d, pris) in biljetter.items():
            ny_dag = i + d
            if ny_dag > max_days:
                continue
            if dp[ny_dag] > dp[i] + pris:
                dp[ny_dag] = dp[i] + pris
                prev[ny_dag] = (i, key)

    # hitta billigaste lösning som täcker MINST antal_dagar
    best_cost = INF
    best_day = None
    for dag in range(antal_dagar, max_days + 1):
        if dp[dag] < best_cost:
            best_cost = dp[dag]
            best_day = dag

    # rekonstruera biljetter
    resultat = []
    dag = best_day
    while dag > 0:
        i, key = prev[dag]
        resultat.append(key)
        dag = i

    return best_cost, resultat


def berakna_resdagar_med_datum():
    """
    Frågar användaren efter start- och slutdatum samt om helger ska räknas.
    Returnerar antal resdagar, startdatum, slutdatum.
    """
    idag = dt.date.today()
    print(f"\nLämna startdatum tomt för att använda dagens datum ({idag.isoformat()}).")

    start_str = input("Startdatum (YYYY-MM-DD): ").strip()
    if start_str == "":
        start = idag
    else:
        start = dt.date.fromisoformat(start_str)

    slut_str = input("Sista dag du behöver resa (YYYY-MM-DD): ").strip()
    slut = dt.date.fromisoformat(slut_str)

    if slut < start:
        raise ValueError("Slutdatum kan inte vara före startdatum.")

    inkludera_helg = input("Räkna med helger? (j/n): ").strip().lower()
    rakna_helg = (inkludera_helg == "j")

    # räkna resdagar
    resdagar = 0
    current = start
    while current <= slut:
        if rakna_helg:
            resdagar += 1
        else:
            # weekday(): 0 = måndag, ..., 6 = söndag
            if current.weekday() < 5:  # måndag–fredag
                resdagar += 1
        current += dt.timedelta(days=1)

    return resdagar, start, slut, rakna_helg


def main():
    print("=== SL-biljettkalkylator ===")
    print("Välj biljettyp:")
    print("\t1) vuxen")
    print("\t2) discount (pensionär/ungdom/student)")

    typ_val = input("Ange 1 eller 2: ").strip()
    if typ_val == "1":
        typ = "vuxen"
    elif typ_val == "2":
        typ = "discount"
    else:
        print("Ogiltigt val, avslutar.")
        return

    print("\nHur vill du ange perioden?")
    print("\t1) Ange direkt hur många dagar du behöver resa")
    print("\t2) Ange start- och slutdatum (med val om helger ska räknas)")

    valg = input("Ange 1 eller 2: ").strip()

    if valg == "1":
        try:
            antal = int(input("Hur många dagar behöver du resa med SL? ").strip())
            if antal <= 0:
                print("Antalet dagar måste vara minst 1.")
                return
            info_text = None
        except ValueError:
            print("Du måste skriva ett heltal för antal dagar.")
            return

    elif valg == "2":
        try:
            antal, start, slut, rakna_helg = berakna_resdagar_med_datum()
        except ValueError as e:
            print(f"Fel: {e}")
            return

        if antal == 0:
            print("Inga resdagar enligt dina val (troligen helger bortvalda).")
            return

        helg_text = "med helger" if rakna_helg else "endast vardagar"
        info_text = (
            f"Period: {start.isoformat()} till {slut.isoformat()} ({helg_text}), "
            f"totalt {antal} resdagar."
        )
    else:
        print("Ogiltigt val, avslutar.")
        return

    pris, biljetter = sl_pris(antal, typ)
    print(f"\nBiljettyp: {typ}")
    if info_text:
        print(info_text)
    else:
        print(f"Antal dagar: {antal}")
    print(f"Billigaste pris: {pris} kr")

    biljett_namn = {
        "enkel": "1 dag (2 enkelbiljetter)",
        "24h":   "24-timmarsbiljett",
        "72h":   "72-timmarsbiljett",
        "7d":    "7-dagarsbiljett",
        "30d":   "30-dagarsbiljett",
        "90d":   "90-dagarsbiljett",
        "365d":  "Årsbiljett",
    }

    print("\nRekommenderade biljetter:")
    antal_per_typ = {}
    for b in biljetter:
        antal_per_typ[b] = antal_per_typ.get(b, 0) + 1

    for key, antal_st in sorted(antal_per_typ.items(), key=lambda x: x[0]):
        print(f"- {antal_st} st {biljett_namn[key]}")

    # visa hur många dagar biljetterna täcker
    priser_tmp = get_prices(typ)
    biljetter_info = {
        "enkel": (1, priser_tmp["enkel"] * 2),
        "24h":   (1, priser_tmp["tjugofyra_h"]),
        "72h":   (3, priser_tmp["sjutva_h"]),
        "7d":    (7, priser_tmp["sju_d"]),
        "30d":   (30, priser_tmp["tre_m"]),
        "90d":   (90, priser_tmp["nio_m"]),
        "365d":  (365, priser_tmp["ars"]),
    }
    total_dagar = sum(biljetter_info[b][0] for b in biljetter)
    print(f"\nBiljetterna täcker totalt {total_dagar} dagar (du behöver {antal}).\n")


if __name__ == "__main__":
    main()
