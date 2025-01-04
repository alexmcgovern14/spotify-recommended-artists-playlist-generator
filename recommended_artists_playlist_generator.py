import requests
import base64
import csv
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Spotify API credentials loaded from the environment
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('SPOTIFY_REFRESH_TOKEN')

def refresh_access_token():
    """Refresh the access token using the refresh token."""
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error refreshing token: {response.status_code}, {response.text}")

def get_top_artists(limit=50, total_artists=100):
    """Get the user's top artists over the long term."""
    access_token = refresh_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    all_artists = []
    for offset in range(0, total_artists, limit):
        params = {
            'limit': limit,
            'offset': offset,
            'time_range': 'long_term'
        }
        response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
        if response.status_code == 200:
            all_artists.extend(response.json().get('items', []))
        else:
            print(f"Error fetching top artists: {response.status_code}, {response.text}")
            return []
    return all_artists

def get_artist_mbid(spotify_artist_id):
    """Fetch the MusicBrainz ID for a given Spotify Artist ID."""
    spotify_url = f"https://open.spotify.com/artist/{spotify_artist_id}"
    base_url = "https://musicbrainz.org/ws/2/url/"
    headers = {
        'User-Agent': 'MyMusicApp/1.0.0 (your@email.com)'
    }
    params = {
        "resource": spotify_url,
        "fmt": "json",
        "inc": "artist-rels"
    }
    retries = 3
    while retries > 0:
        try:
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if "relations" in data:
                for relation in data["relations"]:
                    if relation.get("type") == "free streaming" and "artist" in relation:
                        return relation["artist"].get("id", "Not Found")
            return "Not Found"
        except requests.exceptions.HTTPError as e:
            if response.status_code in [404, 503]:
                retries -= 1
                time.sleep(1)
            else:
                print(f"HTTP Error: {e}")
                return "Not Found"
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return "Not Found"
    return "Service Unavailable"

def get_similar_artists(mbid):
    """Fetch similar artists from ListenBrainz API for a given MBID."""
    BASE_URL = "https://api.listenbrainz.org"
    params = {
        "mode": "medium",
        "max_similar_artists": 3,
        "max_recordings_per_artist": 1,
        "pop_begin": 0,
        "pop_end": 100
    }
    try:
        response = requests.get(
            f"{BASE_URL}/1/lb-radio/artist/{mbid}",
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if not data:
                print(f"No similar artists found for MBID {mbid}")
                return []
            similar_artists = []
            for artist_data in data.values():
                if artist_data and len(artist_data) > 0:
                    artist = {
                        "name": artist_data[0]["similar_artist_name"],
                        "mbid": artist_data[0]["similar_artist_mbid"],
                        "listen_count": artist_data[0]["total_listen_count"],
                        "spotify_url": get_spotify_url(artist_data[0]["similar_artist_mbid"])
                    }
                    similar_artists.append(artist)
            return similar_artists[:3]
        print(f"API request failed with status code: {response.status_code}")
        return []
    except Exception as e:
        print(f"Error fetching similar artists for MBID {mbid}: {e}")
        return []

def get_spotify_url(mbid):
    """Fetch the Spotify free streaming URL for a given MusicBrainz MBID."""
    base_url = f"https://musicbrainz.org/ws/2/artist/{mbid}"
    params = {"inc": "url-rels", "fmt": "json"}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for relation in data.get("relations", []):
                if relation["type"] == "free streaming" and relation["url"]["resource"].startswith("https://open.spotify.com/artist/"):
                    return relation["url"]["resource"].replace("https://open.spotify.com/artist/", "")
        return None
    except Exception as e:
        print(f"Error fetching Spotify URL for MBID {mbid}: {e}")
        return None

def search_spotify_by_name(artist_name):
    """Search for an artist's top track by artist name."""
    access_token = refresh_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    search_url = 'https://api.spotify.com/v1/search'
    search_params = {
        'q': artist_name,
        'type': 'track',
        'limit': 1
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=search_params)
        response.raise_for_status()
        tracks = response.json()['tracks']['items']
        if tracks:
            return {
                'name': tracks[0]['name'],
                'id': tracks[0]['id'],
                'preview_url': tracks[0]['preview_url']
            }
    except Exception as e:
        print(f"Error searching for track by artist name {artist_name}: {e}")
    
    return None

def get_top_track(artist_id, artist_name, retries=5):
    access_token = refresh_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks'
    params = {'market': 'US'}
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            tracks = response.json()['tracks']
            if tracks:
                return {
                    'name': tracks[0]['name'],
                    'id': tracks[0]['id'],
                    'preview_url': tracks[0]['preview_url']
                }
        except Exception as e:
            print(f"Error fetching top track for artist {artist_id}: {e}")
            time.sleep(2 ** attempt)
    
    # If no tracks found, try searching for the artist
    track = search_spotify_by_name(artist_name)
    if track:
        return track
    
    # If search fails, try to get any track by the artist
    try:
        search_url = 'https://api.spotify.com/v1/search'
        search_params = {'q': f'artist:"{artist_name}"', 'type': 'track', 'limit': 1}
        response = requests.get(search_url, headers=headers, params=search_params)
        response.raise_for_status()
        tracks = response.json()['tracks']['items']
        if tracks:
            return {
                'name': tracks[0]['name'],
                'id': tracks[0]['id'],
                'preview_url': tracks[0]['preview_url']
            }
    except Exception as e:
        print(f"Error searching for any track by artist {artist_name}: {e}")
    
    return None

def create_spotify_playlist(track_ids):
    access_token = refresh_access_token()
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    user_id = requests.get('https://api.spotify.com/v1/me', headers=headers).json()['id']
    playlist_data = {
        'name': 'Recommended artists 🎧',
        'description': 'Based on your favourite artists, these are the musicians that like-minded fans also listen to. One track per artist.',
        'public': False
    }
    playlist = requests.post(f'https://api.spotify.com/v1/users/{user_id}/playlists', headers=headers, json=playlist_data).json()
    
    playlist_id = playlist['id']
    unique_track_ids = list(set(track_ids))  # Remove duplicates
    requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers, json={'uris': [f'spotify:track:{track_id}' for track_id in unique_track_ids]})
    
    return playlist['external_urls']['spotify']

def main():
    try:
        print("Fetching top 100 Spotify artists...")
        top_artists = get_top_artists(total_artists=100)
        if not top_artists:
            print("No top artists found.")
            return

        known_artist_ids = set(artist['id'] for artist in top_artists)
        known_artist_names = set(artist['name'] for artist in top_artists)

        print("Mapping Spotify Artist IDs to MusicBrainz IDs for first 50 artists...")
        results = []
        for artist in top_artists[:50]:
            name = artist.get('name', "Unknown")
            spotify_id = artist.get('id', "")
            print(f"Processing artist: {name}")
            mbid = get_artist_mbid(spotify_id)
            results.append({
                "name": name,
                "spotify_id": spotify_id,
                "mbid": mbid,
                "similar_artists": []
            })
            time.sleep(1)

        mbid_output_file = 'artists_with_mbids.csv'
        with open(mbid_output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "SpotifyID", "MBID"])
            for result in results:
                writer.writerow([result["name"], result["spotify_id"], result["mbid"]])
        print(f"Mapped MBIDs have been written to '{mbid_output_file}'.")

        print("Fetching similar artists from ListenBrainz and their top tracks from Spotify...")
        similar_artists_output = 'similar_artists_results.csv'
        track_ids = []
        with open(similar_artists_output, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Original Artist", "Original MBID", "Similar Artist", "Similar Artist MBID", "Listen Count", "Spotify Artist ID", "Top Track Name", "Top Track ID", "Top Track Preview URL"])
            for result in results:
                if result["mbid"] != "Not Found" and result["mbid"] != "Service Unavailable":
                    similar_artists = get_similar_artists(result["mbid"])
                    result["similar_artists"] = similar_artists
                    for similar in similar_artists:
                        spotify_id = similar.get("spotify_url")
                        if spotify_id not in known_artist_ids and similar["name"] not in known_artist_names:
                            top_track = get_top_track(spotify_id, similar["name"]) if spotify_id else None
                            if top_track and top_track['id']:
                                track_ids.append(top_track['id'])
                            writer.writerow([
                                result["name"],
                                result["mbid"],
                                similar["name"],
                                similar["mbid"],
                                similar["listen_count"],
                                spotify_id,
                                top_track['name'] if top_track else "",
                                top_track['id'] if top_track else "",
                                top_track['preview_url'] if top_track else ""
                            ])
                time.sleep(1)
        print(f"Similar artists and their top tracks have been written to '{similar_artists_output}'.")
        
        if track_ids:
            playlist_url = create_spotify_playlist(track_ids)
            print(f"Spotify playlist created: {playlist_url}")
        else:
            print("No tracks found to create a playlist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
