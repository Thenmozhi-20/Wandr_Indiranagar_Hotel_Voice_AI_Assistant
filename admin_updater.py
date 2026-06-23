# ============================================================
#  admin_updater.py  —  Updates wandr_indiranagar.json on GitHub
# ============================================================

import os
import json
import base64
import requests

GITHUB_TOKEN       = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO        = os.environ.get("GITHUB_REPO", "")
RENDER_DEPLOY_HOOK = os.environ.get("RENDER_DEPLOY_HOOK", "")
FILE_PATH          = "wandr_indiranagar.json"
API_URL            = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def _trigger_redeploy():
    if RENDER_DEPLOY_HOOK:
        try:
            requests.get(RENDER_DEPLOY_HOOK, timeout=5)
            print("[Render] Redeploy triggered")
        except Exception as e:
            print(f"[Render] Redeploy failed: {e}")


def _fetch_current_json():
    """Returns (hotel_data, sha) — hotel_data is the inner hotel object only."""
    r = requests.get(API_URL, headers=HEADERS)
    r.raise_for_status()
    data       = r.json()
    content    = base64.b64decode(data["content"]).decode("utf-8")
    sha        = data["sha"]
    full       = json.loads(content)
    # Always extract the inner hotel object
    hotel_data = full["hotel"]
    # Guard against double nesting
    if "hotel" in hotel_data and isinstance(hotel_data["hotel"], dict):
        hotel_data = hotel_data["hotel"]
    return hotel_data, sha


def _push_updated_json(hotel_data: dict, sha: str, message: str):
    """Always saves as {"hotel": hotel_data} — never double-nested."""
    full_data = {"hotel": hotel_data}
    content   = json.dumps(full_data, indent=2, ensure_ascii=False)
    encoded   = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload   = {"message": message, "content": encoded, "sha": sha}
    r = requests.put(API_URL, headers=HEADERS, json=payload)
    r.raise_for_status()
    _trigger_redeploy()
    return True


def add_faq(question: str, answer: str):
    hotel, sha = _fetch_current_json()
    if "faqs" not in hotel:
        hotel["faqs"] = []
    hotel["faqs"].append({"question": question, "answer": answer})
    _push_updated_json(hotel, sha, f"Admin: Added FAQ - {question[:50]}")
    return "FAQ added successfully!"


def update_room_price(room_type: str, plan: str, new_price: int):
    hotel, sha = _fetch_current_json()
    for room in hotel["rooms"]:
        if room["room_type"].lower() == room_type.lower():
            for pricing in room["pricing"]:
                if pricing["plan"].lower() == plan.lower():
                    pricing["price_per_night_INR"] = new_price
                    _push_updated_json(hotel, sha, f"Admin: Updated price for {room_type}")
                    return f"Price updated to Rs.{new_price} for {room_type} ({plan})"
    return "Room type or plan not found."


def update_room_availability(room_type: str, status: str):
    hotel, sha = _fetch_current_json()
    for room in hotel["rooms"]:
        if room["room_type"].lower() == room_type.lower():
            room["availability_status"] = status
            _push_updated_json(hotel, sha, f"Admin: Updated availability for {room_type}")
            return f"Availability updated to '{status}' for {room_type}"
    return "Room type not found."


def add_nearby_place(name: str, distance_km: float, category: str):
    hotel, sha = _fetch_current_json()
    if "nearby_places" not in hotel:
        hotel["nearby_places"] = []
    hotel["nearby_places"].append({
        "name": name,
        "distance_km": distance_km,
        "category": category
    })
    _push_updated_json(hotel, sha, f"Admin: Added nearby place - {name}")
    return f"Nearby place '{name}' added successfully!"


def update_food_info(field: str, value: str):
    hotel, sha = _fetch_current_json()
    if "food_and_dining_details" not in hotel:
        hotel["food_and_dining_details"] = {}
    hotel["food_and_dining_details"][field] = value
    _push_updated_json(hotel, sha, f"Admin: Updated food info - {field}")
    return f"Food info updated: {field} = {value}"


def add_policy(policy_text: str):
    hotel, sha = _fetch_current_json()
    if "fine_print" not in hotel:
        hotel["fine_print"] = []
    hotel["fine_print"].append(policy_text)
    _push_updated_json(hotel, sha, "Admin: Added policy")
    return "Policy added successfully!"


def update_checkin_time(checkin: str, checkout: str):
    hotel, sha = _fetch_current_json()
    if "house_rules" not in hotel:
        hotel["house_rules"] = {}
    if "check_in" not in hotel["house_rules"]:
        hotel["house_rules"]["check_in"] = {}
    if "check_out" not in hotel["house_rules"]:
        hotel["house_rules"]["check_out"] = {}
    hotel["house_rules"]["check_in"]["from"]   = checkin
    hotel["house_rules"]["check_out"]["until"] = checkout
    _push_updated_json(hotel, sha, "Admin: Updated check-in/check-out times")
    return f"Check-in updated to {checkin}, Check-out updated to {checkout}"


def update_general_info(field: str, value: str):
    hotel, sha = _fetch_current_json()
    hotel[field] = value
    _push_updated_json(hotel, sha, f"Admin: Updated {field}")
    return f"Updated {field} successfully!"


# ── TASK 2: DELETE DATA ───────────────────────────────────────

def get_current_data():
    """Returns FAQs, nearby places, and policies — for the admin delete UI."""
    hotel, sha = _fetch_current_json()
    return {
        "faqs":          hotel.get("faqs", []),
        "nearby_places": hotel.get("nearby_places", []),
        "policies":      hotel.get("fine_print", [])
    }


def delete_faq(index: int):
    """Delete a FAQ by its index in the faqs list."""
    hotel, sha = _fetch_current_json()
    faqs = hotel.get("faqs", [])
    if index < 0 or index >= len(faqs):
        return "Invalid FAQ selected."
    deleted = faqs.pop(index)
    hotel["faqs"] = faqs
    _push_updated_json(hotel, sha, f"Admin: Deleted FAQ - {deleted.get('question','')[:50]}")
    return f"Deleted FAQ: '{deleted.get('question','')[:60]}'"


def delete_nearby_place(index: int):
    """Delete a nearby place by its index in the nearby_places list."""
    hotel, sha = _fetch_current_json()
    places = hotel.get("nearby_places", [])
    if index < 0 or index >= len(places):
        return "Invalid place selected."
    deleted = places.pop(index)
    hotel["nearby_places"] = places
    _push_updated_json(hotel, sha, f"Admin: Deleted nearby place - {deleted.get('name','')}")
    return f"Deleted nearby place: '{deleted.get('name','')}'"


def delete_policy(index: int):
    """Delete a policy/fine_print entry by its index."""
    hotel, sha = _fetch_current_json()
    policies = hotel.get("fine_print", [])
    if index < 0 or index >= len(policies):
        return "Invalid policy selected."
    deleted = policies.pop(index)
    hotel["fine_print"] = policies
    _push_updated_json(hotel, sha, "Admin: Deleted policy")
    return f"Deleted policy: '{deleted[:60]}'"
