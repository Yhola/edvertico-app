# Edvertico

A view-only phone app for the Edvertico content plan: today's and tomorrow's posts, the 54-skill plan and the video scripts.

**Install:** open the site link in Chrome (Android) or Safari (iPhone), then choose *Install app* / *Add to Home Screen*. Sign in with the ID and password you were given.

## Security
- Everything except the logo and app code is encrypted with AES-256-GCM. The files in this repo (`content.enc.json`, `live.enc.json`) cannot be read without a valid ID and password.
- Each ID has its own password. Only a wrapped copy of the data key is stored per user, protected by PBKDF2-SHA256 (310,000 rounds). IDs are stored as SHA-256 hashes.
- No API keys, tokens or passwords are stored in this repo. The app cannot post, edit or delete anything.
- To remove someone's access, the owner removes their ID and rotates the data key (`tools/edv.py`).

`live.enc.json` is refreshed automatically several times a day.
