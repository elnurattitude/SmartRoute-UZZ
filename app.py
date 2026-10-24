
import streamlit as st
import requests
import folium
import pandas as pd
from streamlit_folium import st_folium

# =========================================================
# SMARTROUTE UZ — FREE WORLD MAP + ROUTE PLANNER
# =========================================================

st.set_page_config(
    page_title="SmartRoute UZ",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

HEADERS = {
    "User-Agent": "SmartRouteUZ/1.0 (educational route planning app)"
}

# -------------------- DESIGN --------------------

st.markdown("""
<style>
.stApp {
    background: #0b1020;
    color: #f4f7ff;
}
[data-testid="stSidebar"] {
    background: #11182b;
}
.hero {
    background: linear-gradient(120deg, #17294a, #201b43);
    border: 1px solid #293858;
    border-radius: 22px;
    padding: 30px;
    margin-bottom: 24px;
}
.hero h1 {
    font-size: 42px;
    margin: 8px 0;
    color: #ffffff;
}
.hero p {
    color: #c6d5f0;
    font-size: 16px;
}
.metric-card {
    background: #151e32;
    border: 1px solid #293650;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 10px;
}
.small-note {
    color: #aab7d0;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE --------------------

defaults = {
    "origin_results": [],
    "destination_results": [],
    "routes": [],
    "origin_point": None,
    "destination_point": None,
    "route_error": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------- HELPER FUNCTIONS --------------------

def geocode_address(address):
    """Find locations using OpenStreetMap Nominatim."""
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": address,
                "format": "jsonv2",
                "limit": 6,
                "addressdetails": 1
            },
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        return [
            {
                "name": item.get("display_name", "Unknown location"),
                "lat": float(item["lat"]),
                "lon": float(item["lon"])
            }
            for item in data
        ]

    except requests.RequestException as error:
        st.error(f"Manzil qidirishda tarmoq xatosi: {error}")
        return []
    except (ValueError, KeyError):
        st.error("Manzil ma'lumotlarini o'qib bo'lmadi.")
        return []


def get_routes(origin, destination):
    """Get available driving routes from the public OSRM demo."""
    coordinates = (
        f'{origin["lon"]},{origin["lat"]};'
        f'{destination["lon"]},{destination["lat"]}'
    )

    response = requests.get(
        f"{OSRM_URL}/{coordinates}",
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "true"
        },
        headers=HEADERS,
        timeout=45
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(
            "Bu ikki manzil orasida avtomobil yo'nalishi topilmadi."
        )

    return data["routes"]


def make_map():
    """Create a free OpenStreetMap map with no API key."""
    if st.session_state.routes:
        selected_index = st.session_state.get("selected_route", 0)
        routes = st.session_state.routes
        selected_index = min(selected_index, len(routes) - 1)
        route = routes[selected_index]

        coords = route["geometry"]["coordinates"]
        latitudes = [point[1] for point in coords]
        longitudes = [point[0] for point in coords]

        center = [
            (min(latitudes) + max(latitudes)) / 2,
            (min(longitudes) + max(longitudes)) / 2
        ]
        zoom = 7
    else:
        coords = []
        center = st.session_state.get("map_center", [41.3, 64.5])
        zoom = st.session_state.get("map_zoom", 5)

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        min_zoom=2,
        max_zoom=19,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True
    )

    # Draw route alternatives
    if st.session_state.routes:
        routes = st.session_state.routes
        selected_index = min(
            st.session_state.get("selected_route", 0),
            len(routes) - 1
        )

        for i, route in enumerate(routes):
            points = [
                [lat, lon]
                for lon, lat in route["geometry"]["coordinates"]
            ]

            folium.PolyLine(
                points,
                color="#2f80ff" if i == selected_index else "#8293ad",
                weight=7 if i == selected_index else 4,
                opacity=0.95 if i == selected_index else 0.6,
                tooltip=(
                    f"Tanlangan yo'nalish: {i + 1}"
                    if i == selected_index
                    else f"Muqobil yo'nalish: {i + 1}"
                )
            ).add_to(m)

        origin = st.session_state.origin_point
        destination = st.session_state.destination_point

        if origin and destination:
            folium.Marker(
                [origin["lat"], origin["lon"]],
                tooltip="Jo'nash manzili",
                popup=origin["name"],
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)

            folium.Marker(
                [destination["lat"], destination["lon"]],
                tooltip="Yetib borish manzili",
                popup=destination["name"],
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(m)

            m.fit_bounds([
                [min(latitudes), min(longitudes)],
                [max(latitudes), max(longitudes)]
            ], padding=(30, 30))

    # Required OpenStreetMap attribution is shown by Folium.
    return m


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## 🧭 SmartRoute UZ")
    st.caption("Bepul xarita va yo'nalish rejalashtirish")

    st.divider()

    map_view = st.radio(
        "Xarita ko'rinishi",
        ["Butun O'zbekiston", "Butun dunyo"],
        index=0
    )

    if st.button("🌍 Xarita ko'rinishini yangilash", use_container_width=True):
        st.session_state.routes = []
        st.session_state.origin_point = None
        st.session_state.destination_point = None

        if map_view == "Butun dunyo":
            st.session_state.map_center = [20, 0]
            st.session_state.map_zoom = 2
        else:
            st.session_state.map_center = [41.3, 64.5]
            st.session_state.map_zoom = 5

        st.rerun()

    st.divider()
    st.markdown("### 🚚 Safar xarajatlari")

    vehicle = st.selectbox(
        "Transport turi",
        ["Yengil avtomobil", "Yuk mashinasi (truck)"]
    )

    consumption = st.number_input(
        "Yoqilg'i sarfi (litr / 100 km)",
        min_value=1.0,
        max_value=150.0,
        value=25.0 if vehicle.startswith("Yuk") else 8.0,
        step=0.5
    )

    fuel_price = st.number_input(
        "Yoqilg'i narxi (so'm / litr)",
        min_value=0,
        value=12500,
        step=500
    )

    if vehicle.startswith("Yuk"):
        st.markdown("#### Yuk mashinasi ma'lumotlari")

        weight = st.number_input(
            "Umumiy og'irlik (tonna)",
            min_value=0.1,
            max_value=100.0,
            value=20.0,
            step=0.5
        )

        height = st.number_input(
            "Balandlik (metr)",
            min_value=1.0,
            max_value=10.0,
            value=4.0,
            step=0.1
        )

        length = st.number_input(
            "Uzunlik (metr)",
            min_value=1.0,
            max_value=40.0,
            value=16.5,
            step=0.5
        )

        st.warning(
            "Bu o'lchamlar faqat hisobot uchun. "
            "Hozirgi bepul marshrut serveri truck cheklovlarini "
            "kafolatli hisobga olmaydi."
        )

    st.divider()
    st.markdown(
        '<p class="small-note">'
        'Xarita: © OpenStreetMap contributors<br>'
        'Manzil qidiruvi: Nominatim<br>'
        'Marshrut: OSRM demo xizmati<br>'
        'Internet aloqasi kerak.'
        '</p>',
        unsafe_allow_html=True
    )


# -------------------- MAIN PAGE --------------------

st.markdown("""
<div class="hero">
    <div style="color:#78a9ff; letter-spacing:2px; font-weight:bold;">
        SMART LOGISTICS • NAVIGATION • UZBEKISTAN
    </div>
    <h1>🧭 SmartRoute UZ</h1>
    <p>
        Jo'nash va yetib borish manzillarini tanlang.
        Yo'nalish, masofa, vaqt va taxminiy yoqilg'i xarajatlarini
        bitta joyda ko'ring.
    </p>
</div>
""", unsafe_allow_html=True)

st.subheader("1. Safar yo'nalishini belgilang")
st.write(
    "Manzillarni kiriting va qidiruv natijalaridan kerakli joyni tanlang."
)

col1, col2 = st.columns(2)

with col1:
    origin_text = st.text_input(
        "🟢 Jo'nash manzili",
        value="Toshkent, O'zbekiston",
        placeholder="Masalan: Toshkent, O'zbekiston",
        key="origin_text"
    )

with col2:
    destination_text = st.text_input(
        "🔴 Yetib borish manzili",
        value="Samarqand, O'zbekiston",
        placeholder="Masalan: Samarqand, O'zbekiston",
        key="destination_text"
    )

if st.button("🔎 Manzillarni qidirish", type="primary", use_container_width=True):
    if not origin_text.strip() or not destination_text.strip():
        st.error("Ikkala manzilni ham kiriting.")
    else:
        with st.spinner("Manzillar OpenStreetMap orqali qidirilmoqda..."):
            st.session_state.origin_results = geocode_address(origin_text)
            st.session_state.destination_results = geocode_address(destination_text)

        st.session_state.routes = []
        st.session_state.origin_point = None
        st.session_state.destination_point = None

        if not st.session_state.origin_results:
            st.error(
                "Jo'nash manzili topilmadi. Aniqroq manzil yoki shahar nomini kiriting."
            )

        if not st.session_state.destination_results:
            st.error(
                "Yetib borish manzili topilmadi. Aniqroq manzil yoki shahar nomini kiriting."
            )

# -------------------- SELECT SEARCH RESULTS --------------------

if st.session_state.origin_results and st.session_state.destination_results:
    st.markdown("### Topilgan manzillardan tanlang")

    c1, c2 = st.columns(2)

    with c1:
        origin_index = st.selectbox(
            "Jo'nash joyi",
            options=list(range(len(st.session_state.origin_results))),
            format_func=lambda i: st.session_state.origin_results[i]["name"],
            key="origin_select"
        )

    with c2:
        destination_index = st.selectbox(
            "Borish joyi",
            options=list(range(len(st.session_state.destination_results))),
            format_func=lambda i: st.session_state.destination_results[i]["name"],
            key="destination_select"
        )

    if st.button(
        "🛣️ Eng qulay mavjud yo'nalishlarni hisoblash",
        type="primary",
        use_container_width=True
    ):
        origin = st.session_state.origin_results[origin_index]
        destination = st.session_state.destination_results[destination_index]

        try:
            with st.spinner("Yo'l variantlari hisoblanmoqda..."):
                routes = get_routes(origin, destination)

            # Sort by estimated duration, shortest first
            routes.sort(key=lambda r: r.get("duration", float("inf")))

            st.session_state.routes = routes
            st.session_state.origin_point = origin
            st.session_state.destination_point = destination
            st.session_state.selected_route = 0
            st.session_state.route_error = None

        except requests.RequestException:
            st.session_state.route_error = (
                "Marshrut serveriga ulanishda xatolik. "
                "Internetni tekshiring va birozdan so'ng qayta urinib ko'ring."
            )
        except ValueError as error:
            st.session_state.route_error = str(error)

if st.session_state.route_error:
    st.error(st.session_state.route_error)

# -------------------- ROUTE RESULTS --------------------

if st.session_state.routes:
    routes = st.session_state.routes

    st.subheader("2. Yo'nalish natijalari")

    route_labels = [
        (
            f"Variant {i + 1} — "
            f"{route['distance'] / 1000:.1f} km, "
            f"{route['duration'] / 3600:.1f} soat"
        )
        for i, route in enumerate(routes)
    ]

    selected_label = st.selectbox(
        "Yo'nalishni tanlang",
        options=route_labels,
        index=min(st.session_state.get("selected_route", 0), len(routes) - 1),
        key="route_choice"
    )

    selected_index = route_labels.index(selected_label)
    st.session_state.selected_route = selected_index
    route = routes[selected_index]

    distance_km = route["distance"] / 1000
    duration_hours = route["duration"] / 3600
    duration_minutes = round(route["duration"] / 60)

    hours = duration_minutes // 60
    minutes = duration_minutes % 60

    fuel_litres = distance_km * consumption / 100
    fuel_cost = fuel_litres * fuel_price

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("📏 Masofa", f"{distance_km:,.1f} km")

    with m2:
        st.metric("⏱️ Taxminiy vaqt", f"{hours} soat {minutes} daqiqa")

    with m3:
        st.metric("⛽ Yoqilg'i", f"{fuel_litres:,.1f} litr")

    with m4:
        st.metric("💰 Yoqilg'i xarajati", f"{fuel_cost:,.0f} so'm")

    st.info(
        "Safar vaqti taxminiy hisoblanadi. Real tirbandlik, ob-havo, "
        "to'xtashlar va yo'l yopilishi hisobga olinmagan."
    )

    st.subheader("3. Xarita")

    st.caption(
        "Xaritani sichqoncha bilan siljiting. "
        "G'ildirak yordamida kattalashtiring yoki kichraytiring. "
        "Dunyo bo'ylab ko'rish uchun kichraytiring."
    )

    route_map = make_map()
    st_folium(
        route_map,
        width=None,
        height=600,
        key="smart_route_map",
        returned_objects=[]
    )

    st.subheader("4. Yo'l bo'yicha ko'rsatmalar")

    steps_data = []
    legs = route.get("legs", [])

    for leg in legs:
        for step in leg.get("steps", []):
            maneuver = step.get("maneuver", {})
            road_name = step.get("name") or "Nomsiz yo'l"
            maneuver_type = maneuver.get("type", "davom eting")
            modifier = maneuver.get("modifier", "")

            instruction = f"{maneuver_type} {modifier}".strip()
            instruction = instruction.replace("_", " ").capitalize()

            steps_data.append({
                "Yo'l": road_name,
                "Harakat": instruction,
                "Masofa (km)": round(step.get("distance", 0) / 1000, 2),
                "Vaqt (daq.)": round(step.get("duration", 0) / 60, 1)
            })

    if steps_data:
        st.dataframe(
            pd.DataFrame(steps_data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("Ushbu marshrut uchun batafsil ko'rsatmalar mavjud emas.")

    report = pd.DataFrame([{
        "Transport": vehicle,
        "Jo'nash": st.session_state.origin_point["name"],
        "Manzil": st.session_state.destination_point["name"],
        "Masofa_km": round(distance_km, 2),
        "Taxminiy_vaqt_soat": round(duration_hours, 2),
        "Yoqilgi_litr": round(fuel_litres, 2),
        "Yoqilgi_narxi_som": fuel_price,
        "Taxminiy_xarajat_som": round(fuel_cost)
    }])

    st.download_button(
        "📥 Safar hisobotini CSV formatida yuklab olish",
        data=report.to_csv(index=False).encode("utf-8-sig"),
        file_name="smartroute_uz_report.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    # Initial map: show Uzbekistan, or the world when selected.
    if map_view == "Butun dunyo":
        initial_center = [20, 0]
        initial_zoom = 2
    else:
        initial_center = [41.3, 64.5]
        initial_zoom = 5

    st.subheader("2. Interaktiv xarita")
    st.caption(
        "Bu xaritada O'zbekiston va butun dunyoni ko'rishingiz mumkin. "
        "Manzillarni qidirganingizdan keyin marshrut shu yerda ko'rsatiladi."
    )

    initial_map = folium.Map(
        location=initial_center,
        zoom_start=initial_zoom,
        min_zoom=2,
        max_zoom=19,
        tiles="OpenStreetMap",
        control_scale=True
    )

    st_folium(
        initial_map,
        width=None,
        height=600,
        key="initial_world_map",
        returned_objects=[]
    )

st.divider()
st.caption(
    "SmartRoute UZ • OpenStreetMap ma'lumotlari • "
    "OSRM demo marshrutlari • O'quv loyihasi"
)
