<img width="612" height="892" alt="image" src="https://github.com/user-attachments/assets/7d748fad-eb0f-49b8-b731-90240478bfdd" />
<img width="445" height="381" alt="image" src="https://github.com/user-attachments/assets/2df645bc-765b-4439-bfb6-17a0e354193d" />
<img width="613" height="83" alt="image" src="https://github.com/user-attachments/assets/4c86a4cc-1992-44de-9e8b-b5841dbaafce" />

# 🎵 Discord Music Bot

A modern **Discord Music Bot** featuring an interactive **Components V2 UI**, music queue system, audio effects, and a clean **Now Playing Interface**.

---

# ✨ Features

## 🎶 Music Features

* **YouTube Music Streaming** (`yt-dlp`)
* Song Queue System
* Song History (previous tracks)
* Loop Mode
* Pause / Resume
* Skip / Stop
* Automatic Voice Channel Join

---

## 🎛 Audio Effects

Change the sound in real time while music is playing:

| Effect    | Description                 |
| --------- | --------------------------- |
| Normal    | Default audio               |
| Nightcore | Faster speed & higher pitch |
| Vaporwave | Slower speed & lower pitch  |
| Earrape   | Extremely loud              |

Effects are applied **live**, without restarting the song.

---

## 🖥 Modern Discord UI

The bot uses **Discord Components V2** to provide a modern music panel.

### Now Playing Features

* Song Thumbnail
* Channel/Uploader Avatar
* Live Progress Bar
* Queue Information
* Song Duration
* Source Information
* Playback Status

### Interactive Controls

Directly below the music player:

* ⏮ Previous Song
* ⏯ Pause / Resume
* ⏭ Skip
* 🔁 Toggle Loop
* ⏹ Stop
* 🔌 Disconnect
* 🔗 Direct Song Link

---

## 🔒 Permission System

Only users listed in `allowed_users` can:

* Use commands
* Interact with buttons
* Control music playback

Unauthorized users will receive:

```txt
No permission.
```

---

# 📦 Installation

## 1. Clone the Repository

```bash
git clone [https://github.com/USERNAME/REPOSITORY.git](https://github.com/xlito08/Discord.py-Music-Bot)
cd REPOSITORY
```

---

## 2. Install Dependencies

```bash
pip install discord.py yt-dlp
```

---

## 3. Install FFmpeg

### Windows

Download FFmpeg and add it to your **PATH environment variable**.

### Linux

```bash
sudo apt install ffmpeg
```

### macOS

```bash
brew install ffmpeg
```

---

# ⚙️ Configuration

Create a file named:

```txt
config.json
```

With the following content:

```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN",
  "allowed_users": [
    123456789012345678
  ]
}
```

## Config Explanation

| Key             | Description                      |
| --------------- | -------------------------------- |
| `token`         | Your Discord bot token           |
| `allowed_users` | Users allowed to control the bot |

---

# 🚀 Running the Bot

Start the bot with:

```bash
python main.py
```

If everything works correctly, you should see:

```txt
Bot online as YourBotName
```

---

# 🎮 Slash Commands

## 🎵 Music Commands

| Command       | Description             |
| ------------- | ----------------------- |
| `/play <url>` | Add a song to the queue |
| `/skip`       | Skip the current song   |
| `/stop`       | Stop playback           |
| `/commands`   | Open the help menu      |
| `/restart`    | Restart the bot         |

---

# 🧠 How It Works

1. Use `/play`
2. The bot automatically joins your voice channel
3. Music is loaded using `yt-dlp`
4. Audio is streamed through **FFmpeg**
5. The **Now Playing Panel** updates live
6. The queue continues automatically

---

# 📁 Project Structure

```txt
project/
│── main.py
│── config.json
│── README.md
```

---

# 🛠 Built With

* Python
* discord.py
* yt-dlp
* FFmpeg
* Discord Components V2

---

# 🔥 Planned Features

* [ ] Spotify Support
* [ ] Playlist Support
* [ ] Queue Command
* [ ] Volume Command
* [ ] Lyrics Command
* [ ] Multi-Guild Save System

---

# ⚠️ Notes

* YouTube may occasionally rate-limit requests
* Livestreams may behave differently
* FFmpeg must be installed

---

# ⭐ Support

If you like this project:

**⭐ Star the repository on GitHub**
