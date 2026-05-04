#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Village-Scale Gravity Battery Calculator
Built for the 12-year-old hacker keeping the lights on.

The Math: Energy (Joules) = Mass (kg) x Gravity (9.81) x Height (meters) x Efficiency
"""

import argparse

def calculate_village_battery(mass_kg, height_m, drop_time_minutes, efficiency):
    g = 9.81  # Earth's gravity in m/s^2
    
    # 1. Total Stored Energy (Joules)
    total_energy_joules = mass_kg * g * height_m
    
    # 2. Usable Energy after friction/motor losses
    usable_energy_joules = total_energy_joules * efficiency
    
    # Convert Joules to Watt-hours (Wh) for everyday electronics (1 Wh = 3600 Joules)
    usable_watt_hours = usable_energy_joules / 3600
    
    # 3. Power Output (Watts)
    # Power is energy divided by time (in seconds)
    drop_time_seconds = drop_time_minutes * 60
    power_watts = usable_energy_joules / drop_time_seconds if drop_time_seconds > 0 else 0
    
    return {
        "energy_joules": total_energy_joules,
        "usable_joules": usable_energy_joules,
        "usable_wh": usable_watt_hours,
        "power_watts": power_watts
    }

def print_hacker_guide(mass, height, minutes, eff, results):
    print("\n" + "="*50)
    print(" 🛠️  VILLAGE GRAVITY BATTERY CALCULATOR  🛠️")
    print("="*50)
    print(f"\n[ THE SETUP ]")
    print(f"  * Hanging Mass  : {mass} kg (Like {int(mass/20)} large buckets of water)")
    print(f"  * Drop Height   : {height} meters (Like a {int(height/3)} story building/tree)")
    print(f"  * Drop Time     : {minutes} minutes")
    print(f"  * Generator Eff.: {int(eff*100)}% (Scrap DC motors lose power to friction/heat)")

    print(f"\n[ THE PHYSICS ]")
    print(f"  Total Raw Energy : {results['energy_joules']:,.0f} Joules")
    print(f"  Usable Energy    : {results['usable_joules']:,.0f} Joules ({results['usable_wh']:.2f} Watt-Hours)")
    print(f"  Constant Power   : {results['power_watts']:.2f} Watts")

    print(f"\n[ WHAT CAN IT DO WHILE DROPPING? ]")
    
    # Give practical examples based on the wattage
    if results['power_watts'] >= 5.0:
        phones = int(results['power_watts'] / 5.0)
        print(f"  📱 Slowly charge {phones} smartphone(s)")
    else:
        print("  📱 Not enough steady power to charge a smartphone (needs ~5W).")
        
    leds = int(results['power_watts'] / 0.5)
    if leds > 0:
        print(f"  💡 Light up {leds} bright LED bulbs (0.5W each)")
    else:
        print("  💡 Barely enough for a tiny LED.")
        
    if results['power_watts'] >= 2.0:
        print("  📻 Power a small emergency shortwave radio!")

    print(f"\n[ HOW TO BUILD IT WITH SCRAP ]")
    print("  1. The Pulley  : An old bicycle wheel with the tire removed.")
    print("  2. The Rope    : Sturdy climbing rope or braided fishing line.")
    print("  3. The Weight  : Sandbags, rocks, or sealed jugs of water.")
    print("  4. The Gears   : Use the bike chain to connect the wheel to a smaller gear.")
    print("  5. The Dynamo  : An old DC motor (from a broken toy car or power drill).")
    print("                   Spinning a motor backwards turns it into a generator!")
    print("==================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DIY Gravity Battery Math")
    parser.add_argument("--mass", type=float, default=200.0, help="Mass in kg (e.g. 200 = 10 buckets of water)")
    parser.add_argument("--height", type=float, default=10.0, help="Height in meters")
    parser.add_argument("--minutes", type=float, default=30.0, help="How many minutes it takes to drop to the bottom")
    parser.add_argument("--eff", type=float, default=0.35, help="System efficiency (scraps are usually 0.20 to 0.40)")
    
    args = parser.parse_args()
    
    res = calculate_village_battery(args.mass, args.height, args.minutes, args.eff)
    print_hacker_guide(args.mass, args.height, args.minutes, args.eff, res)
