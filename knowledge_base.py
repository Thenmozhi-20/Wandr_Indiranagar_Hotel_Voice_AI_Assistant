# ============================================================
#  knowledge_base.py  —  JSON-based knowledge retrieval
#  Fixed to match actual wandr_indiranagar.json structure
# ============================================================

import json
import os
import re

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH = os.path.join(_BASE_DIR, "wandr_indiranagar.json")

with open(_JSON_PATH, "r", encoding="utf-8") as f:
    _HOTEL = json.load(f)["hotel"]

print(f"[KB] Loaded hotel data: {_HOTEL['name']}")

# ── Synonym map ───────────────────────────────────────────────
SYNONYMS = {
    "gym": "fitness_center", "workout": "fitness_center",
    "exercise": "fitness_center", "fitness": "fitness_center",
    "pool": "swimming_pool", "swim": "swimming_pool", "swimming": "swimming_pool",
    "wifi": "internet", "wi-fi": "internet", "internet": "internet",
    "wi fi": "internet", "broadband": "internet",
    "parking": "parking", "car park": "parking", "park my car": "parking",
    "breakfast": "food", "lunch": "food", "dinner": "food", "food": "food",
    "restaurant": "food", "eat": "food", "meal": "food", "dining": "food",
    "room service": "food", "menu": "food",
    "check in": "checkin", "check-in": "checkin", "checkin": "checkin",
    "check out": "checkout", "check-out": "checkout", "checkout": "checkout",
    "early check": "checkin", "late check": "checkout",
    "room": "rooms", "rooms": "rooms", "suite": "rooms",
    "accommodation": "rooms", "bed": "rooms", "balcony": "rooms",
    "types of room": "rooms", "room type": "rooms", "room types": "rooms",
    "price": "pricing", "cost": "pricing", "rate": "pricing",
    "how much": "pricing", "charges": "pricing", "tariff": "pricing",
    "location": "location", "address": "location", "where": "location",
    "directions": "location", "metro": "location", "airport": "location",
    "how far": "location", "distance": "location",
    "nearby": "nearby", "around": "nearby", "close to": "nearby",
    "walking distance": "nearby",
    "restaurants near": "nearby_restaurants", "places to eat": "nearby_restaurants",
    "where to eat": "nearby_restaurants",
    "laundry": "laundry", "wash clothes": "laundry", "dry cleaning": "laundry",
    "cab": "transport", "taxi": "transport", "uber": "transport",
    "ola": "transport", "shuttle": "transport", "airport transfer": "transport",
    "safe": "safety", "security": "safety", "cctv": "safety",
    "pet": "pets", "dog": "pets", "cat": "pets", "animal": "pets",
    "smoke": "smoking", "smoking": "smoking", "cigarette": "smoking",
    "payment": "billing", "pay": "billing", "card": "billing",
    "cash": "billing", "gst": "billing", "invoice": "billing", "bill": "billing",
    "wheelchair": "accessibility", "disabled": "accessibility",
    "accessible": "accessibility", "elevator": "accessibility", "lift": "accessibility",
    "hospital": "nearby", "pharmacy": "nearby", "atm": "nearby",
    "bus stand": "location", "bus stop": "location", "railway": "transport",
    "station": "transport", "train": "transport",
    "police": "nearby", "police station": "nearby",
    "medical": "nearby", "medicals": "nearby", "pharmacist": "nearby",
    "chemist": "nearby", "drug store": "nearby",
    "mall": "nearby", "shopping": "nearby", "supermarket": "nearby",
    "grocery": "nearby", "petrol": "nearby", "fuel": "nearby",
    "first aid": "safety", "doctor": "safety", "emergency": "safety",
    "celebrate": "events", "birthday": "events", "anniversary": "events",
    "honeymoon": "events", "decoration": "events",
    "contact": "contact", "phone": "contact", "email": "contact",
    "call": "contact", "reach": "contact", "number": "contact",
    "amenities": "amenities", "facilities available": "amenities",
    "what do you offer": "amenities", "features": "amenities",
    "review": "reviews", "rating": "reviews", "feedback": "reviews",
    "guest review": "reviews", "what do guests say": "reviews",
    "walk in": "booking_ops", "no show": "booking_ops",
    "modify booking": "booking_ops", "change booking": "booking_ops",
    "attraction": "area_info", "places to visit": "area_info",
    "tourist": "area_info", "sightseeing": "area_info",
    "upgrade": "personalization", "loyalty": "personalization",
    "returning guest": "personalization", "discount": "personalization",
    "business": "business", "meeting": "business", "print": "business",
    "couple": "policies", "unmarried": "policies", "pets allowed": "pets",
}

# ── Section builders ──────────────────────────────────────────

def _section_general() -> str:
    h = _HOTEL
    addr = h["address"]
    r = h["ratings"]
    pm = h["property_master"]
    return (
        f"Hotel: {h['name']}\n"
        f"Address: {addr['street']}, {addr['city']} - {addr['pincode']}\n"
        f"Type: {pm['property_type']}\n"
        f"Floors: {pm['number_of_floors']}, Total Rooms: {pm['total_rooms']}\n"
        f"Rating: {r['overall_score']}/10 ({r['overall_label']}) based on {r['total_reviews']} reviews\n"
        f"Couple Friendly: Yes (unmarried couples allowed with valid ID)\n"
        f"Popular with Families: Yes\n"
        f"Year Opened: {pm['year_opened']}\n"
        f"Google Maps: {pm['google_maps_url']}\n"
        f"Website: wandrhotels.com\n"
        f"Languages Spoken: {', '.join(h['facilities']['languages_spoken'])}\n"
        f"Landmarks nearby: {', '.join(pm['landmarks'])}"
    )

def _section_rooms() -> str:
    lines = ["ROOM TYPES & PRICING:"]
    for room in _HOTEL["rooms"]:
        rtype = room.get("room_type", "N/A")
        bed = room.get("bed_type", "N/A")
        status = room.get("availability_status", "N/A")
        amenities = ", ".join(room.get("amenities", []))
        pricing_list = room.get("pricing", [])
        if isinstance(pricing_list, list) and len(pricing_list) > 0:
            p = pricing_list[0]
            price = f"₹{p.get('price_per_night_INR', 'N/A')}/night ({p.get('plan','Room Only')})"
            if len(pricing_list) > 1:
                p2 = pricing_list[1]
                price += f" | ₹{p2.get('price_per_night_INR', 'N/A')}/night ({p2.get('plan','With Breakfast')})"
        else:
            price = "Sold Out / Check website"
        specs = _HOTEL.get("room_specs", {})
        size_key = rtype.lower().replace(" ", "_")
        size = specs.get("room_size_sqft", {}).get(size_key, "N/A")
        lines.append(
            f"- {rtype}: {price} | Bed: {bed} | Size: {size} sqft | "
            f"Status: {status} | Amenities: {amenities}"
        )
    rs = _HOTEL.get("room_specs", {})
    bd = rs.get("bed_dimensions", {})
    lines.append(f"Queen bed size: {bd.get('queen_bed', 'N/A')}")
    lines.append(f"Single bed size: {bd.get('single_bed', 'N/A')}")
    lines.append(f"Mattress: {rs.get('mattress_type', 'N/A')}")
    lines.append(f"Blackout curtains: {'Yes' if rs.get('blackout_curtains') else 'No'}")
    lines.append(f"Smart TV: {'Yes' if rs.get('smart_tv') else 'No'}")
    lines.append(f"Hot water: {rs.get('hot_water_availability', 'N/A')}")
    return "\n".join(lines)

def _section_pricing() -> str:
    lines = ["PRICING:"]
    for room in _HOTEL["rooms"]:
        rtype = room.get("room_type", "N/A")
        pricing_list = room.get("pricing", [])
        if isinstance(pricing_list, list) and len(pricing_list) > 0:
            for p in pricing_list:
                lines.append(
                    f"- {rtype} ({p.get('plan','N/A')}): "
                    f"₹{p.get('price_per_night_INR','N/A')}/night "
                    f"(original ₹{p.get('original_price_INR','N/A')}, "
                    f"saving ₹{p.get('discount_INR','N/A')})"
                )
        else:
            lines.append(f"- {rtype}: Sold Out / Check website")
    b = _HOTEL.get("billing_details", {})
    gst = b.get("gst_breakdown", {})
    lines.append(f"GST: {gst.get('total_gst_percentage', 12)}% on room tariff")
    lines.append(f"Refund timeline: {b.get('refund_timeline_days', 7)} days")
    lines.append(f"Split payment: Yes | Corporate billing: Yes")
    lines.append(f"Payment methods: {', '.join(_HOTEL.get('payment_methods', ['Card', 'Cash']))}")
    return "\n".join(lines)

def _section_checkin() -> str:
    hr = _HOTEL.get("house_rules", {})
    ci = hr.get("check_in", {})
    co = hr.get("check_out", {})
    dig = _HOTEL.get("digital_experience", {})
    return (
        f"CHECK-IN / CHECK-OUT:\n"
        f"Check-in: from {ci.get('from', '13:00')}\n"
        f"Check-out: until {co.get('until', '11:00')}\n"
        f"Early check-in: {ci.get('early_check_in', 'Subject to availability at additional cost')}\n"
        f"Late check-out: {co.get('late_check_out', 'Subject to availability')}\n"
        f"Note: {ci.get('note', 'Advance notice of arrival time required')}\n"
        f"Express check-in/check-out: Available\n"
        f"Private check-in/check-out: Available\n"
        f"Walk-in guests: Allowed\n"
        f"Mobile check-in: {'Yes' if dig.get('mobile_check_in') else 'No'}\n"
        f"Digital check-out: {'Yes' if dig.get('digital_check_out') else 'No'}\n"
        f"Online KYC: {'Yes' if dig.get('online_kyc') else 'No'}"
    )

def _section_food() -> str:
    fd = _HOTEL.get("food_and_dining_details", {})
    fac = _HOTEL.get("facilities", {})
    bf = _HOTEL.get("breakfast", {})
    return (
        f"FOOD & DINING:\n"
        f"Restaurant on-site: Yes (serves breakfast, lunch, and dinner)\n"
        f"Breakfast timings: {fd.get('breakfast_timings', 'Morning')}\n"
        f"Lunch timings: {fd.get('lunch_timings', 'Afternoon')}\n"
        f"Dinner timings: {fd.get('dinner_timings', 'Evening')}\n"
        f"Breakfast type: {fd.get('breakfast_type', 'South Indian Veg & Non-Veg')}\n"
        f"Breakfast options: {', '.join(bf.get('options', []))}\n"
        f"Room service: {fd.get('room_service_timings', '24 Hours')}\n"
        f"Late night food: {'Yes' if fd.get('late_night_food_available') else 'No'}\n"
        f"Complimentary tea/coffee: {'Yes' if fd.get('complimentary_tea_coffee') else 'No'}\n"
        f"Outside food/Swiggy/Zomato allowed: Yes\n"
        f"RO drinking water: Yes"
    )

def _section_internet() -> str:
    net = _HOTEL["facilities"]["internet"]
    dig = _HOTEL.get("digital_experience", {})
    return (
        f"WIFI & INTERNET:\n"
        f"WiFi: {net.get('wifi_cost','Free')} in {net.get('wifi_areas','all areas')}\n"
        f"Speed: {dig.get('wifi_speed_mbps', 100)} Mbps\n"
        f"Backup provider: {dig.get('backup_internet_provider', 'Available')}\n"
        f"WhatsApp concierge: {'Yes' if dig.get('whatsapp_concierge') else 'No'}"
    )

def _section_parking() -> str:
    p = _HOTEL["facilities"]["parking"]
    return (
        f"PARKING:\n"
        f"Available: {'Yes' if p.get('available') else 'No'}\n"
        f"Type: {p.get('type', 'Free private parking on site')}\n"
        f"Reservation needed: {'Yes' if p.get('reservation_needed') else 'No'}\n"
        f"Garage: {'Yes' if p.get('parking_garage') else 'No'}\n"
        f"Accessible parking: {'Yes' if p.get('accessible_parking') else 'No'}\n"
        f"Capacity: {p.get('capacity', 'At least 2 cars inside the property')}"
    )

def _section_fitness_pool() -> str:
    fac = _HOTEL["facilities"]
    return (
        f"FITNESS & POOL:\n"
        f"Swimming pool: {'Yes' if fac.get('swimming_pool') else 'No, we do not have a swimming pool at this property.'}\n"
        f"Fitness center/Gym: {'Yes' if fac.get('fitness_center') else 'No, we do not have a gym or fitness center at this property.'}"
    )

def _section_location() -> str:
    h = _HOTEL
    pm = h["property_master"]
    li = h.get("location_intelligence", {})
    return (
        f"LOCATION:\n"
        f"Address: {h['address']['street']}, {h['address']['city']} - {h['address']['pincode']}\n"
        f"Distance from city center: {h.get('distance_from_city_center_km', 4.7)} km\n"
        f"Distance from airport: {h.get('distance_from_airport_km', 33)} km\n"
        f"Airport travel time: {li.get('airport_travel_time_minutes', ['~65 minutes'])[0]}\n"
        f"Landmarks: {', '.join(pm.get('landmarks', []))}\n"
        f"Google Maps: {pm.get('google_maps_url', 'See wandrhotels.com')}\n"
        f"Nearest hospitals: {', '.join(li.get('nearest_hospital', [])[:2])}\n"
        f"Nearest pharmacy: {', '.join(li.get('nearest_pharmacy', [])[:2])}\n"
        f"Nearest ATM: {', '.join(li.get('nearest_atm', [])[:2])}\n"
        f"Cab access: {li.get('cab_accessibility', ['Uber and Ola available'])[0]}"
    )

def _section_nearby() -> str:
    li = _HOTEL.get("location_intelligence", {})
    nearby = _HOTEL.get("nearby_places", [])
    top = [p["name"] for p in nearby[:8]] if isinstance(nearby, list) else []
    return (
        f"NEARBY PLACES:\n"
        f"Nearest hospitals: {', '.join(li.get('nearest_hospital', [])[:3])}\n"
        f"Nearest pharmacy/medicals: {', '.join(li.get('nearest_pharmacy', [])[:3])}\n"
        f"Nearest ATM: {', '.join(li.get('nearest_atm', [])[:2])}\n"
        f"Nearest grocery: {', '.join(li.get('nearest_grocery_store', [])[:2])}\n"
        f"Nearest police station: {', '.join(li.get('nearest_police_station', [])[:2])}\n"
        f"Nearest petrol bunk: {', '.join(li.get('nearest_petrol_bunk', [])[:2])}\n"
        f"Landmarks: {', '.join(_HOTEL['property_master'].get('landmarks', []))}\n"
        f"Nearby places: {', '.join(top)}"
    )

def _section_nearby_restaurants() -> str:
    nearby = _HOTEL.get("nearby_places", [])
    if not isinstance(nearby, list):
        return "NEARBY RESTAURANTS:\nFor nearby restaurant recommendations, please ask our front desk."
    food_keywords = ["restaurant", "cafe", "café", "kitchen", "food", "dine",
                     "bistro", "grill", "bar", "brew", "eat", "pizza", "burger"]
    restaurants = [
        p["name"] for p in nearby
        if any(kw in p.get("name", "").lower() for kw in food_keywords)
    ]
    lines = ["NEARBY RESTAURANTS:"]
    if restaurants:
        for r in restaurants[:8]:
            lines.append(f"- {r}")
    else:
        lines.append("Please ask our front desk for nearby restaurant recommendations.")
    return "\n".join(lines)

def _section_transport() -> str:
    li = _HOTEL.get("location_intelligence", {})
    shuttle = _HOTEL["facilities"].get("airport_shuttle", {})
    return (
        f"TRANSPORT:\n"
        f"Airport shuttle: {'Yes' if shuttle.get('available') else 'No'} "
        f"({'extra charge' if shuttle.get('additional_charge') else 'free'}, "
        f"request: {shuttle.get('request', 'after booking')})\n"
        f"Cab: {li.get('cab_accessibility', ['Uber and Ola available'])[0]}\n"
        f"Railway stations: {', '.join(li.get('railway_station_distance_km', [])[:2])}\n"
        f"Airport travel time: {li.get('airport_travel_time_minutes', ['~65 minutes'])[0]}\n"
        f"Note: There is no bus stand information available — please contact front desk."
    )

def _section_safety() -> str:
    fac = _HOTEL["facilities"]
    li = _HOTEL.get("location_intelligence", {})
    se = _HOTEL.get("safety_emergency", {})
    return (
        f"SAFETY & SECURITY:\n"
        f"Security: {', '.join(fac.get('safety_and_security', []))}\n"
        f"Safe at night: {li.get('safe_at_night', ['Yes'])[0]}\n"
        f"Female traveler safety: {se.get('female_traveler_safety_rating', 'Excellent')}\n"
        f"Doctor on call: {'Yes' if se.get('doctor_on_call') else 'No'}\n"
        f"First aid kit: {'Yes' if se.get('first_aid_kit_available') else 'No'}\n"
        f"Emergency contact: {se.get('emergency_contact_process', '24/7 front desk')}"
    )

def _section_laundry() -> str:
    c = _HOTEL["facilities"]["cleaning_services"]
    return (
        f"LAUNDRY & CLEANING:\n"
        f"Daily housekeeping: {'Yes' if c.get('daily_housekeeping') else 'No'}\n"
        f"Laundry: {'Yes' if c.get('laundry', {}).get('available') else 'No'} (extra charge)\n"
        f"Dry cleaning: {'Yes' if c.get('dry_cleaning', {}).get('available') else 'No'} (extra charge)\n"
        f"Ironing service: {'Yes' if c.get('ironing_service', {}).get('available') else 'No'} (extra charge)\n"
        f"Linen change: {_HOTEL.get('cleaning_hygiene', {}).get('linen_change_frequency', 'On request')}"
    )

def _section_billing() -> str:
    b = _HOTEL.get("billing_details", {})
    methods = _HOTEL.get("payment_methods", [])
    gst = b.get("gst_breakdown", {})
    return (
        f"PAYMENT & BILLING:\n"
        f"Accepted methods: {', '.join(methods)}\n"
        f"GST: {gst.get('total_gst_percentage', 12)}%\n"
        f"Refund timeline: {b.get('refund_timeline_days', 7)} days\n"
        f"Split payment: {'Yes' if b.get('split_payment_supported') else 'No'}\n"
        f"Corporate billing: {'Yes' if b.get('corporate_billing_available') else 'No'}"
    )

def _section_smoking() -> str:
    hr = _HOTEL.get("house_rules", {})
    sm = hr.get("smoking", {})
    return (
        f"SMOKING POLICY:\n"
        f"Smoking allowed: {'Yes' if sm.get('allowed') else 'No'}\n"
        f"Designated smoking area: {'Yes (outdoor)' if sm.get('designated_smoking_area') else 'No'}\n"
        f"Property is non-smoking throughout."
    )

def _section_pets() -> str:
    hr = _HOTEL.get("house_rules", {})
    pets = hr.get("pets", {})
    return (
        f"PETS POLICY:\n"
        f"Pets allowed: {'Yes' if pets.get('allowed') else 'No'}\n"
        f"Details: Pets are not allowed at this property."
    )

def _section_policies() -> str:
    hr = _HOTEL.get("house_rules", {})
    ci = hr.get("check_in", {})
    co = hr.get("check_out", {})
    age = hr.get("age_restriction", {})
    ch = hr.get("children_policy", {})
    fp = _HOTEL.get("fine_print", [])
    return (
        f"POLICIES & HOUSE RULES:\n"
        f"Check-in: from {ci.get('from', '13:00')} | Check-out: until {co.get('until', '11:00')}\n"
        f"Cancellation: {hr.get('cancellation_prepayment', 'Varies by room type')}\n"
        f"Children: Welcome. Age {age.get('minimum_check_in_age', 18)}+ to check in independently.\n"
        f"Under 18: Must be with parent/guardian\n"
        f"Pets: Not allowed\n"
        f"Parties/events: Not allowed (no bachelor/bachelorette parties)\n"
        f"Unmarried couples: Allowed with valid ID\n"
        f"Outside food: Allowed\n"
        f"Visitors: Allowed\n"
        f"Fine print: {' | '.join(fp[:4]) if fp else 'Standard hotel policies apply'}"
    )

def _section_accessibility() -> str:
    acc = _HOTEL["facilities"].get("accessibility", [])
    return (
        f"ACCESSIBILITY:\n"
        f"Wheelchair accessible: Yes\n"
        f"Elevator/Lift: Yes\n"
        f"Accessible parking: Yes\n"
        f"Features: {', '.join(acc)}"
    )

def _section_events() -> str:
    ev = _HOTEL.get("event_services", {})
    return (
        f"EVENTS & CELEBRATIONS:\n"
        f"Birthday decorations: {ev.get('birthday_decorations', 'Via third-party vendors only')}\n"
        f"Anniversary setup: {ev.get('anniversary_setup', 'Via third-party vendors only')}\n"
        f"Honeymoon setup: {'Available' if ev.get('honeymoon_setup') else 'Not available'}\n"
        f"Cake arrangement: {ev.get('cake_arrangement', 'Via Swiggy/Zomato')}\n"
        f"Private dining: {'Available' if ev.get('private_dining') else 'Not available'}\n"
        f"Note: In-house staff setups are not provided. No bachelor/bachelorette parties allowed."
    )

def _section_business() -> str:
    biz = _HOTEL.get("business_traveler_features", {})
    dig = _HOTEL.get("digital_experience", {})
    return (
        f"BUSINESS TRAVELER FEATURES:\n"
        f"Printing: {biz.get('printing_service', 'At front desk on request')}\n"
        f"Scanning: {biz.get('scanning_service', 'At front desk on request')}\n"
        f"Meeting room: {'Available' if biz.get('meeting_room_available') else 'Not available'}\n"
        f"Co-working space: {'Available' if biz.get('coworking_space') else 'Not available'}\n"
        f"WiFi speed: {dig.get('wifi_speed_mbps', 100)} Mbps\n"
        f"Workspace-friendly rooms: Yes"
    )


def _section_contact() -> str:
    c = _HOTEL.get("contact", {})
    return (
        f"CONTACT INFO:\n"
        f"Phone: {c.get('phone', 'Please check wandrhotels.com')}\n"
        f"Email: {c.get('email', 'Please check wandrhotels.com')}\n"
        f"Website: {c.get('website', 'wandrhotels.com')}\n"
        f"Full Address: {c.get('address_full', _HOTEL['address']['street'])}"
    )


def _section_amenities() -> str:
    amenities = _HOTEL.get("amenities", [])
    return (
        f"AMENITIES:\n"
        f"All amenities: {', '.join(amenities) if amenities else 'WiFi, Parking, Elevator, Restaurant, 24h Front Desk'}"
    )


def _section_description() -> str:
    d = _HOTEL.get("description", {})
    return (
        f"HOTEL DESCRIPTION:\n"
        f"{d.get('comfortable_accommodations', '')}\n"
        f"{d.get('essential_facilities', '')}\n"
        f"{d.get('dining_options', '')}"
    )


def _section_reviews() -> str:
    reviews = _HOTEL.get("guest_reviews", [])
    r = _HOTEL.get("ratings", {})
    if not reviews:
        return f"GUEST REVIEWS:\nOverall rating: {r.get('overall_score', 'N/A')}/10"
    lines = [f"GUEST REVIEWS (Overall: {r.get('overall_score', 'N/A')}/10 — {r.get('overall_label', '')})"]
    for rv in reviews[:3]:
        pos = rv.get('positive', '')
        neg = rv.get('negative', '')
        if pos:
            lines.append(f"- {rv.get('reviewer','Guest')} ({rv.get('traveler_type','')}, {rv.get('stay_month','')}): '{pos}'")
    return "\n".join(lines)


def _section_booking_ops() -> str:
    b = _HOTEL.get("booking_operations", {})
    return (
        f"BOOKING OPERATIONS:\n"
        f"Walk-in guests: {'Yes' if b.get('walk_in_guests_allowed') else 'No'}\n"
        f"Booking modification: {b.get('booking_modification_policy', 'Subject to availability')}\n"
        f"No-show policy: {b.get('no_show_policy', 'Full night charge applies')}"
    )


def _section_area_info() -> str:
    a = _HOTEL.get("area_info", {})
    attractions = a.get("top_attractions", [])
    enjoyed = a.get("guests_enjoyed_area_for", [])
    top = [f"{x['name']} ({x['distance_km']} km)" for x in attractions[:5]]
    dist_city = _HOTEL.get("distance_from_city_center_km", "4.7")
    dist_airport = _HOTEL.get("distance_from_airport_km", "33")
    return (
        f"AREA INFO:\n"
        f"Distance from city center: {dist_city} km\n"
        f"Distance from airport: {dist_airport} km\n"
        f"Guests enjoy area for: {', '.join(enjoyed)}\n"
        f"Top attractions nearby: {', '.join(top)}"
    )


def _section_guest_personalization() -> str:
    g = _HOTEL.get("guest_personalization", {})
    return (
        f"GUEST PERSONALIZATION:\n"
        f"Room upgrade: {g.get('room_upgrade_policy', 'Subject to availability upon arrival')}\n"
        f"Loyalty program: {'Yes' if g.get('loyalty_program') else 'Not available'}\n"
        f"Returning guest discount: {'Yes' if g.get('returning_guest_discount') else 'Not available'}"
    )

# ── Intent → section mapping ──────────────────────────────────
INTENT_SECTIONS = {
    "fitness_center":     [_section_fitness_pool],
    "swimming_pool":      [_section_fitness_pool],
    "internet":           [_section_internet],
    "parking":            [_section_parking],
    "food":               [_section_food],
    "checkin":            [_section_checkin],
    "checkout":           [_section_checkin],
    "rooms":              [_section_rooms],
    "pricing":            [_section_pricing, _section_rooms],
    "location":           [_section_location],
    "nearby":             [_section_nearby, _section_location],
    "nearby_restaurants": [_section_nearby_restaurants, _section_nearby],
    "transport":          [_section_transport, _section_location],
    "safety":             [_section_safety],
    "laundry":            [_section_laundry],
    "billing":            [_section_billing],
    "smoking":            [_section_smoking],
    "pets":               [_section_pets],
    "accessibility":      [_section_accessibility],
    "events":             [_section_events],
    "business":           [_section_business],
    "policies":           [_section_policies, _section_checkin],
    "contact":            [_section_contact],
    "amenities":          [_section_amenities],
    "description":        [_section_description],
    "reviews":            [_section_reviews],
    "booking_ops":        [_section_booking_ops],
    "area_info":          [_section_area_info],
    "personalization":    [_section_guest_personalization],
}

# ── Core retrieval function ───────────────────────────────────
def get_relevant_context(query: str, top_k: int = 3) -> str:
    q = query.lower()
    q = re.sub(r"[^\w\s]", " ", q)

    matched_intents = set()
    for keyword, intent in SYNONYMS.items():
        if keyword in q:
            matched_intents.add(intent)

    builders = []
    seen = set()
    for intent in matched_intents:
        for fn in INTENT_SECTIONS.get(intent, []):
            if fn not in seen:
                builders.append(fn)
                seen.add(fn)

    if _section_general not in seen:
        builders.insert(0, _section_general)

    builders = builders[:top_k + 1]

    if len(builders) <= 1:
        builders = [_section_general, _section_policies, _section_checkin]

    context_parts = []
    for fn in builders:
        try:
            context_parts.append(fn())
        except Exception as e:
            print(f"[KB] Section error in {fn.__name__}: {e}")

    return "\n\n".join(context_parts)
