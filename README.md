# Lichess Tournament Stats App

A Streamlit web app that visualizes player performance and statistics across Lichess tournaments. Built using the Lichess API, the app offers insights into tournament history, point trends, and player-specific results.

**Note:** This project is still under development.

## Live App

https://lichess.streamlit.app

## Features

- Filter tournaments by date
- View individual player stats and total points
- Plot cumulative performance over time
- Interactive, browser-based interface

## Run Locally

1. Clone the repository:
   ```
   git clone https://github.com/Houdineo/Lichess.git
   cd Lichess
   ```

2. (Optional) Create and activate a virtual environment:
   ```
   python -m venv lichess-env
   source lichess-env/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a secrets file:
   - Inside your project folder, create a `.streamlit` directory
   - Inside it, create a file named `secrets.toml` with the following content:
     ```
     LICHESS_API_KEY = "your_actual_api_key_here"
     ```

5. Run the app:
   ```
   streamlit run Lichess_app.py
   ```

## Security Notes

- API key is stored locally in `.streamlit/secrets.toml`
- This file is excluded from version control via `.gitignore`
- In production, Streamlit Cloud uses its own Secrets Manager

## Built With

- Streamlit
- Pandas
- Requests
- Lichess API

## License

MIT License. Use and modify freely with attribution.
