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

try:
    client.delete_collection(name=COLLECTION_NAME)
    print("[Chroma] Cleared previous collection")
except Exception:
    pass

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
    docs_and_ids.append((
        f"Accepted payment methods: {', '.join(payment_methods)}. "
        f"IMPORTANT: Only the above payment methods are accepted. "
        f"UPI, GPay, PhonePe, Paytm, and net banking are NOT mentioned in hotel data.",
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

    documents = [d for d, _ in docs_and_ids if d]
    ids       = [i for _, i in docs_and_ids if i]
    return documents, ids


# ── Index into ChromaDB ───────────────────────────────────────
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
    print("[Chroma] Warning: No documents to index.")


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
