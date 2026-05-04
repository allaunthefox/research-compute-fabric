#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
The Survival Engine: Dust Bowl Salvage Tech
Built for when the crops fail and you need topsoil/food using scrap metal, sunlight, and a car battery.

Phase 1: Grab moisture from the air.
Phase 2: Split it with rusty solar panels and a spark.
Phase 3: Smash the remaining air (Nitrogen) into topsoil food.
"""
import argparse

def calculate_survival_loop(scrap_solar_w, days_running):
    # Extremely low efficiencies because a starving kid is building this with rusty pipes
    solar_to_elec_eff = 0.10     # Cracked PV panels
    water_capture_eff = 0.05     # A cold metal pipe in the shade at night
    elec_to_h2_eff = 0.40        # Running wires through salt water in a glass jar (Electrolysis)
    haber_scrap_eff = 0.01       # Using a car jack as a makeshift pressure pump for Haber
    
    # 1. Total Daily Power Harvest (Roughly 6 hours of usable daylight)
    daily_watt_hours = scrap_solar_w * 6 * solar_to_elec_eff
    
    # 2. Water Harvesting (assuming ~1 Liter (1000g) of moisture condenses per 100 Wh of cooling)
    water_grams_per_day = (daily_watt_hours / 100) * 1000 * water_capture_eff
    
    # 3. Crack the water into Hydrogen and Oxygen (roughly 9 grams water -> 1g H2)
    # Constrained by our terrible electrical efficiency
    max_h2_from_elec = (daily_watt_hours * elec_to_h2_eff) / 50.0  # ~50 Wh to make 1g H2 terribly
    h2_grams_per_day = min(water_grams_per_day / 9.0, max_h2_from_elec)
    
    # 4. Scrap-Metal Fertilizer (Haber-Bosch in a reinforced iron pipe heated by a campfire)
    # 3g H2 + ~14g N2 (from air) -> 17g Ammonia/Fertilizer precursor
    fert_grams_per_day = (h2_grams_per_day / 3.0) * 17.0 * haber_scrap_eff
    
    # 5. Food Yield (Assuming 1 gram of nitrogen fertilizer yields ~50 grams of potato/corn over a season)
    biomass_grams_per_day = fert_grams_per_day * 50.0
    calories = (biomass_grams_per_day / 100.0) * 86.0  # ~86 calories per 100g of potato
    
    total_calories = calories * days_running
    
    return {
        "water_g": water_grams_per_day,
        "h2_g": h2_grams_per_day,
        "fert_g": fert_grams_per_day,
        "food_g": biomass_grams_per_day,
        "cals": calories,
        "total_cals": total_calories
    }

def print_survival_guide(watts, days, res):
    print("\n" + "!"*50)
    print(" 🛠️  THE DUST BOWL SURVIVAL ENGINE  🛠️")
    print("!"*50)
    print("If the sky is dry and the ground is dead. Build this.")
    print(f"\n[ SCRAP INPUTS ]")
    print(f"  * Scavenged Solar Panels : {watts} Watts (Cracked but working)")
    print(f"  * Runtime                : {days} Days out in the sun")
    
    print(f"\n[ DAILY OUTPUT - SCRAP METAL EFFICIENCY ]")
    print(f"  💧 Water Pulled From Air : {res['water_g']:.1f} grams (A few sips)")
    print(f"  ⚡ Hydrogen Gas Made     : {res['h2_g']:.1f} grams")
    print(f"  🌱 Raw Fertilizer Dust   : {res['fert_g']:.2f} grams")
    
    print(f"\n[ THE DIFFERENCE BETWEEN LIFE AND DEATH ]")
    print(f"  🥔 Expected Crop Yield   : {res['food_g']:.1f} grams of potatoes grown per day of running this")
    print(f"  🔥 Caloric Output        : {res['cals']:.0f} Calories per day")
    print(f"  🗓️ Total Food Over {days} days: {int(res['total_cals'])} Calories")
    
    if res['cals'] < 1000:
        print(f"\n  [!] WARNING: YOU ARE SLOWLY STARVING. Scavenge {int(1000/max(res['cals'],1))}x more solar panels.")
    else:
        print(f"\n  [+] YOU LIVE. Keep the engine running.")
    print("!"*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dust Bowl Maker Protocol")
    parser.add_argument("--watts", type=float, default=200.0, help="Total watts of broken solar panels found")
    parser.add_argument("--days", type=int, default=30, help="How many days you run it before harvest")
    args = parser.parse_args()
    res = calculate_survival_loop(args.watts, args.days)
    print_survival_guide(args.watts, args.days, res)
