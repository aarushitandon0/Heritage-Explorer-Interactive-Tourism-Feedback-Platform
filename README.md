# India's Living Heritage — Interactive Cultural Map & Feedback Platform

**Celebrate India's rich cultural diversity!**

---

This app was built as a submission for the **YourStory x Snowflake Hero Hackathon 2025** to promote responsible tourism and celebrate India's living cultural heritage using data-driven interactive visualizations.

---

## Project Overview

This Streamlit web app showcases 25 authentic heritage cities across India, highlighting their unique art forms, cultural trivia, month-wise festivals, and responsible tourism tips. It features:

- An interactive Folium map with clustered heritage city markers.
- Detailed city profiles with static image galleries and user-uploaded photos.
- User feedback submission with ratings, categories, and Cloudinary image uploads.
- Cultural trivia and fun facts to deepen appreciation.
- A month-wise calendar of festivals and cultural events.
- Responsible tourism guidelines based on UNESCO and Indian Ministry of Tourism recommendations.
- An admin dashboard to visualize user feedback and analytics.
- A cultural trivia quiz to engage and educate users.

---

## Demo

Watch the app walkthrough video here:  
[Google Drive Video Link](https://drive.google.com/file/d/1HEQM-mkakb0a7DgNIWjdoaCz_-uQAurC/view?usp=sharing)

---

## Features

- **Interactive Map:** View heritage cities clustered geographically with popup info.
- **City Details:** Explore art forms, tourism tips, and image galleries.
- **User Feedback:** Submit reviews with optional photos uploaded to Cloudinary.
- **Cultural Trivia:** Fun facts mapped geographically and listed.
- **Cultural Calendar:** Monthly festivals and events by city.
- **Responsible Tourism:** Practical tips to explore respectfully.
- **Admin Dashboard:** Analytics of feedback with review counts and average ratings.
- **Quiz:** Engage users with heritage-related trivia questions.

---

## Tech Stack

-  **Frontend & Backend:** [Streamlit](https://streamlit.io/) (Python)  
-  **Maps & Visualization:** [Folium](https://python-visualization.github.io/folium/) + [streamlit-folium](https://github.com/randyzwitch/streamlit-folium)  
-  **Data Storage:** [Snowflake](https://www.snowflake.com/) (for user feedback)  
-  **Image Hosting:** [Cloudinary](https://cloudinary.com/) (for user-uploaded photos)  
-  **Environment Variables:** [python-dotenv](https://pypi.org/project/python-dotenv/) for secure config management  
-  **Other:** [Pandas](https://pandas.pydata.org/) for data handling  

---

## Getting Started

### Prerequisites

- Python 3.8+
- Snowflake account & warehouse with `user_feedback` table set up
- Cloudinary account for image uploads
- `.env` file with your API keys and credentials
