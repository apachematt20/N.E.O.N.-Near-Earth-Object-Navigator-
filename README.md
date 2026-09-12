# ☄️ Near-Earth Asteroids (NEA) Monitoring Dashboard

An interactive and modern dashboard built with **Streamlit**, **Pandas**, and **Plotly** that queries the public NASA NeoWs (Near Earth Object Web Service) API to monitor near-Earth asteroids in real time for a specified date range.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0%2B-red.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Key Features

* **🔍 Custom Search:** Select a date range (up to a maximum of 7 days, as imposed by the NASA API) to analyze passing asteroids.
* **📊 Global Statistics (KPIs):** At-a-glance metrics showing the total number of detected asteroids, potential hazards, average speed, estimated average diameter, and minimum approach distance in Lunar Distances (LD).
* **📈 Interactive Scatter Plot:** Advanced visual analysis comparing distance from the Earth (on a logarithmic scale) with the estimated average diameter, clearly distinguishing safe asteroids from potentially hazardous ones.
* **📅 Daily Timeline:** A stacked bar chart to monitor the distribution of asteroids day by day.
* **📋 Data Table with Conditional Formatting:** A detailed table displaying all orbital and physical parameters, automatically highlighting potentially hazardous objects.
* **📥 Data Export:** Option to download the entire processed dataset directly as a CSV file.
* **🎨 "Deep Space" Design:** Meticulously crafted interface featuring a thematic color palette, modern typography, and native dark mode support.

---

## 🛠️ Tech Stack

* **Python** (version 3.8+)
* **Streamlit** - Framework for building interactive web apps
* **Pandas** - Data manipulation and cleaning
* **Plotly** - Interactive graphical visualizations
* **Requests** - HTTP calls to the REST API
* **NASA NeoWs API** - Official data source

---

## 🚀 Local Installation & Startup

Follow these steps to set up and run the project on your local machine:

### 1. Clone the repository
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO.git](https://github.com/YOUR_USERNAME/YOUR_REPO.git)
cd YOUR_REPO

2. Create and activate a virtual environment (recommended)
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

3. Install dependencies
pip install -r requirements.txt

4. Run the Streamlit application
streamlit run app.py

The application will automatically open in your browser at http://localhost:8501.

🔑 How to Get a NASA API Key

The application defaults to using the DEMO_KEY provided by NASA, which has restrictive hourly and daily rate limits (30 requests/hour, 50/day).
For optimal, uninterrupted usage:
- Visit the official NASA API Portal.
- Fill out the quick registration form with your first name, last name, and email.
- You will receive your personal alphanumeric API key.
- Enter your key directly into the designated field in the application sidebar.

☁️ Deployment on Streamlit Community Cloud

You can publish this dashboard online completely free and in just a few clicks by connecting it to GitHub:
- Push your code to a public GitHub repository (make sure it contains app.py and requirements.txt).
- Go to Streamlit Community Cloud and sign in with your GitHub account.
- Click on New app.
 -Select your repository, reference branch (main), and main file path (app.py).
 - Click Deploy! Your dashboard will be online and publicly accessible.

📄 License
Distributed under the MIT License. See LICENSE for more information.
