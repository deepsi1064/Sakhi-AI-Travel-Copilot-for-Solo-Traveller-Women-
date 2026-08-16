"""Static, curated destination knowledge — not a live data source.

This is a small placeholder knowledge base for a handful of well-known
solo-travel destinations in India. Treat it as example data: replace with a
real content pipeline and verified sources before relying on it. See
docs/mcp.md for why this lives behind an MCP tool rather than inline in the
system prompt.
"""

DESTINATIONS: dict[str, dict] = {
    "varkala": {
        "state": "Kerala",
        "overview": "Cliffside beach town with a well-established backpacker and yoga scene.",
        "best_time": "November to March",
        "getting_around": "Autos and the cliff-top walkway cover most of the tourist area on foot.",
        "traveller_notes": [
            "The North Cliff strip is well lit and busy into the evening; the beach itself empties out after sunset.",
            "Varkala railway station is about 2km from the cliff — pre-book an auto for late arrivals.",
        ],
    },
    "rishikesh": {
        "state": "Uttarakhand",
        "overview": "Yoga and adventure-sports hub on the Ganges, popular with solo travellers.",
        "best_time": "September to April",
        "getting_around": "Most of Laxman Jhula and Tapovan is walkable; autos cover longer distances.",
        "traveller_notes": [
            "Areas around the main ghats and ashrams are busy with pilgrims and tourists most of the day.",
            "River-crossing footbridges can be crowded — keep bags zipped and to the front.",
        ],
    },
    "goa": {
        "state": "Goa",
        "overview": "Coastal state with a large domestic and international tourist base.",
        "best_time": "November to February",
        "getting_around": "Scooters are common; state buses and app-based cabs cover the rest.",
        "traveller_notes": [
            "North Goa beach belts are lively at night; South Goa is quieter with fewer people around after dark.",
            "Helmet use and scooter licensing are enforced with fines in places.",
        ],
    },
    "jaipur": {
        "state": "Rajasthan",
        "overview": "Walled Pink City, major gateway for Rajasthan trips.",
        "best_time": "October to March",
        "getting_around": "Autos and app cabs are widely available; the old city is dense and walkable in daytime.",
        "traveller_notes": [
            "Main bazaars are busy and well trafficked through the evening.",
            "Agree on auto fares upfront or insist on the meter.",
        ],
    },
    "hampi": {
        "state": "Karnataka",
        "overview": "UNESCO ruins site spread across a boulder-strewn landscape, popular backpacker stop.",
        "best_time": "October to February",
        "getting_around": "Bicycles and scooters are the normal way to cover the ruins, which are spread out.",
        "traveller_notes": [
            "The site is remote with long stretches between settlements — plan return transport before dark.",
            "Mobile signal is patchy in parts of the ruins area.",
        ],
    },
}


def normalize_key(name: str) -> str:
    return name.strip().lower()
