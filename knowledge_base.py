# ============================================================
#  knowledge_base.py  —  Lightweight JSON-based retrieval
#  No ChromaDB. No ONNX. No 400MB RAM overhead.
#  Drop-in replacement: get_relevant_context() works the same.
# ============================================================

import json
import os
import re

# ── Load JSON once at startup ─────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH = os.path.join(_BASE_DIR, "wandr_indiranagar.json")

with open(_JSON_PATH, "r", encoding="utf-8") as f:
    _HOTEL = json.load(f)["hotel"]

print(f"[KB] Loaded hotel data: {_HOTEL['name']}")

# ── Synonym map — handles natural language variations ─────────
SYNONYMS = {
    # fitness
    "gym": "fitness_center",
    "workout": "fitness_center",
    "exercise": "fitness_center",
    "fitness": "fitness_center",
    "work out": "fitness_center",
    # pool
    "pool": "swimming_pool",
    "swim": "swimming_pool",
    "swimming": "swimming_pool",
    # wifi
    "wifi": "internet",
    "wi-fi": "internet",
    "internet": "internet",
    "broadband": "internet",
    "wi fi": "internet",
    # parking
    "parking": "parking",
    "car park": "parking",
    "park my car": "parking",
    "vehicle": "parking",
    # food
    "breakfast": "food",
    "lunch": "food",
    "dinner": "food",
    "food": "food",
    "restaurant": "food",
    "eat": "food",
    "meal": "food",
    "dining": "food",
    "room service": "food",
    "menu": "food",
    # checkin/checkout
    "check in": "checkin",
    "check-in": "checkin",
    "checkin": "checkin",
    "check out": "checkout",
    "check-out": "checkout",
    "checkout": "checkout",
    "early check": "checkin",
    "late check": "checkout",
    # rooms
    "room": "rooms",
    "rooms": "rooms",
    "suite": "rooms",
    "accommodation": "rooms",
    "bed": "rooms",
    "balcony": "rooms",
    # price
    "price": "pricing",
    "cost": "pricing",
    "rate": "pricing",
    "how much": "pricing",
    "charges": "pricing",
    "tariff": "pricing",
    "fees": "pricing",
    # location
    "location": "location",
    "address": "location",
    "where": "location",
    "directions": "location",
    "metro": "location",
    "airport": "location",
    "how far": "location",
    "distance": "location",
    # nearby
    "nearby": "nearby",
    "around": "nearby",
    "close to": "nearby",
    "walking distance": "nearby",
    "restaurants near": "nearby_restaurants",
    "places to eat": "nearby_restaurants",
    "where to eat": "nearby_restaurants",
    # laundry
    "laundry": "laundry",
    "wash clothes": "laundry",
    "dry cleaning": "laundry",
    "ironing": "laundry",
    # transport
    "cab": "transport",
    "taxi": "transport",
    "uber": "transport",
    "ola": "transport",
    "shuttle": "transport",
    "airport transfer": "transport",
    "auto": "transport",
    # safety
    "safe": "safety",
    "security": "safety",
    "cctv": "safety",
    "night": "safety",
    # pets
    "pet": "pets",
    "dog": "pets",
    "cat": "pets",
    "animal": "pets",
    # smoking
    "smoke": "smoking",
    "smoking": "smoking",
    "cigarette": "smoking",
    # payment
    "payment": "billing",
    "pay": "billing",
    "card": "billing",
    "cash": "billing",
    "upi": "billing",
    "gst": "billing",
    "invoice": "billing",
    "bill": "billing",
    # accessibility
    "wheelchair": "accessibility",
    "disabled": "accessibility",
    "accessible": "accessibility",
    "elevator": "accessibility",
    "lift": "accessibility",
}

# ── Section builders — each returns a text block ─────────────

def _section_general() -> str:
    h = _HOTEL
    addr = h["address"]
    r = h["ratings"]
    return (
        f"Hotel: {h['name']}\n"
        f"Address: {addr['street']}, {addr['city']} - {addr['pincode']}\n"
        f"Type: {h['property_master']['property_type']}\n"
        f"Floors: {h['property_master']['number_of_floors']}, Total Rooms: {h['property_master']['total_rooms']}\n"
        f"Rating: {r['overall_score']}/10 ({r['overall_label']}) based on {r['total_reviews']} reviews\n"
        f"Location Score: {r['category_scores']['location']}/10\n"
        f"Staff Score: {r['category_scores']['staff']}/10\n"
        f"Couple Friendly: Yes\n"
        f"Popular with Families: Yes\n"
        f"Year Opened: {h['property_master']['year_opened']}\n"
        f"Google Maps: {h['property_master']['google_maps_url']}\n"
        f"Website: {h['contact']['website']}\n"
        f"Languages Spoken: {', '.join(h['facilities']['languages_spoken'])}"
    )

def _section_rooms() -> str:
    lines = ["ROOM TYPES & PRICING:"]
    for room in _HOTEL["rooms"]:
        pricing = room.get("pricing", {})
        base = pricing.get("base_price_per_night_inr", "N/A")
        amenities = ", ".join(room.get("amenities", []))
        specs = _HOTEL["room_specs"]
        size_key = room["room_type"].lower().replace(" ", "_")
        size = specs["room_size_sqft"].get(size_key, "N/A")
        lines.append(
            f"- {room['room_type']}: ₹{base}/night | Bed: {room.get('bed_type','N/A')} | "
            f"Size: {size} sqft | Amenities: {amenities}"
        )
    lines.append(f"Bed sizes — Queen: {_HOTEL['room_specs']['bed_dimensions']['queen_bed']}, "
                 f"Single: {_HOTEL['room_specs']['bed_dimensions']['single_bed']}")
    lines.append(f"Mattress: {_HOTEL['room_specs']['mattress_type']}")
    lines.append(f"Blackout curtains: {'Yes' if _HOTEL['room_specs']['blackout_curtains'] else 'No'}")
    lines.append(f"Smart TV: {'Yes' if _HOTEL['room_specs']['smart_tv'] else 'No'}")
    lines.append(f"Hot water: {_HOTEL['room_specs']['hot_water_availability']}")
    return "\n".join(lines)

def _section_pricing() -> str:
    lines = ["PRICING:"]
    for room in _HOTEL["rooms"]:
        pricing = room.get("pricing", {})
        base = pricing.get("base_price_per_night_inr", "N/A")
        weekend = pricing.get("weekend_price_inr", "N/A")
        lines.append(f"- {room['room_type']}: ₹{base}/night (weekday), ₹{weekend}/night (weekend)")
    gst = _HOTEL["billing_details"]["gst_breakdown"]
    lines.append(f"GST: {gst['total_gst_percentage']}% (CGST {gst['cgst_percentage']}% + SGST {gst['sgst_percentage']}%)")
    lines.append(f"Refund timeline: {_HOTEL['billing_details']['refund_timeline_days']} days")
    lines.append(f"Split payment supported: Yes")
    lines.append(f"Corporate billing available: Yes")
    return "\n".join(lines)

def _section_checkin() -> str:
    p = _HOTEL["policies"]
    return (
        f"CHECK-IN / CHECK-OUT:\n"
        f"Check-in: {p['check_in_time']}\n"
        f"Check-out: {p['check_out_time']}\n"
        f"Early check-in: {p.get('early_check_in', 'Subject to availability')}\n"
        f"Late check-out: {p.get('late_check_out', 'Subject to availability')}\n"
        f"Express check-in/check-out: Available\n"
        f"Private check-in/check-out: Available\n"
        f"Walk-in guests allowed: Yes\n"
        f"Online KYC: Yes\n"
        f"Mobile check-in: Yes\n"
        f"Digital check-out: Yes"
    )

def _section_food() -> str:
    f_d = _HOTEL["food_and_dining_details"]
    fac = _HOTEL["facilities"]
    return (
        f"FOOD & DINING:\n"
        f"Restaurant on-site: Yes ({fac['restaurant_note']})\n"
        f"Breakfast timings: {f_d['breakfast_timings']}\n"
        f"Breakfast type: {f_d['breakfast_type']}\n"
        f"Room service: {f_d['room_service_timings']}\n"
        f"Late night food: {'Yes' if f_d['late_night_food_available'] else 'No'}\n"
        f"Complimentary tea/coffee: {'Yes' if f_d['complimentary_tea_coffee'] else 'No'}\n"
        f"Outside food delivery (Swiggy/Zomato) allowed: {'Yes' if f_d['outside_delivery_apps_allowed'] else 'No'}\n"
        f"Outside food and beverages allowed: Yes\n"
        f"RO drinking water: Yes"
    )

def _section_internet() -> str:
    net = _HOTEL["facilities"]["internet"]
    dig = _HOTEL["digital_experience"]
    return (
        f"WIFI & INTERNET:\n"
        f"WiFi available: {'Yes' if net['wifi_available'] else 'No'}\n"
        f"Coverage: {net['wifi_areas']}\n"
        f"Cost: {net['wifi_cost']}\n"
        f"Speed: {dig['wifi_speed_mbps']} Mbps\n"
        f"Backup provider: {dig['backup_internet_provider']}\n"
        f"WhatsApp concierge: Yes\n"
        f"QR room service: Yes"
    )

def _section_parking() -> str:
    p = _HOTEL["facilities"]["parking"]
    pm = _HOTEL["property_master"]
    return (
        f"PARKING:\n"
        f"Available: {'Yes' if p['available'] else 'No'}\n"
        f"Type: {p['type']}\n"
        f"Reservation needed: {'Yes' if p['reservation_needed'] else 'No'}\n"
        f"Parking garage: {'Yes' if p['parking_garage'] else 'No'}\n"
        f"Accessible parking: {'Yes' if p['accessible_parking'] else 'No'}\n"
        f"Capacity: {p['capacity']}\n"
        f"EV charging: {'Yes' if pm['ev_charging'] else 'No'}\n"
        f"Valet parking: {'Yes' if pm['valet_parking'] else 'No'}"
    )

def _section_fitness_pool() -> str:
    fac = _HOTEL["facilities"]
    return (
        f"FITNESS & POOL:\n"
        f"Gym/Fitness center: {'Yes' if fac['fitness_center'] else 'No, we do not have a gym or fitness center at this property.'}\n"
        f"Swimming pool: {'Yes' if fac['swimming_pool'] else 'No, we do not have a swimming pool at this property.'}"
    )

def _section_location() -> str:
    h = _HOTEL
    pm = h["property_master"]
    li = h["location_intelligence"]
    return (
        f"LOCATION:\n"
        f"Address: {h['contact']['address_full']}\n"
        f"Distance from city center: {h['distance_from_city_center_km']} km\n"
        f"Distance from airport: {h['distance_from_airport_km']} km\n"
        f"Airport travel time: {li['airport_travel_time_minutes'][0]}\n"
        f"Nearby landmarks: {', '.join(pm['landmarks'])}\n"
        f"Railway stations: {', '.join(li['railway_station_distance_km'])}\n"
        f"Google Maps: {pm['google_maps_url']}"
    )

def _section_nearby() -> str:
    li = _HOTEL["location_intelligence"]
    nearby = _HOTEL.get("nearby_places", {})
    lines = ["NEARBY PLACES:"]
    if nearby:
        for category, places in nearby.items():
            if isinstance(places, list):
                lines.append(f"{category.replace('_',' ').title()}: {', '.join(str(p) for p in places[:3])}")
    lines.append(f"Nearest hospitals: {', '.join(li['nearest_hospital'][:2])}")
    lines.append(f"Nearest ATMs: {', '.join(li['nearest_atm'][:2])}")
    lines.append(f"Nearest pharmacy: {', '.join(li['nearest_pharmacy'][:2])}")
    lines.append(f"Nearest grocery: {', '.join(li['nearest_grocery_store'][:2])}")
    lines.append(f"Cab access: {li['cab_accessibility'][0]}")
    return "\n".join(lines)

def _section_nearby_restaurants() -> str:
    nearby = _HOTEL.get("nearby_places", {})
    lines = ["NEARBY RESTAURANTS:"]
    found = False
    for key, val in nearby.items():
        if "restaurant" in key.lower() or "dining" in key.lower() or "food" in key.lower():
            if isinstance(val, list):
                for item in val:
                    lines.append(f"- {item}")
                found = True
    if not found:
        lines.append("For nearby restaurant recommendations, please ask our front desk — "
                     "they know the best spots in Indiranagar.")
    return "\n".join(lines)

def _section_transport() -> str:
    li = _HOTEL["location_intelligence"]
    shuttle = _HOTEL["facilities"]["airport_shuttle"]
    return (
        f"TRANSPORT & GETTING AROUND:\n"
        f"Airport shuttle: {'Yes' if shuttle['available'] else 'No'} "
        f"({'additional charge' if shuttle['additional_charge'] else 'free'}, "
        f"request: {shuttle['request']})\n"
        f"Cab availability: {li['cab_accessibility'][0]}\n"
        f"Traffic: {li['traffic_level'][0]}\n"
        f"Railway stations: {', '.join(li['railway_station_distance_km'][:2])}\n"
        f"Airport travel time: {li['airport_travel_time_minutes'][0]}"
    )

def _section_safety() -> str:
    fac = _HOTEL["facilities"]
    li = _HOTEL["location_intelligence"]
    se = _HOTEL["safety_emergency"]
    return (
        f"SAFETY & SECURITY:\n"
        f"Security features: {', '.join(fac['safety_and_security'])}\n"
        f"Safe at night: {li['safe_at_night'][0]}\n"
        f"Female traveler safety: {se['female_traveler_safety_rating']}\n"
        f"Doctor on call: {'Yes' if se['doctor_on_call'] else 'No'}\n"
        f"First aid kit: {'Yes' if se['first_aid_kit_available'] else 'No'}\n"
        f"Emergency contact: {se['emergency_contact_process']}"
    )

def _section_laundry() -> str:
    c = _HOTEL["facilities"]["cleaning_services"]
    return (
        f"LAUNDRY & CLEANING:\n"
        f"Daily housekeeping: {'Yes' if c['daily_housekeeping'] else 'No'}\n"
        f"Laundry service: {'Yes' if c['laundry']['available'] else 'No'} "
        f"({'extra charge' if c['laundry']['additional_charge'] else 'free'})\n"
        f"Dry cleaning: {'Yes' if c['dry_cleaning']['available'] else 'No'} "
        f"({'extra charge' if c['dry_cleaning']['additional_charge'] else 'free'})\n"
        f"Ironing service: {'Yes' if c['ironing_service']['available'] else 'No'} "
        f"({'extra charge' if c['ironing_service']['additional_charge'] else 'free'})\n"
        f"Linen change: {_HOTEL['cleaning_hygiene']['linen_change_frequency']}"
    )

def _section_billing() -> str:
    b = _HOTEL["billing_details"]
    return (
        f"PAYMENT & BILLING:\n"
        f"Accepted: Credit card, Debit card, UPI\n"
        f"GST: {b['gst_breakdown']['total_gst_percentage']}%\n"
        f"Refund timeline: {b['refund_timeline_days']} days\n"
        f"Split payment: {'Yes' if b['split_payment_supported'] else 'No'}\n"
        f"Corporate billing: {'Yes' if b['corporate_billing_available'] else 'No'}\n"
        f"Security deposit: {b['security_deposit'] or 'Not required'}"
    )

def _section_smoking() -> str:
    policies = _HOTEL.get("policies", {})
    rules = _HOTEL.get("house_rules", [])
    smoking_rules = [r for r in rules if "smok" in r.lower()]
    return (
        f"SMOKING POLICY:\n"
        f"Non-smoking throughout: Yes\n"
        f"Designated smoking area: Yes (outdoor)\n"
        f"Rules: {'; '.join(smoking_rules) if smoking_rules else 'Non-smoking property with designated outdoor area'}"
    )

def _section_pets() -> str:
    rules = _HOTEL.get("house_rules", [])
    pet_rules = [r for r in rules if "pet" in r.lower() or "animal" in r.lower()]
    policies = _HOTEL.get("policies", {})
    pets_allowed = policies.get("pets_allowed", False)
    return (
        f"PETS POLICY:\n"
        f"Pets allowed: {'Yes' if pets_allowed else 'No'}\n"
        f"Details: {'; '.join(pet_rules) if pet_rules else 'Pets are not allowed at this property.'}"
    )

def _section_policies() -> str:
    p = _HOTEL["policies"]
    rules = _HOTEL.get("house_rules", [])
    return (
        f"POLICIES & HOUSE RULES:\n"
        f"Check-in: {p['check_in_time']} | Check-out: {p['check_out_time']}\n"
        f"Cancellation: {p.get('cancellation_policy', 'Please check at time of booking')}\n"
        f"Children policy: {p.get('children_policy', 'Children welcome')}\n"
        f"Age restriction: {p.get('age_restriction', 'Guests under 18 must be with parent/guardian')}\n"
        f"House rules: {' | '.join(rules[:6]) if rules else 'Standard hotel policies apply'}"
    )

def _section_accessibility() -> str:
    acc = _HOTEL["facilities"].get("accessibility", [])
    gen = _HOTEL["facilities"].get("general", [])
    lift = "Yes" in str(gen) and "Lift" in str(gen)
    return (
        f"ACCESSIBILITY:\n"
        f"Wheelchair accessible: Yes\n"
        f"Elevator/Lift: Yes\n"
        f"Accessible parking: Yes\n"
        f"Features: {', '.join(acc)}"
    )

def _section_events() -> str:
    ev = _HOTEL["event_services"]
    return (
        f"EVENTS & CELEBRATIONS:\n"
        f"Birthday decorations: {ev['birthday_decorations']}\n"
        f"Anniversary setup: {ev['anniversary_setup']}\n"
        f"Cake arrangement: {ev['cake_arrangement']}\n"
        f"Bachelor parties: Not allowed\n"
        f"Private dining: {ev['private_dining'] or 'Not available'}"
    )

def _section_business() -> str:
    biz = _HOTEL["business_traveler_features"]
    dig = _HOTEL["digital_experience"]
    return (
        f"BUSINESS TRAVELER FEATURES:\n"
        f"Printing: {biz['printing_service']}\n"
        f"Scanning: {biz['scanning_service']}\n"
        f"Meeting room: {biz['meeting_room_available'] or 'Not available'}\n"
        f"Co-working space: {biz['coworking_space'] or 'Not available'}\n"
        f"Weekly/monthly rates: {biz['weekly_rates_available']}\n"
        f"WiFi speed: {dig['wifi_speed_mbps']} Mbps\n"
        f"Workspace-friendly rooms: Yes"
    )

# ── Intent → section mapping ──────────────────────────────────
INTENT_SECTIONS = {
    "fitness_center": [_section_fitness_pool],
    "swimming_pool":  [_section_fitness_pool],
    "internet":       [_section_internet],
    "parking":        [_section_parking],
    "food":           [_section_food],
    "checkin":        [_section_checkin],
    "checkout":       [_section_checkin],
    "rooms":          [_section_rooms],
    "pricing":        [_section_pricing, _section_rooms],
    "location":       [_section_location],
    "nearby":         [_section_nearby, _section_location],
    "nearby_restaurants": [_section_nearby_restaurants, _section_nearby],
    "transport":      [_section_transport, _section_location],
    "safety":         [_section_safety],
    "laundry":        [_section_laundry],
    "billing":        [_section_billing],
    "smoking":        [_section_smoking],
    "pets":           [_section_pets],
    "accessibility":  [_section_accessibility],
    "events":         [_section_events],
    "business":       [_section_business],
}

# ── Core retrieval function ───────────────────────────────────

def get_relevant_context(query: str, top_k: int = 3) -> str:
    """
    Drop-in replacement for ChromaDB get_relevant_context().
    Maps query keywords → relevant JSON sections → context string.
    """
    q = query.lower()
    q = re.sub(r"[^\w\s]", " ", q)  # strip punctuation

    # Resolve synonyms to intents
    matched_intents = set()
    for keyword, intent in SYNONYMS.items():
        if keyword in q:
            matched_intents.add(intent)

    # Collect unique section builders
    builders = []
    seen = set()
    for intent in matched_intents:
        for fn in INTENT_SECTIONS.get(intent, []):
            if fn not in seen:
                builders.append(fn)
                seen.add(fn)

    # Always include general info
    if _section_general not in seen:
        builders.insert(0, _section_general)

    # Cap at top_k + 1 sections (general + top_k relevant)
    builders = builders[:top_k + 1]

    # If nothing matched, return general + policies
    if len(builders) <= 1:
        builders = [_section_general, _section_policies, _section_checkin]

    context_parts = []
    for fn in builders:
        try:
            context_parts.append(fn())
        except Exception as e:
            print(f"[KB] Section error in {fn.__name__}: {e}")

    return "\n\n".join(context_parts)
