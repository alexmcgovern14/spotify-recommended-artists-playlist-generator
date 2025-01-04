# Artist recommendation engine for Spotify: playlist generator 🎧

This project is a Python-based tool which generates a Spotify playlist with personalized artist recommendations based on user's listening history. 

It connects user's top artists data with the more comprehensive MusicBrainz dataset, to fetch similar artists for each favourite, before returning to Spotify API to extract each recommended artist's top song and output as a Spotify playlist added to user's library.

[Spotify playlist: Recommended artists 🧠](https://open.spotify.com/playlist/7JbjUVGzu2E6H8xffw4jzG?si=d92c9844dfb84b29)
![Example image](recommended_artists_playlist_img.png)

## Features
* Fetches user's top 100 artists from Spotify API
* Maps Spotify artist IDs to MusicBrainz IDs (MBID) by extracting Spotify ID from free streaming links within artist url table [(Schema)](https://musicbrainz.org/doc/MusicBrainz_Database/Schema%23Artist#Overview)
    * CSV output of 100-artist longlist with MBID, Spotify ID: 'artists_with_mbids.csv'
* Extracts similar artists for user's top 50 artists using the ListenBrainz API, mode is configurable (easy/medium/hard)
* References similar artists against original 100-artist longlist to remove duplicates
* Fetches top song for every recommended artist remaining as a sample of their work
    * CSV output of list of similar artists and tracks with Spotify IDs: 'similar_artists_results.csv'
* Creates Spotify playlist with top tracks from recommended artists
* Spotify playlist "Recommended artists 🎧" added to user's Spotify library

## Setup
* Create a Spotify Developer account and register a new Web API application.
* Clone this repository
* Install required dependencies: pip install -r requirements.txt
* Set up a .env file in the project root with your Spotify API credentials:
```text
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
REFRESH_TOKEN=your_refresh_token
```
* Install required packages: pip install -r requirements.txt

## Usage
* Run the script: python mbid_similar_artists.py
* The script will generate a new Spotify playlist with recommended tracks and output two CSV files with artist and track information.

