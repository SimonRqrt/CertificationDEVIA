import requests

CLIENT_ID = "152407"
CLIENT_SECRET = "8e091f0333d1bf6c807095b96abe5405f32b79ab"
ACCESS_TOKEN = "98e4bc7fee5e049c3567fc0d105942952f942d58"
REFRESH_TOKEN = "7444c0ce4ce6bbe348236e4ac2416f118401e8c9"

auth_url = "https://www.strava.com/oauth/token"

params = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN
}

response = requests.post(auth_url, data=params)
access_token = response.json().get("access_token")

print("Nouveau token d'accès :", access_token)
