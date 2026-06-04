# ============================================================
#  knowledge_base.py  —  ChromaDB Knowledge Base
#  Uses ChromaDB semantic search on wandr_indiranagar.json
#  Fixed:
#    - Gym/pool explicitly indexed as NOT available
#    - Restaurants pulled from correct field (area_info)
#    - Payment methods strictly from JSON only
#    - Nearby places NOT labeled as restaurants
# ============================================================

import json
import os
import chromadb

# ── Initialize Chroma Client ──────────────────────────────────
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
os.makedirs(CHROMA_DB_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# ── Load JSON data ────────────────────────────────────────────
JSON_PATH = os.path.join(os.path.dirname(__file__), "wandr_indiranagar.json")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    HOTEL_DATA = json.load(f)["hotel"]

print(f"[KB] Loaded hotel data: {HOTEL_DATA['name']}")

# ── Initialize Chroma Collection ──────────────────────────────
COLLECTION_NAME = "wandr_knowledge"

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


# ── Prepare documents from JSON ───────────────────────────────
def prepare_documents():
    """
    Extract all hotel information as documents for ChromaDB.
    Every fact is explicit — no ambiguity for the LLM.
    """
    docs_and_ids = []
    h = HOTEL_DATA

    # ── 1. Hotel Basics ───────────────────────────────────────
    docs_and_ids.append((
        f"Hotel name: {h['name']}. "
        f"Address: {h['address']['street']}, {h['address']['city']} - {h['address']['pincode']}. "
        f"State: {h['address']['state']}, Country: {h['address']['country']}.",
        "hotel_basics"
    ))

    # ── 2. Ratings ────────────────────────────────────────────
    s = h["ratings"]["category_scores"]
    docs_and_ids.append((
        f"Overall rating: {h['ratings']['overall_score']}/10 ({h['ratings']['overall_label']}) "
        f"based on {h['ratings']['total_reviews']} reviews. "
        f"Staff: {s['staff']}/10. Facilities: {s['facilities']}/10. "
        f"Cleanliness: {s['cleanliness']}/10. Comfort: {s['comfort']}/10. "
        f"Value for money: {s['value_for_money']}/10. "
        f"Location: {s['location']}/10. Free WiFi: {s['free_wifi']}/10. "
        f"Couples rating: {h['ratings'].get('couples_rating', 'N/A')}/10.",
        "hotel_ratings"
    ))

    # ── 3. Distance / Location ────────────────────────────────
    docs_and_ids.append((
        f"Distance from city center: {h['distance_from_city_center_km']} km. "
        f"Distance from airport (Kempegowda International Airport): {h['distance_from_airport_km']} km. "
        f"Location tag: {h.get('location_tag', 'Excellent location')}.",
        "hotel_distance"
    ))

    # ── 4. Description ────────────────────────────────────────
    desc = h.get("description", {})
    docs_and_ids.append((
        f"About the hotel: {desc.get('comfortable_accommodations', '')} "
        f"{desc.get('essential_facilities', '')} "
        f"{desc.get('dining_options', '')} "
        f"{desc.get('local_attractions', '')} "
        f"Popular with families: {desc.get('popular_with_families')}. "
        f"Couple friendly: {desc.get('couple_friendly')}.",
        "hotel_description"
    ))

    # ── 5. Rooms & Pricing ────────────────────────────────────
    for room in h.get("rooms", []):
        rtype  = room.get("room_type", "Room")
        bed    = room.get("bed_type", "")
        status = room.get("availability_status", "")
        amenities = ", ".join(room.get("amenities", []))
        pricing_parts = []
        for plan in room.get("pricing", []):
            pricing_parts.append(
                f"{plan['plan']}: Rs.{plan['price_per_night_INR']}/night "
                f"(original Rs.{plan['original_price_INR']}, "
                f"discount Rs.{plan['discount_INR']}, {plan['price_note']})"
            )
        pricing_str = " | ".join(pricing_parts) if pricing_parts else "Sold out — no pricing available"
        docs_and_ids.append((
            f"Room type: {rtype}. Bed type: {bed}. "
            f"Availability: {status}. "
            f"Room amenities: {amenities}. "
            f"Pricing: {pricing_str}.",
            f"room_{rtype.lower().replace(' ', '_')}"
        ))

    # ── 6. Breakfast / Dining ─────────────────────────────────
    bf = h.get("breakfast", {})
    meal_periods = ", ".join(bf.get("meal_periods", []))
    docs_and_ids.append((
        f"Breakfast available: {bf.get('available')}. "
        f"Breakfast options: {', '.join(bf.get('options', []))}. "
        f"Breakfast includes: {', '.join(bf.get('includes', []))}. "
        f"Meal periods served at hotel: {meal_periods}. "
        f"On-site restaurant: {h['facilities'].get('restaurant_onsite')}. "
        f"Restaurant serves: {h['facilities'].get('restaurant_note', 'breakfast, lunch and dinner')}. "
        f"Breakfast guest review score: {bf.get('guest_review_score')}/10.",
        "breakfast_dining"
    ))

    # ── 7. Nearby Restaurants (CORRECT field) ─────────────────
    restaurants = h["area_info"].get("restaurants_and_cafes", [])
    rest_list = ", ".join([
        f"{r['name']} ({r['type']}) - {r.get('distance_m', '')}m away"
        for r in restaurants
    ])
    docs_and_ids.append((
        f"Nearby restaurants and cafes close to the hotel: {rest_list}. "
        f"These are the only known nearby dining options from hotel data.",
        "nearby_restaurants"
    ))

    # ── 8. Nearby Places (NOT restaurants) ────────────────────
    nearby = h.get("nearby_places", [])
    nearby_list = ", ".join([
        f"{n['name']} - {n['distance_km']}km" for n in nearby
    ])
    docs_and_ids.append((
        f"Nearby places and landmarks (these are NOT restaurants): {nearby_list}.",
        "nearby_places"
    ))

    # ── 9. Top Attractions ────────────────────────────────────
    attractions = h["area_info"].get("top_attractions", [])
    attr_list = ", ".join([
        f"{a['name']} - {a['distance_km']}km" for a in attractions
    ])
    docs_and_ids.append((
        f"Top tourist attractions near the hotel: {attr_list}.",
        "top_attractions"
    ))

    # ── 10. WiFi ──────────────────────────────────────────────
    wifi = h["facilities"].get("internet", {})
    docs_and_ids.append((
        f"WiFi available: {wifi.get('wifi_available')}. "
        f"WiFi coverage: {wifi.get('wifi_areas')}. "
        f"WiFi cost: {wifi.get('wifi_cost')}.",
        "wifi"
    ))

    # ── 11. Parking ───────────────────────────────────────────
    parking = h["facilities"].get("parking", {})
    docs_and_ids.append((
        f"Parking available: {parking.get('available')}. "
        f"Type: {parking.get('type')}. "
        f"Reservation needed: {parking.get('reservation_needed')}. "
        f"Capacity: {parking.get('capacity')}. "
        f"Parking garage: {parking.get('parking_garage')}. "
        f"Accessible parking: {parking.get('accessible_parking')}.",
        "parking"
    ))

    # ── 12. Pool — EXPLICITLY NOT available ───────────────────
    has_pool = h["facilities"].get("swimming_pool", False)
    docs_and_ids.append((
        f"Swimming pool: {'Available at the hotel.' if has_pool else 'NOT available. This hotel does NOT have a swimming pool.'}",
        "swimming_pool"
    ))

    # ── 13. Gym — EXPLICITLY NOT available ────────────────────
    has_gym = h["facilities"].get("fitness_center", False)
    docs_and_ids.append((
        f"Gym / Fitness center: {'Available at the hotel.' if has_gym else 'NOT available. This hotel does NOT have a gym or fitness center.'}",
        "gym_fitness"
    ))

    # ── 14. Airport Shuttle ───────────────────────────────────
    shuttle = h["facilities"].get("airport_shuttle", {})
    docs_and_ids.append((
        f"Airport shuttle: Available={shuttle.get('available')}. "
        f"Additional charge applies: {shuttle.get('additional_charge')}. "
        f"How to request: {shuttle.get('request')}.",
        "airport_shuttle"
    ))

    # ── 15. Check-in / Check-out ──────────────────────────────
    rules = h.get("house_rules", {})
    ci = rules.get("check_in", {})
    co = rules.get("check_out", {})
    docs_and_ids.append((
        f"Check-in from: {ci.get('from')} (1:00 PM). "
        f"Check-out until: {co.get('until')} (11:00 AM). "
        f"Early check-in: {ci.get('early_check_in')}. "
        f"Late check-out: {co.get('late_check_out')}.",
        "checkin_checkout"
    ))

    # ── 16. Policies ──────────────────────────────────────────
    age   = rules.get("age_restriction", {})
    pets  = rules.get("pets", {})
    smoke = rules.get("smoking", {})
    food  = rules.get("outside_food_beverage", {})
    visit = rules.get("visitors", {})
    party = rules.get("parties_events", {})
    idr   = rules.get("id_requirements", {})
    docs_and_ids.append((
        f"Minimum check-in age: {age.get('minimum_check_in_age')}. "
        f"Pets: {'Allowed' if pets.get('allowed') else 'NOT allowed'}. "
        f"Smoking: {'Allowed' if smoke.get('allowed') else 'NOT allowed'} (designated area available). "
        f"Outside food and beverages: {'Allowed' if food.get('allowed') else 'Not allowed'}. "
        f"Visitors: {'Allowed' if visit.get('allowed') else 'Not allowed'}. "
        f"Parties/events: {'Allowed' if party.get('allowed') else 'NOT allowed'}. "
        f"Government ID required: {idr.get('government_id_required')}. "
        f"Local ID accepted: {idr.get('local_id_allowed')}. "
        f"Foreigners allowed: {idr.get('foreigners_allowed')}. "
        f"Cancellation policy: {rules.get('cancellation_prepayment', 'Varies by room type')}.",
        "house_policies"
    ))

    # ── 17. Couple Policy ─────────────────────────────────────
    couple = rules.get("couples", {})
    docs_and_ids.append((
        f"Couple friendly: {couple.get('couple_friendly')}. "
        f"Unmarried couples allowed: {couple.get('unmarried_couples_allowed')}. "
        f"Valid ID cards required for all guests.",
        "couple_policy"
    ))

    # ── 18. Children Policy ───────────────────────────────────
    children = rules.get("children_policy", {})
    extra_bed = children.get("extra_bed", {})
    docs_and_ids.append((
        f"Children welcome: {children.get('children_welcome')}. "
        f"Children charged as adults from age: {children.get('children_charged_as_adults_age')}. "
        f"Cribs available: {children.get('cribs_available')}. "
        f"Extra bed: available on request at "
        f"Rs.{extra_bed.get('price_per_person_per_night_INR', 1500)}/person/night.",
        "children_policy"
    ))

    # ── 19. Payment Methods (STRICTLY from JSON) ──────────────
    payment_methods = h.get("payment_methods", [])
    upi = h.get("billing_details", {}).get("upi_accepted", False)

    docs_and_ids.append((
        f"Accepted payment methods: {', '.join(payment_methods)}. "
        f"UPI accepted: {upi}.",
        "payment_methods"
    ))

    # ── 20. Amenities ─────────────────────────────────────────
    docs_and_ids.append((
        f"Hotel amenities: {', '.join(h.get('amenities', []))}.",
        "amenities"
    ))

    # ── 21. Safety & Security ─────────────────────────────────
    security = h["facilities"].get("safety_and_security", [])
    docs_and_ids.append((
        f"Safety and security features: {', '.join(security)}.",
        "security"
    ))

    # ── 22. Accessibility ─────────────────────────────────────
    accessibility = h["facilities"].get("accessibility", [])
    docs_and_ids.append((
        f"Accessibility features: {', '.join(accessibility)}.",
        "accessibility"
    ))

    # ── 23. Languages Spoken ──────────────────────────────────
    languages = h["facilities"].get("languages_spoken", [])
    docs_and_ids.append((
        f"Languages spoken by staff: {', '.join(languages)}.",
        "languages"
    ))

    # ── 24. Cleaning Services ─────────────────────────────────
    cl = h["facilities"].get("cleaning_services", {})
    docs_and_ids.append((
        f"Daily housekeeping: {cl.get('daily_housekeeping')}. "
        f"Guest room cleaning: {cl.get('guest_room_cleaning')}. "
        f"Disinfectant cleaning: {cl.get('disinfectant_cleaning')}. "
        f"Laundry: available at additional charge. "
        f"Dry cleaning: available at additional charge. "
        f"Ironing service: available at additional charge.",
        "cleaning_services"
    ))

    # ── 25. Public Transit ────────────────────────────────────
    transit = h["area_info"].get("public_transit", [])
    transit_list = ", ".join([
        f"{t['name']} ({t['type']}) - {t['distance_km']}km" for t in transit
    ])
    docs_and_ids.append((
        f"Nearby public transit options: {transit_list}.",
        "public_transit"
    ))

    # ── 26. FAQs ──────────────────────────────────────────────
    for i, faq in enumerate(h.get("faqs", [])):
        docs_and_ids.append((
            f"FAQ: {faq['question']} Answer: {faq['answer']}",
            f"faq_{i}"
        ))

    # ── 27. Guest Reviews ─────────────────────────────────────
    for i, rv in enumerate(h.get("guest_reviews", [])):
        docs_and_ids.append((
            f"Guest review by {rv['reviewer']} ({rv['country']}), "
            f"{rv['room_type']}, {rv['stay_duration']}, "
            f"Rating: {rv['rating']}/10. "
            f"Positive: {rv['positive']}. "
            f"Negative: {rv.get('negative', 'None')}.",
            f"review_{i}"
        ))

    # ── 28. Fine Print ────────────────────────────────────────
    fine_print = h.get("fine_print", [])
    docs_and_ids.append((
        f"Important notes: {' '.join(fine_print)}",
        "fine_print"
    ))

    # ── 29. Contact Details ───────────────────────────────────
    contact = h.get("contact", {})
    phone   = contact.get("phone",   "Not available — please check wandrhotels.com")
    email   = contact.get("email",   "Not available — please check wandrhotels.com")
    website = contact.get("website", "wandrhotels.com")
    addr    = contact.get("address_full", "3363 No. 3363, 2nd cross road, HAL 2nd stage, Indiranagar, Bangalore - 560038")
    docs_and_ids.append((
        f"Hotel contact details — Phone: {phone}. "
        f"Email: {email}. Website: {website}. "
        f"Full address: {addr}.",
        "contact_details"
    ))

    # ── 30. Property Master ─────────────────────────────
    pm = h.get("property_master", {})
    docs_and_ids.append((
        f"Property type: {pm.get('property_type')}. "
        f"Year opened: {pm.get('year_opened')}. "
        f"Last renovated: {pm.get('last_renovated')}. "
        f"Total rooms: {pm.get('total_rooms')}. "
        f"Number of floors: {pm.get('number_of_floors')}. "
        f"Power backup available: {pm.get('power_backup')}. "
        f"EV charging available: {pm.get('ev_charging')}. "
        f"Valet parking available: {pm.get('valet_parking')}.",
        "property_master"
    ))

    # ── 31. Location Intelligence ──────────────────────
    loc = h.get("location_intelligence", {})
    docs_and_ids.append((
        f"Nearest hospitals: {', '.join(loc.get('nearest_hospital', []))}. "
        f"Nearest pharmacies: {', '.join(loc.get('nearest_pharmacy', []))}. "
        f"Nearest ATMs: {', '.join(loc.get('nearest_atm', []))}. "
        f"Nearest grocery stores: {', '.join(loc.get('nearest_grocery_store', []))}. "
        f"Nearest petrol stations: {', '.join(loc.get('nearest_petrol_bunk', []))}.",
        "location_intelligence"
    ))

    # ── 32. Room Specifications ────────────────────────
    specs = h.get("room_specs", {})
    docs_and_ids.append((
        f"Room sizes: {specs.get('room_size_sqft')}. "
        f"Bed dimensions: {specs.get('bed_dimensions')}. "
        f"Mattress type: {specs.get('mattress_type')}. "
        f"Hot water availability: {specs.get('hot_water_availability')}. "
        f"Blackout curtains: {specs.get('blackout_curtains')}. "
        f"Workspace friendly: {specs.get('workspace_friendly')}. "
        f"Smart TV available: {specs.get('smart_tv')}.",
        "room_specs"
    ))

    # ── 33. Digital Experience ─────────────────────────
    dx = h.get("digital_experience", {})
    docs_and_ids.append((
        f"Mobile check-in: {dx.get('mobile_check_in')}. "
        f"Digital check-out: {dx.get('digital_check_out')}. "
        f"Online KYC: {dx.get('online_kyc')}. "
        f"WhatsApp concierge: {dx.get('whatsapp_concierge')}. "
        f"QR room service: {dx.get('qr_room_service')}. "
        f"WiFi speed: {dx.get('wifi_speed_mbps')} Mbps. "
        f"Backup internet provider: {dx.get('backup_internet_provider')}.",
        "digital_experience"
    ))

    # ── 34. Food & Dining Details ──────────────────────
    food = h.get("food_and_dining_details", {})
    docs_and_ids.append((
        f"Breakfast timings: {food.get('breakfast_timings')}. "
        f"Breakfast type: {food.get('breakfast_type')}. "
        f"Room service timings: {food.get('room_service_timings')}. "
        f"Late night food available: {food.get('late_night_food_available')}. "
        f"Complimentary tea and coffee: {food.get('complimentary_tea_coffee')}. "
        f"Outside delivery apps allowed: {food.get('outside_delivery_apps_allowed')}.",
        "food_dining_details"
    ))

    # ── 35. Cleaning & Hygiene ─────────────────────────
    clean = h.get("cleaning_hygiene", {})
    docs_and_ids.append((
        f"Room cleaning frequency: {clean.get('room_cleaning_frequency')}. "
        f"Linen change frequency: {clean.get('linen_change_frequency')}. "
        f"Sanitization process: {clean.get('sanitization_process')}. "
        f"RO drinking water available: {clean.get('ro_drinking_water')}.",
        "cleaning_hygiene"
    ))

    # ── 36. Safety & Emergency ─────────────────────────
    safe = h.get("safety_emergency", {})
    docs_and_ids.append((
        f"Doctor on call: {safe.get('doctor_on_call')}. "
        f"First aid kit available: {safe.get('first_aid_kit_available')}. "
        f"Fire exit map in rooms: {safe.get('fire_exit_map_in_rooms')}. "
        f"Emergency contact process: {safe.get('emergency_contact_process')}. "
        f"Female traveler safety rating: {safe.get('female_traveler_safety_rating')}.",
        "safety_emergency"
    ))

    # ── 37. Billing Details ────────────────────────────
    bill = h.get("billing_details", {})
    gst = bill.get("gst_breakdown", {})
    docs_and_ids.append((
        f"UPI accepted: {bill.get('upi_accepted')}. "
        f"Split payment supported: {bill.get('split_payment_supported')}. "
        f"Corporate billing available: {bill.get('corporate_billing_available')}. "
        f"Refund timeline: {bill.get('refund_timeline_days')} days. "
        f"GST percentage: {gst.get('total_gst_percentage')}%.",
        "billing_details"
    ))

    # ── 38. Booking Operations ─────────────────────────
    booking = h.get("booking_operations", {})
    docs_and_ids.append((
        f"Walk-in guests allowed: {booking.get('walk_in_guests_allowed')}. "
        f"Tentative booking available: {booking.get('tentative_booking_available')}. "
        f"Booking modification policy: {booking.get('booking_modification_policy')}. "
        f"No-show policy: {booking.get('no_show_policy')}.",
        "booking_operations"
    ))

    # ── 39. Event Services ─────────────────────────────
    event = h.get("event_services", {})
    docs_and_ids.append((
        f"Birthday decorations: {event.get('birthday_decorations')}. "
        f"Anniversary setup: {event.get('anniversary_setup')}. "
        f"Cake arrangement: {event.get('cake_arrangement')}.",
        "event_services"
    ))

    # ── 40. Business Traveler Features ────────────────
    biz = h.get("business_traveler_features", {})
    docs_and_ids.append((
        f"Printing service: {biz.get('printing_service')}. "
        f"Scanning service: {biz.get('scanning_service')}. "
        f"Weekly rates: {biz.get('weekly_rates_available')}. "
        f"Monthly stay discount: {biz.get('monthly_stay_discount')}.",
        "business_traveler_features"
    ))


    documents = [d for d, _ in docs_and_ids if d]
    ids       = [i for _, i in docs_and_ids if i]
    return documents, ids


# ── Query Function ────────────────────────────────────────────
def get_relevant_context(query: str, top_k: int = 6) -> str:
    """
    Semantic search on ChromaDB.
    Returns top_k most relevant hotel info chunks for the query.
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )

        if results and results["documents"] and results["documents"][0]:
            context_lines = []
            for i, doc in enumerate(results["documents"][0], 1):
                if doc:
                    context_lines.append(f"{i}. {doc}")
            return "\n".join(context_lines)
        else:
            return "No relevant information found in knowledge base."

    except Exception as e:
        print(f"[Chroma] Query error: {e}")
        return "Error retrieving information from knowledge base."

# ── Index only if collection is empty (skip on subsequent startups) ──
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

# Only index if empty
if collection.count() == 0:
    print("[Chroma] Indexing hotel knowledge base...")
    documents, ids = prepare_documents()
    if documents:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=[{"source": "wandr_indiranagar"} for _ in documents]
        )
        print(f"[Chroma] Indexed {len(documents)} documents successfully.")
else:
    print(f"[Chroma] Using cached index ({collection.count()} docs).")