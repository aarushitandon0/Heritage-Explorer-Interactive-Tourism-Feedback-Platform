import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from dotenv import load_dotenv
import os
import json
import snowflake.connector
import cloudinary
import cloudinary.uploader
load_dotenv(dotenv_path=r"C:\Users\AARUSHI TANDON\OneDrive\Python\snowflake_hackathon\.env") 

# Cloudinary config using env variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

@st.cache_resource(show_spinner=False)
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )
# ---------------- Streamlit Config ----------------
st.set_page_config(page_title="India's Living Heritage", layout="wide")
st.title("🇮🇳 India’s Living Heritage")
st.markdown("Celebrate India's cultural diversity — explore heritage cities, timeless art forms, and sustainable tourism tips.")

# ---------------- Load CSV ----------------
@st.cache_data(show_spinner=False)
def load_heritage_data():
    csv_path = r"C:\Users\AARUSHI TANDON\Downloads\India_Authentic_Heritage_Cities.csv"
    return pd.read_csv(csv_path)

df = load_heritage_data()

# ---------------- Sidebar Filters ----------------
st.sidebar.header("Filter by Art Form")
selected_art_forms = st.sidebar.multiselect("Select one or more art forms:", df["Art Forms / Culture"].unique())
filtered_df = df[df["Art Forms / Culture"].isin(selected_art_forms)] if selected_art_forms else df

# ---------------- Feedback DB Helpers ----------------
def save_feedback_to_snowflake(city, name, review, image_urls, rating=None, category=None):
    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        image_urls_json = json.dumps(image_urls) if image_urls else '[]'
        insert_sql = """
            INSERT INTO user_feedback (city, name, review, image_urls, rating, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (city, name, review, image_urls_json, rating, category))
        conn.commit()
        st.success("Feedback saved successfully!")
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
    finally:
        cursor.close()

def get_feedback_from_snowflake(city):
    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        select_sql = """
            SELECT name, review, image_urls, rating, category
            FROM user_feedback
            WHERE city = %s
            ORDER BY created_on DESC
        """
        cursor.execute(select_sql, (city,))
        rows = cursor.fetchall()
        feedback_list = []
        for name, review, image_urls_str, rating, category in rows:
            try:
                images = json.loads(image_urls_str) if image_urls_str else []
            except Exception:
                images = []
            feedback_list.append({
                "name": name,
                "review": review,
                "images": images,
                "rating": rating,
                "category": category
            })
        return feedback_list
    except Exception as e:
        st.error(f"Error loading feedback: {e}")
        return []
    finally:
        cursor.close()

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    " Heritage Map & Feedback",
    "Did you know??",
    "🗓️ Cultural Calendar", 
    " Responsible Tourism", 
    " Admin Dashboard",
    "Heritage Trivia Quiz"
])


with tab1:
    st.subheader("Cultural Heritage Map of India")

    folium_map = folium.Map(location=[22.0, 79.0], zoom_start=5)
    cluster = MarkerCluster().add_to(folium_map)

    for _, row in filtered_df.iterrows():
        popup_html = f"""
        <div style="width:200px;">
            <b>{row['Heritage Cities']}</b><br>
            <i>{row['Art Forms / Culture']}</i><br><br>
            <b>Tips:</b><br>{row['Tourism Tips']}
        </div>
        """
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=row['Heritage Cities'],  
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(cluster)

    map_data = st_folium(folium_map, width=1000, height=600)

    st.markdown("### 🔍 Selected City Details")
    selected_city_row = None

    if map_data and map_data.get("last_object_clicked"):
        st.success(" Marker clicked! Scroll down to view details & share your experience 👇")
        clicked_lat = map_data["last_object_clicked"]["lat"]
        clicked_lon = map_data["last_object_clicked"]["lng"]

        # Find city by matching coordinates with tolerance
        for _, row in filtered_df.iterrows():
            if abs(row["Latitude"] - clicked_lat) < 0.001 and abs(row["Longitude"] - clicked_lon) < 0.001:
                selected_city_row = row
                break

    if selected_city_row is not None:
        city_name = selected_city_row["Heritage Cities"]
        city_key = city_name.strip().lower().replace(" ", "")

        st.markdown(f"##  {city_name}")
        st.markdown(f"**Art Form:** {selected_city_row['Art Forms / Culture']}")
        st.info(f" **Tourism Tip:** {selected_city_row['Tourism Tips']}")

        # ---------------- Local Gallery ----------------
        image_root_dir = r"C:\Users\AARUSHI TANDON\OneDrive\Python\snowflake_hackathon\assets\images"
        city_folder_path = os.path.join(image_root_dir, city_key)

        if os.path.exists(city_folder_path):
            image_files = sorted([
                f for f in os.listdir(city_folder_path)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ])
            if image_files:
                st.markdown("#### Cultural Gallery (Static Images)")
                cols = st.columns(3)
                for idx, img_file in enumerate(image_files):
                    image_path = os.path.join(city_folder_path, img_file)
                    if os.path.exists(image_path):
                        with cols[idx % 3]:
                            st.image(image_path, use_container_width=True)
                    else:
                        st.warning(f" Could not find: {img_file}")
            else:
                st.warning("No images found in the local gallery folder!")
        else:
            st.info(" Local images gallery coming soon or use Cloudinary!")

        # ---------------- Feedback Form ----------------
        st.markdown("##  Share Your Experience")

        with st.form("feedback_form", clear_on_submit=True):
            name_input = st.text_input(" Your Name (optional)")
            review_input = st.text_area("Write your experience or review", max_chars=500)
            rating = st.radio("⭐ Rate your experience (out of five)", options=[1, 2, 3, 4, 5], horizontal=True)
            category = st.selectbox(" Select feedback category", options=[
                "General",
                "Hospitality",
                "Art & Culture",
                "Tourism Tips",
                "Other"
            ])
            uploaded_files = st.file_uploader(
                " Upload images (optional)", 
                type=["jpg", "jpeg", "png"], 
                accept_multiple_files=True
            )
            submitted = st.form_submit_button("🚀 Submit Feedback")

            if submitted:
                if review_input.strip() == "":
                    st.warning("Please write something before submitting.")
                else:
                    with st.spinner("Submitting your feedback..."):

                        uploaded_urls = []
                        for uploaded_file in uploaded_files:
                            try:
                                result = cloudinary.uploader.upload(
                                    uploaded_file,
                                    folder=f"heritage_feedback/{city_key}")
                                uploaded_urls.append(result["secure_url"])
                            except Exception as e:
                                st.error(f"❌ Failed to upload {uploaded_file.name}: {e}")

                    save_feedback_to_snowflake(
                        city=city_name,
                        name=name_input.strip() if name_input.strip() else "Anonymous",
                        review=review_input.strip(),
                        image_urls=uploaded_urls,
                        rating=rating,
                        category=category
                    )
                    st.success("✅ Thank you for sharing your experience!")

        # ---------------- Display Feedback ----------------
        st.markdown(f"###  Reviews for {city_name}")
        feedbacks = get_feedback_from_snowflake(city_name)

        if feedbacks:
            for fb in feedbacks:
                st.markdown(f"** {fb['name']} says:**")
                if fb.get("rating"):
                    st.markdown(f"⭐ Rating: {fb['rating']} / 5")
                if fb.get("category"):
                    st.markdown(f" Category: {fb['category']}")
                st.write(fb["review"])
                if fb["images"]:
                    cols = st.columns(3)
                    for idx, img_url in enumerate(fb["images"]):
                        with cols[idx % 3]:
                            try:
                                st.image(img_url, use_container_width=True)
                            except Exception:
                                st.error(f"❌ Could not load image: {img_url}")
                st.markdown("---")
        else:
            st.info("No reviews yet. Be the first to share your experience!")

    else:
        st.info("🔎 Click on a map marker to view cultural details and contribute your thoughts.")

with tab2:
    st.subheader("🤯 Did You Know? | Cultural Trivia Map")

    trivia_map = folium.Map(location=[22.0, 79.0], zoom_start=5, control_scale=True)
    trivia_cluster = MarkerCluster().add_to(trivia_map)

    did_you_know_dict = {
        "Pattadakal": "Where kings were crowned — a blend of North and South Indian temple styles.",
        "Aihole": "Known as the cradle of Indian architecture with 120+ temples.",
        "Lepakshi": "Has a hanging pillar that defies gravity!",
        "Srirangam": "The largest functioning Hindu temple complex in the world.",
        "Melkote": "A Bhakti movement stronghold rich in Iyengar traditions.",
        "Chanderi": "Famed for handwoven sarees once exported to royal courts.",
        "Kalna": "Home to 108 Shiva temples arranged in two concentric circles.",
        "Kushinagar": "Believed to be the place where Buddha attained Nirvana.",
        "Shekhawati": "Called the open art gallery of Rajasthan for its painted havelis.",
        "Kangra": "Origin of the delicate Kangra miniature painting style.",
        "Deogarh (Jharkhand)": "Major pilgrimage site during the Shravani Mela.",
        "Baripada": "Its Rath Yatra is pulled by women — a rare tradition!",
        "Dharanikota": "Capital of Satavahanas and ancient Buddhist hub.",
        "Bishnupur": "Famous for terracotta temples and Baluchari sarees.",
        "Lonar": "Crater lake formed by a meteor impact — both saline and alkaline.",
        "Dholavira": "Had water systems 4500 years ago — from the Harappan era!",
        "Rani ki Vav": "Stepwell built as an inverted temple dedicated to water.",
        "Champaner-Pavagadh": "India’s only preserved pre-Mughal Islamic city.",
        "Bateshwar": "200+ temples scattered across ravines — now being restored.",
        "Mandu": "City of Joy — romantic ruins and Afghan architecture.",
        "Ziro": "Apatani tribe’s home — known for eco-living and nose plugs.",
        "Unakoti": "Rock carvings of Shiva — literally ‘one less than a crore’.",
        "Tawang": "India’s largest monastery — second in the world.",
        "Karaikal": "Home of Karaikal Ammaiyar, one of the first female Shaiva saints.",
        "Narsinghgarh": "Picturesque palace-fort overlooking a scenic lake."
    }

    # Add markers
    for _, row in filtered_df.iterrows():
        city = row['Heritage Cities']
        if city in did_you_know_dict:
            trivia_text = did_you_know_dict[city]
            popup_html = f"""
            <div style="width:200px;">
                <b>{city}</b><br><br>
                <i>Did you know?</i><br>
                {trivia_text}
            </div>
            """
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="green", icon="info-sign")
            ).add_to(trivia_cluster)

    st_folium(trivia_map, width=1000, height=500)

    st.markdown("### 📜 Cultural Nuggets")
    for city, trivia in did_you_know_dict.items():
        st.markdown(f"**{city}**: {trivia}")


with tab3:
    st.markdown("**Cultural Calendar: Month-wise Festivals & Events**")
    st.markdown("Discover festivals and cultural events in the 25 heritage cities, organized by month:")

    cultural_events = {
        "january": [
            "Baripada Chhau Festival (Baripada)",
            "Lohri Celebrations (Shekhawati)",
            "Republic Day Cultural Fair (Lepakshi)"
        ],
        "february": [
            "Shekhawati Haat & Culture Festival (Shekhawati)",
            "Kangra Valley Miniature Art Festival (Kangra)",
            "Bishnupur Terracotta Music Fest (Bishnupur)"
        ],
        "march": [
            "Mandu Music and Architecture Festival (Mandu)",
            "Kushinagar Buddhist Peace Walk (Kushinagar)",
            "Srirangam Holi Pilgrimage Trail (Srirangam)"
        ],
        "april": [
            "Lonar Crater Earth Heritage Trek (Lonar)",
            "Aihole Chalukya Utsav (Aihole)",
            "Deogarh Spring Tribal Arts Showcase (Deogarh)"
        ],
        "may": [
            "Ziro Tribal Arts Residency (Ziro)",
            "Kalna Riverbank Music Rituals (Kalna)",
            "Champaner-Pavagadh Heritage Monsoon Prep (Champaner)"
        ],
        "june": [
            "Rani ki Vav Cultural Conservation Camp (Rani ki Vav)",
            "Melkote Vairamudi Festival (Melkote)",
            "Tawang Pre-Monsoon Crafts Retreat (Tawang)"
        ],
        "july": [
            "Chanderi Weaving Festival (Chanderi)",
            "Pattadakal Temple Dance Recitals (Pattadakal)",
            "Bateshwar Temple Water Festival (Bateshwar)"
        ],
        "august": [
            "Unakoti Rock Carvings Festival (Unakoti)",
            "Karaikal Coastal Heritage Fair (Karaikal)",
            "Narsinghgarh Tribal Folklore Month (Narsinghgarh)"
        ],
        "september": [
            "Dharanikota Buddhist Heritage Walk (Dharanikota)",
            "Shekhawati Folk Art Festival (Shekhawati)",
            "Kangra Valley Autumn Harvest (Kangra)"
        ],
        "october": [
            "Mandu Monsoon Music and Food (Mandu)",
            "Baripada Tribal Dance (Baripada)",
            "Lonar Crater Geology Seminar (Lonar)"
        ],
        "november": [
            "Ziro Music Festival (Ziro)",
            "Chanderi Handloom Expo (Chanderi)",
            "Kushinagar Peace Meditation (Kushinagar)"
        ],
        "december": [
            "Pattadakal Dance & Light Show (Pattadakal)",
            "Rani ki Vav Winter Cultural Fair (Rani ki Vav)",
            "Melkote Religious Pilgrimage (Melkote)"
        ]
    }

    selected_month = st.selectbox("Select Month", options=list(cultural_events.keys()), index=0)
    events_list = cultural_events[selected_month]

    st.write(f"### Festivals and Events in {selected_month.capitalize()}:")
    for event in events_list:
        st.write(f"- {event}")

with tab4:
    st.subheader("Travel Kindly: Responsible Tourism Tips 🌍")


    st.markdown("""
    India’s cultural sites are living legacies — not just photo ops. Here’s how you can explore respectfully:


    ### 🧭 General Tips
    -  **Leave no trace:** Don’t litter at heritage sites.
    -  **Be mindful:** Always ask before photographing people or rituals.
    -  **Respect customs:** Dress modestly and follow local etiquette.
    -  **Support artisans:** Buy handmade, not machine-made replicas.
    -  **Silence is golden:** Many sites are sacred — be quiet and reverent.


    ###  Sustainable Shopping
    -  **Buy local:** Choose crafts sold directly by artisans.
    -  **Avoid animal-based products:** Like ivory or fur.
    -  **Look for Geographical Indication (GI) tags:** They ensure authenticity.


    ###  Community-Based Tourism
    -  **Opt for guided walks with locals.**
    -  **Stay in homestays**, not big hotels.
    -  **Eat local:** Encourage traditional food joints and family kitchens.


    ###  Give Back
    -  Tip local performers, not just watch.
    -  Leave positive reviews for small businesses and artists.
    -  Volunteer if you revisit — many heritage sites welcome help.


    > “Take only memories, leave only footprints.” 🌾
    """)


    st.info("🤝 These tips are based on UNESCO guidelines and the Ministry of Tourism's 'Dekho Apna Desh' initiative.")
with tab5:
    st.subheader("📈 Admin Analytics: Feedback Insights")


    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                city,
                COUNT(*) AS total_reviews,
                ROUND(AVG(rating), 2) AS avg_rating
            FROM user_feedback
            GROUP BY city
            ORDER BY total_reviews DESC
        """)
        results = cursor.fetchall()
        analytics_df = pd.DataFrame(results, columns=["City", "Total Reviews", "Avg Rating"])


        if analytics_df.empty:
            st.info("No feedback data yet!")
        else:
            st.markdown("### 🔝 Most Reviewed Cities")
            st.dataframe(analytics_df, use_container_width=True)


            # Simple bar chart
            st.bar_chart(data=analytics_df.set_index("City")["Total Reviews"])


            st.markdown("### Cities with Low Rating (Avg < 3)")
            low_rated = analytics_df[analytics_df["Avg Rating"] < 3]
            if not low_rated.empty:
                st.warning("Some cities may need improvement:")
                st.dataframe(low_rated, use_container_width=True)
            else:
                st.success("All cities rated 3+ on average!")


    except Exception as e:
        st.error(f"Failed to fetch analytics: {e}")
    finally:
        cursor.close()


with tab6:
    # your trivia quiz code here
    st.header("Test your knowledge! 🇮🇳")

    trivia_questions = [
        {
            "question": "Which heritage city is famous for the Chola temples?",
            "answer": "Thanjavur"
        },
        {
            "question": "Rani ki Vav is located in which state?",
            "answer": "Gujarat"
        },
        {
            "question": "Which art form is Shekhawati known for?",
            "answer": "Frescoes"
        },
        {
            "question": "Which city is famous for its Terracotta temples?",
            "answer": "Bishnupur"
        }
    ]

    if 'trivia_index' not in st.session_state:
        st.session_state.trivia_index = 0
        st.session_state.score = 0
        st.session_state.answered = False

    q = trivia_questions[st.session_state.trivia_index]
    st.markdown(f"### Question {st.session_state.trivia_index + 1}: {q['question']}")

    user_answer = st.text_input("Your answer:")

    if st.button("Submit Answer") and not st.session_state.answered:
        if user_answer.strip().lower() == q['answer'].lower():
            st.success("🎉 Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Incorrect! The right answer is: {q['answer']}")
        st.session_state.answered = True

    if st.session_state.answered:
        if st.button("Next Question"):
            st.session_state.trivia_index += 1
            st.session_state.answered = False

            if st.session_state.trivia_index >= len(trivia_questions):
                st.write(f"Quiz finished! Your final score: {st.session_state.score} / {len(trivia_questions)}")
                # Reset for replay
                st.session_state.trivia_index = 0
                st.session_state.score = 0
st.markdown("---")
st.success("🌟 Built with ❤️ to showcase India’s timeless cultural legacy.")
