from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from googleapiclient.discovery import build

# Load the dataset
data_path = 'bollywood_songs_fixed_urls.csv'  # Ensure the correct path
songs_df = pd.read_csv(data_path)

# Create Flask app
app = Flask(__name__)
app.secret_key = 'YOUTUBE API KEY'  # Required for flashing messages 

# YouTube API Configuration
API_KEY = 'AIzaSyB25ysBKFGanrrAt2on2gKBd1BX4anR-SU'  # Replace with your actual API key  
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def fetch_youtube_url(query):
    """Fetch the first valid YouTube video URL based on the song name or author."""
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=1,  # Fetch only the top result
        type='video'  # Only return videos
    ).execute()

    # Extract the video ID and form the YouTube URL
    if 'items' in search_response and search_response['items']:
        video_id = search_response['items'][0]['id']['videoId']
        return f'https://www.youtube.com/watch?v={video_id}'
    return None

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Search route with recommendations
@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query').strip().lower()
    
    # Ensure lowercase matching for Song Name and Author
    search_results = songs_df[
        (songs_df['Song Name'].str.lower().str.contains(query, na=False)) | 
        (songs_df['Author'].str.lower().str.contains(query, na=False))
    ]

    if search_results.empty:
        flash("This song is not present in the dataset.", "error")
        return redirect(url_for('index'))

    # Get details of the first matching result
    first_result = search_results.iloc[0]
    genre = first_result['Genre']
    author = first_result['Author'].strip().lower()  # Standardizing case and whitespace

    # **Fixing Genre-Based Recommendations**
    genre_recommendations = songs_df[
        (songs_df['Genre'].str.lower() == genre.lower()) & 
        (songs_df['Song Name'] != first_result['Song Name'])
    ]

    # **Fixing Artist-Based Recommendations**
    artist_recommendations = songs_df[
        (songs_df['Author'].str.lower().str.strip() == author) & 
        (songs_df['Song Name'] != first_result['Song Name'])
    ]

    # Sampling only if there are enough songs available
    genre_recommendations = genre_recommendations.sample(n=min(10, len(genre_recommendations)), replace=False) if not genre_recommendations.empty else pd.DataFrame()
    artist_recommendations = artist_recommendations.sample(n=min(10, len(artist_recommendations)), replace=False) if not artist_recommendations.empty else pd.DataFrame()

    # Fetch YouTube URLs for each recommendation
    search_results['YouTube URL'] = search_results['Song Name'].apply(fetch_youtube_url)
    genre_recommendations['YouTube URL'] = genre_recommendations['Song Name'].apply(fetch_youtube_url)
    artist_recommendations['YouTube URL'] = artist_recommendations['Song Name'].apply(fetch_youtube_url)

    return render_template(
        'recommendations.html',
        search_results=search_results.to_dict(orient='records'),
        genre_recommendations=genre_recommendations.to_dict(orient='records'),
        artist_recommendations=artist_recommendations.to_dict(orient='records')  # Fixed variable name
    )

if __name__ == '__main__':
    app.run(debug=True)

