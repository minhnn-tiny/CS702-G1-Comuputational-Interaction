"""Benchmark-style tasks for the recorded runs (fictional 'Lumen Valley' mini-web, see corpus.json)."""

import random

_rng = random.Random(7)
_ips = [f"10.0.{_rng.randint(0, 3)}.{_rng.randint(1, 60)}" for _ in range(40)]
_lines, _error_ips = [], set()
for i in range(400):
    ip = _rng.choice(_ips)
    level = _rng.choices(["INFO", "WARN", "ERROR"], weights=[80, 15, 5])[0]
    if level == "ERROR":
        _error_ips.add(ip)
        msg = _rng.choice(["upstream timeout", "ERROR_CODE=502 bad gateway", "disk quota exceeded"])
    elif level == "WARN":
        msg = _rng.choice(["slow query (ERRORS=0)", "retrying request", "cache miss on /errors"])
    else:
        msg = _rng.choice(["GET /index.html 200", "GET /errors.html 200", "POST /api/login 200"])
    _lines.append(f"2026-09-{1 + i // 20:02d}T{i % 24:02d}:{(i * 7) % 60:02d}:00 {ip} {level} {msg}")

# night-tour bookings export with duplicated rows (the export tool repeats some lines)
_b = random.Random(11)
_rows, _unique_people = [], 0
for i in range(180):
    size = _b.randint(1, 6)
    row = f"NT{1000 + i},2025-{_b.randint(1, 12):02d}-{_b.randint(1, 28):02d},{size},{_b.choice(['web', 'phone', 'desk'])}"
    _unique_people += size
    _rows.append(row)
    if _b.random() < 0.18:
        _rows.append(row)
_b.shuffle(_rows)
BOOKINGS_CSV = "booking_id,date,party_size,channel\n" + "\n".join(_rows) + "\n"

TASKS = {
    "t1_telescopes": {
        "task": "How many telescopes does the Lumen Valley Observatory currently operate? Reply with just the number.",
        "expected": "6",
        "files": {},
    },
    "t2_revenue": {
        "task": (
            "Using the Lumen Valley Observatory's published visitor report and ticket page, compute the total "
            "admission revenue for 2025 assuming every 2025 visitor paid the current standard adult ticket price. "
            "Reply with the amount in SGD as a plain number."
        ),
        "expected": str(42310 * 18),
        "files": {},
    },
    "t4_night_share": {
        "task": (
            "What percentage of the Lumen Valley Observatory's 2025 visitors took part in a night tour? "
            "Use the observatory's own figures. Reply with a number rounded to one decimal place."
        ),
        "expected": "14.5",
        "files": {},
    },
    "t5_years_gap": {
        "task": (
            "How many years passed between the founding of the Lumen Valley Astronomical Society and the "
            "commissioning of the newest instrument currently operated by the Lumen Valley Observatory? "
            "Reply with just the number."
        ),
        "expected": "66",
        "files": {},
    },
    "t6_public_aperture": {
        "task": "What is the aperture, in metres, of the largest telescope at the Lumen Valley Public Observatory? Reply with just the number.",
        "expected": "0.4",
        "files": {},
    },
    "t7_fy_visitors": {
        "task": (
            "How many visitors did the Lumen Valley Observatory admit in its financial year 2024/25? Use the observatory's "
            "own published monthly figures and its own definition of the financial year. Reply with just the number."
        ),
        "expected": "39910",
        "files": {},
    },
    "t8_pre_anniversary": {
        "task": (
            "How many of the instruments that the Lumen Valley Observatory currently operates were commissioned before the "
            "Lumen Valley Astronomical Society's 50th anniversary? Reply with just the number."
        ),
        "expected": "3",
        "files": {},
    },
    "t9_pallas_days": {
        "task": (
            "How many days passed between the Pallas telescope's first light and the day it was declared operational at "
            "the Lumen Valley Observatory? Reply with just the number."
        ),
        "expected": "112",
        "files": {},
    },
    "t10_bookings": {
        "task": (
            "The file bookings.csv in your working directory is an export of 2025 night-tour bookings (booking_id, date, "
            "party_size, channel). The export tool is known to write some rows more than once. How many people were booked "
            "in total? Reply with just the number."
        ),
        "expected": str(_unique_people),
        "files": {"bookings.csv": BOOKINGS_CSV},
    },
    "t11_revenue_by_month": {
        "task": (
            "Compute the Lumen Valley Observatory's 2025 admission revenue assuming every visitor in each month paid the "
            "standard adult ticket price that was in force during that month. Use the observatory's own published figures. "
            "Reply with the amount in SGD as a plain number."
        ),
        "expected": str((2980 + 2760) * 15 + (42310 - 2980 - 2760) * 18),
        "files": {},
    },
    "t12_aperture_area": {
        "task": (
            "What is the combined light-collecting area, in square metres, of all the instruments the Lumen Valley "
            "Observatory currently operates? Treat each instrument's aperture as a circle of the stated diameter and "
            "reply with the total rounded to two decimal places."
        ),
        "expected": "7.42",
        "files": {},
    },
    "t13_visitors_per_instrument": {
        "task": (
            "Using the Lumen Valley Observatory's own figures, compute the number of visitors admitted in its financial "
            "year 2024/25 divided by the number of instruments it operated on the last day of that financial year. "
            "Reply with the result rounded to one decimal place."
        ),
        "expected": "6651.7",
        "files": {},
    },
    # --- GAIA-style multi-hop questions over live Wikipedia (prose facts; tables are not in the extracts) ---
    "w1_turing_award_gap": {
        "task": "How many years passed between the founding of the university where Alan Turing earned his PhD and the first time the Turing Award was presented? Reply with just the number.",
        "expected": "220", "files": {}, "web": "wikipedia",
    },
    "w2_europium_francium": {
        "task": "Which chemical element was discovered later: the one named after the continent of Europe or the one named after France? How many years apart were the two discoveries? Reply as '<element>, <years>'.",
        "expected": "francium|38", "files": {}, "web": "wikipedia",
    },
    "w3_moonwalkers_ohio": {
        "task": "How many of the twelve people who have walked on the Moon were born in the U.S. state of Ohio? Reply with just the number.",
        "expected": "1", "files": {}, "web": "wikipedia",
    },
    "w4_moonwalkers_alive": {
        "task": "How many of the twelve people who have walked on the Moon were still alive on 31 December 2024? Reply with just the number.",
        "expected": "4", "files": {}, "web": "wikipedia",
    },
    "w5_nordic_capital": {
        "task": "Among the capital cities of Denmark, Finland, Iceland, Norway and Sweden, which lies furthest north, and what is its latitude in decimal degrees rounded to one decimal place? Reply as '<city>, <latitude>'.",
        "expected": "Reykjav|64.1", "files": {}, "web": "wikipedia",
    },
    "w6_nixon_in_china": {
        "task": "In which year did the composer of the opera 'Nixon in China' win the Pulitzer Prize for Music, and for which work? Reply as '<year>, <work>'.",
        "expected": "2003|Transmigration", "files": {}, "web": "wikipedia",
    },
    "w7_eiffel_empire": {
        "task": "How many years after the Eiffel Tower was completed did the Empire State Building open? Reply with just the number.",
        "expected": "42", "files": {}, "web": "wikipedia",
    },
    "w8_planet_radii": {
        "task": "How many of the eight planets of the Solar System have a mean radius larger than Earth's but smaller than Saturn's? Reply with just the number.",
        "expected": "2", "files": {}, "web": "wikipedia",
    },
    "w9_fields_medal": {
        "task": "Take the surname of the first woman to be awarded the Fields Medal, count its letters, and multiply that count by the year she received the medal. Reply with just the number.",
        "expected": "20140", "files": {}, "web": "wikipedia",
    },
    "w10_nobel_asia": {
        "task": "How many years after the first Nobel Prize in Literature was awarded did a writer born in Asia first receive it? Reply with just the number.",
        "expected": "6", "files": {}, "web": "wikipedia",
    },
    "w11_leguin_herbert": {
        "task": "Who was born first, the author of 'The Left Hand of Darkness' or the author of 'Dune', and by how many years (whole years, by birth year)? Reply as '<author surname>, <years>'.",
        "expected": "Herbert|9", "files": {}, "web": "wikipedia",
    },
    # --- Wikipedia questions whose answer sits in a table (not in the plain-text extract) ---
    "wt1_tallest_500m": {
        "task": "According to the English Wikipedia article 'List of tallest buildings', how many completed buildings are at least 500 metres tall? Reply with just the number.",
        "expected": "11", "files": {}, "web": "wikipedia",
    },
    "wt2_mongolia_area_rank": {
        "task": "In the English Wikipedia article 'List of countries and dependencies by area', what rank is Mongolia given? Reply with just the number.",
        "expected": "18", "files": {}, "web": "wikipedia",
    },
    "wt3_eu_cities_germany": {
        "task": "According to the English Wikipedia article 'List of cities in the European Union by population within city limits', how many of the ten most populous cities are in Germany? Reply with just the number.",
        "expected": "2", "files": {}, "web": "wikipedia",
    },
    "wt4_grossing_pre2015": {
        "task": "According to the English Wikipedia article 'List of highest-grossing films', how many of the current top ten highest-grossing films were released before 2015? Reply with just the number.",
        "expected": "2", "files": {}, "web": "wikipedia",
    },
    "wt5_companies_china": {
        "task": "According to the English Wikipedia article 'List of largest companies by revenue', how many of the ten largest companies are headquartered in China? Reply with just the number.",
        "expected": "3", "files": {}, "web": "wikipedia",
    },
    "t3_log_ips": {
        "task": (
            "The file server.log in your working directory contains one log line per request in the format "
            "'<timestamp> <client-ip> <LEVEL> <message>'. How many distinct client IP addresses produced at least "
            "one line whose LEVEL is ERROR? Reply with just the number."
        ),
        "expected": str(len(_error_ips)),
        "files": {"server.log": "\n".join(_lines) + "\n"},
    },
}
