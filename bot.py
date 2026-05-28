import discord
from discord.ext import commands
from discord import ui
import yt_dlp
import asyncio
import logging
import os
import sys
import json
import time

logging.basicConfig(level=logging.INFO)

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN         = config["token"]
ALLOWED_USERS = config["allowed_users"]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(intents=intents)
BOT_START_TIME = 0.0

class Emojis:
    UTILITY    = "<:Icons_utility:1372374976577011763>"
    HOME       = "<:icons_home:1372374981203333140>"
    CLOCK      = "<:icon_clock:1372375013466050560>"
    SPEAKER    = "<:Icon_Speaker:1372375018344022029>"
    MUSIC      = "<:icon_music:1372375041542721638>"
    PLAY       = "<:icon_play:1372375062136623104>"
    LINK       = "<:Icon_Link:1372375084987187292>"
    TICK       = "<:icon_tick:1372375089668161597>"
    CROSS      = "<:icon_cross:1372375094336425986>"
    SETTINGS   = "<:icon_settings:1373173980466384967>"
    USER       = "<:user:1373171037998682214>"
    PING       = "<:icon_ping:1373948868114513972>"
    ARROW      = "<:GC_z_icon_rightarrow:1374279174751125534>"
    STAR       = "<:star:1376600544847593482>"
    PAUSED     = "<:icons_pause:1381535606382792726>"
    PLAYING    = "<:icon_pause:1372375109461082112>"
    LOOP_ICON  = "<:Icon_Loop:1372375099394490388>"
    DANGER     = "<:icon_danger:1373170993236803688>"
    DOT        = "<:dot:1479361908766281812>"
    ARROW_HELP = "<:arrow:1479361920254345391>"
    BUTTERFLY  = "<a:ButterflyWhite:1479361913812025386>"
    STOP_NEW   = "<:music_stop:1373925462828650592>"
    SKIP_NEW   = "<:music_skip:1373925947685998653>"
    REWIND     = "<:rewind:1373926276683005975>"
    IGNORE     = "<:icon_ignore:1372375104100765706>"

guild_music_data = {}

YDL_OPTIONS = {
    "format": "bestaudio/best", "quiet": True,
    "default_search": "ytsearch", "noplaylist": True,
    "nocheckcertificate": True,
    "extractor_args": {"youtube": {"player_client": ["android", "web"]}}
}

# ── Effects Map ───────────────────────────────────────────────────────────────
EFFECTS = {
    "none":      "",
    "nightcore": "atempo=1.06,asetrate=48000*1.25",
    "vaporwave": "atempo=0.8,asetrate=48000*0.8",
    "earrape":   "volume=10"
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_guild_data(guild_id: int) -> dict:
    if guild_id not in guild_music_data:
        guild_music_data[guild_id] = {
            "queue": [], "history": [], "voice": None, "volume": 0.5,
            "now_playing": None, "text_channel": None, "loop_id": 0,
            "effect": "none", "restarting": False, "loop_mode": False
        }
    return guild_music_data[guild_id]

def format_time(seconds: int) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def format_duration_short(seconds: int) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

def format_uptime() -> str:
    diff = int(time.time() - BOT_START_TIME)
    d, r  = divmod(diff, 86400)
    h, r  = divmod(r, 3600)
    m, s  = divmod(r, 60)
    return f"{d}d {h}h {m}m {s}s"

async def ensure_voice(interaction: discord.Interaction):
    data = get_guild_data(interaction.guild.id)
    if not interaction.user.voice: return None
    if not data["voice"] or not data["voice"].is_connected():
        data["voice"] = await interaction.user.voice.channel.connect()
    return data["voice"]

async def fetch_channel_avatar(uploader_url: str | None) -> str | None:
    if not uploader_url: return None
    try:
        def _fetch():
            opts = {"quiet": True, "extract_flat": True, "skip_download": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(uploader_url, download=False)
                if not info: return None
                thumbs = info.get("thumbnails", [])
                square = [t for t in thumbs if t.get("width") and t.get("height")
                          and t["width"] == t["height"] and t.get("url")]
                if square: return max(square, key=lambda t: t.get("width", 0))["url"]
                return thumbs[0]["url"] if thumbs else None
        return await asyncio.to_thread(_fetch)
    except Exception: return None

# ═══════════════════════════════════════════════════════════════════════════════
# VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class InfoView(ui.LayoutView):
    def __init__(self, text: str):
        super().__init__(timeout=60)
        c = ui.Container(accent_color=None)
        c.add_item(ui.TextDisplay(text))
        self.add_item(c)

class NowPlayingView(ui.LayoutView):
    def __init__(self, song: dict, progress: str, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.container = ui.Container(accent_color=discord.Color.from_str("#2b2d31"))
        self._build(song, progress)
        self.add_item(self.container)

    def _build(self, song: dict, progress: str):
        self.container.clear_items()
        title = f"## <:icon_music:1372375041542721638> Now Playing\n## __**{song['title']}**__"
        thumb = song.get("channel_avatar") or song.get("thumbnail")
        if thumb:
            self.container.add_item(ui.Section(ui.TextDisplay(title), accessory=ui.Thumbnail(media=thumb, description="Channel")))
        else: self.container.add_item(ui.TextDisplay(title))

        self.container.add_item(ui.Separator())
        if song.get("thumbnail"):
            self.container.add_item(ui.MediaGallery(discord.MediaGalleryItem(media=song["thumbnail"], description="Song Image")))
            self.container.add_item(ui.Separator())

        data = get_guild_data(self.guild_id)
        q_count = len(data.get("queue", []))
        duration = format_duration_short(song.get("duration", 0))
        vc = data.get("voice")
        is_paused = vc.is_paused() if vc else False
        status_emoji = Emojis.PAUSED if is_paused else Emojis.PLAYING
        status_text = "paused" if is_paused else "playing"

        stats = (
            f"<:icons_pings:1373173701704683540> **Status:** {status_text}\n"
            f"<:Icon_Loop:1372375099394490388> **Loop:** {'An' if data.get('loop_mode') else 'Aus'}\n"
            f"<:icon_clock:1372375013466050560> **Duration:** {duration}\n"
            f"<:profile_icons:1398702779320766596> **Uploader:** {song.get('uploader', 'Unknown')}\n"
            f"<:icon_Extra:1372375162640535653> **Source:** {song.get('extractor', 'youtube').capitalize()}\n"
            f"<:docs:1372529980331921532> **Queue:** {q_count} songs in queue"
        )
        self.container.add_item(ui.TextDisplay(stats))
        self.container.add_item(ui.Separator())
        self.container.add_item(ui.TextDisplay(f"**<:icon_question:1372528294494212107> Progress**\n{progress}"))
        self.container.add_item(ui.Separator())

        # ── ACTIONS ──
        self.container.add_item(ui.TextDisplay(f"**<:Icons_utility:1372374976577011763> Actions**"))
        vc = data.get("voice")
        is_paused = vc.is_paused() if vc else False
        
        btn_row1 = ui.ActionRow(
            ui.Button(style=discord.ButtonStyle.secondary, custom_id="btn_prev", emoji=Emojis.REWIND),
            ui.Button(style=discord.ButtonStyle.secondary, custom_id="btn_pause", emoji=Emojis.PLAYING if is_paused else Emojis.PLAY),
            ui.Button(style=discord.ButtonStyle.secondary, custom_id="btn_skip", emoji=Emojis.SKIP_NEW),
            ui.Button(style=discord.ButtonStyle.secondary, custom_id="btn_loop", emoji=Emojis.LOOP_ICON),
            ui.Button(label="Link", style=discord.ButtonStyle.link, url=song.get('original_url', 'https://youtube.com')),
        )
        btn_row1.children[0].callback = self._prev_cb
        btn_row1.children[1].callback = self._pause_cb
        btn_row1.children[2].callback = self._skip_cb
        btn_row1.children[3].callback = self._loop_cb
        self.container.add_item(btn_row1)

        btn_row2 = ui.ActionRow(
            ui.Button(style=discord.ButtonStyle.secondary, custom_id="btn_stop", emoji=Emojis.STOP_NEW),
            ui.Button(style=discord.ButtonStyle.secondary, custom_id="btn_dc", emoji=Emojis.IGNORE),
        )
        btn_row2.children[0].callback = self._stop_cb
        btn_row2.children[1].callback = self._dc_cb
        self.container.add_item(btn_row2)
        self.container.add_item(ui.Separator())

        # ── EFFECTS ──
        self.container.add_item(ui.TextDisplay(f"**<:icon_giveaway:1372375046332485663> Effects**"))
        effect_select = ui.Select(
            placeholder="Select an effect...",
            options=[
                discord.SelectOption(label="Alle Effekte entfernen", value="none", description="Standard Sound"),
                discord.SelectOption(label="Nightcore", value="nightcore", description="Schneller & Hoeher"),
                discord.SelectOption(label="Vaporwave", value="vaporwave", description="Langsamer & Tiefer"),
                discord.SelectOption(label="Earrape", value="earrape", description="EXTREM LAUT"),
            ],
            custom_id="sel_effect"
        )
        effect_select.callback = self._effect_cb
        self.container.add_item(ui.ActionRow(effect_select))
        self.container.add_item(ui.Separator())
        self.container.add_item(ui.TextDisplay("-# Musik-Bot · Components V2"))

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in ALLOWED_USERS:
            await interaction.response.send_message(view=InfoView("No permission."), ephemeral=True); return False
        return True

    async def _pause_cb(self, interaction: discord.Interaction):
        if not await self._check(interaction): return
        vc = get_guild_data(self.guild_id).get("voice")
        if vc and vc.is_playing(): vc.pause(); await interaction.response.send_message(view=InfoView("Pausiert."), ephemeral=True)
        elif vc and vc.is_paused(): vc.resume(); await interaction.response.send_message(view=InfoView("Fortgesetzt."), ephemeral=True)
        else: await interaction.response.send_message(view=InfoView("Es laeuft nichts."), ephemeral=True)

    async def _skip_cb(self, interaction: discord.Interaction):
        if not await self._check(interaction): return
        if vc := get_guild_data(self.guild_id).get("voice"): vc.stop()
        await interaction.response.send_message(view=InfoView("Uebersprungen."), ephemeral=True)

    async def _stop_cb(self, interaction: discord.Interaction):
        if not await self._check(interaction): return
        data = get_guild_data(self.guild_id); data["queue"].clear()
        if vc := data.get("voice"): vc.stop()
        await interaction.response.send_message(view=InfoView("Gestoppt."), ephemeral=True)

    async def _dc_cb(self, interaction: discord.Interaction):
        if not await self._check(interaction): return
        data = get_guild_data(self.guild_id)
        if (vc := data.get("voice")) and vc.is_connected(): await vc.disconnect(); data["voice"] = None
        await interaction.response.send_message(view=InfoView("Vom Voice getrennt."), ephemeral=True)

    async def _prev_cb(self, interaction: discord.Interaction):
        if not await self._check(interaction): return
        data = get_guild_data(self.guild_id)
        if not data["history"]:
            await interaction.response.send_message(view=InfoView("Keine vorherigen Lieder."), ephemeral=True); return
        if data["now_playing"]: data["queue"].insert(0, data["now_playing"]["original_url"])
        last_url = data["history"].pop()
        data["queue"].insert(0, last_url)
        if vc := data.get("voice"): vc.stop()
        await interaction.response.send_message(view=InfoView("Vorheriges Lied."), ephemeral=True)

    async def _loop_cb(self, interaction: discord.Interaction):
        if not await self._check(interaction): return
        data = get_guild_data(self.guild_id)
        data["loop_mode"] = not data["loop_mode"]
        await interaction.response.send_message(view=InfoView(f"Loop {'aktiviert' if data['loop_mode'] else 'deaktiviert'}."), ephemeral=True)

    async def _effect_cb(self, interaction: discord.Interaction):
        if not await self._check(interaction): return
        effect = interaction.data["values"][0]
        data = get_guild_data(self.guild_id)
        data["effect"] = effect
        await interaction.response.send_message(view=InfoView(f"Effekt gewechselt: {effect}"), ephemeral=True)
        
        # Wiedergabe mit neuem Filter neu starten
        vc = data.get("voice")
        if vc and data["now_playing"]:
            data["restarting"] = True
            vc.stop()
            await apply_audio_source(self.guild_id, offset=data["now_playing"]["elapsed"])
            data["restarting"] = False

# ── Commands Help View ────────────────────────────────────────────────────────
class CommandsView(ui.LayoutView):
    def __init__(self, page: str = "overview"):
        super().__init__(timeout=300)
        self.page = page; self.container = ui.Container(accent_color=None); self._build(); self.add_item(self.container)

    def _build(self):
        self.container.clear_items()
        self.container.add_item(ui.TextDisplay("### <:icons_global:1372374990363562126> Bot Command Help Section"))
        self.container.add_item(ui.TextDisplay("Willkommen im Hilfe-Menü!\nHier findest du alle Funktionen des Bots übersichtlich aufgelistet."))
        self.container.add_item(ui.Separator())
        if self.page == "overview":
            ping = round(bot.latency * 1000); servers = len(bot.guilds); uptime = format_uptime()
            ov_text = f"**<:icons_home:1372374981203333140> Overview**\nCommands: **7**\nServers: **{servers}**\nUptime: **{uptime}**\nPing: **{ping}ms**"
            self.container.add_item(ui.TextDisplay(ov_text))
            self.container.add_item(ui.Separator())
            cat_text = f"**<:icon_ignore:1372375104100765706> Categories**\nMusic Commands: **6**\nBasic Commands: **1**"
            self.container.add_item(ui.TextDisplay(cat_text))
        elif self.page == "music":
            mu_text = "**<:icon_music:1372375041542721638> Music Commands**\n> `/play`\n> `/skip`\n> `/stop`\n> `/pause`\n> `/resume`\n> `/disconnect`"
            self.container.add_item(ui.TextDisplay(mu_text))
        elif self.page == "system":
            sys_text = "**<:icon_settings:1372375191405199480> Basic Commands**\n> `/commands`\n> `/restart`"
            self.container.add_item(ui.TextDisplay(sys_text))
        select = ui.Select(
            placeholder="Select a category...",
            options=[
                discord.SelectOption(label="Overview", value="overview", emoji=Emojis.HOME),
                discord.SelectOption(label="Music",    value="music",    emoji=Emojis.MUSIC),
                discord.SelectOption(label="Basic",    value="system",   emoji=Emojis.SETTINGS),
            ],
            custom_id="nav_select"
        )
        select.callback = self._nav_callback
        self.container.add_item(ui.ActionRow(select))
        self.container.add_item(ui.Separator())
        self.container.add_item(ui.TextDisplay("-# Try: </play:0> · </skip:0>"))

    async def _nav_callback(self, interaction: discord.Interaction):
        self.page = interaction.data["values"][0]
        self._build()
        await interaction.response.edit_message(view=self)

# ── Global Check ──────────────────────────────────────────────────────────────
async def global_check(interaction: discord.Interaction) -> bool:
    if interaction.command and interaction.command.name == "commands": return True
    if interaction.user.id not in ALLOWED_USERS:
        await interaction.response.send_message(view=InfoView("No permission."), ephemeral=True); return False
    return True
bot.tree.interaction_check = global_check

# ═══════════════════════════════════════════════════════════════════════════════
# PLAYBACK LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

async def apply_audio_source(guild_id: int, offset: int = 0):
    data = get_guild_data(guild_id); vc = data["voice"]; song = data["now_playing"]
    if not vc or not song: return

    effect_key = data.get("effect", "none")
    filter_str = EFFECTS.get(effect_key, "")
    
    ffmpeg_opts = {
        "before_options": f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {offset}",
        "options": f"-vn -loglevel error"
    }
    if filter_str:
        ffmpeg_opts["options"] += f' -af "{filter_str}"'

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song["url"], **ffmpeg_opts), volume=data["volume"])
    
    def after_callback(e):
        if data.get("restarting"): return
        if data["now_playing"]:
            if data.get("loop_mode"):
                data["queue"].insert(0, data["now_playing"]["original_url"])
            else:
                data["history"].append(data["now_playing"]["original_url"])
                if len(data["history"]) > 20: data["history"].pop(0)
        asyncio.run_coroutine_threadsafe(_play_next(guild_id), bot.loop)

    vc.play(source, after=after_callback)

async def _play_next(guild_id: int):
    data = get_guild_data(guild_id)
    if not data["queue"]: data["now_playing"] = None; return
    url = data["queue"].pop(0)
    try:
        def extract():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl: return ydl.extract_info(url, download=False)
        info = await asyncio.to_thread(extract)
        if "entries" in info: info = info["entries"][0]
        audio_url = info["url"]
    except Exception: await _play_next(guild_id); return

    uploader_url = info.get("uploader_url") or info.get("channel_url")
    avatar = await fetch_channel_avatar(uploader_url)
    data["now_playing"] = {
        "title": info.get("title", "Unknown"), "url": audio_url, "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail"), "uploader": info.get("uploader"),
        "extractor": info.get("extractor", "youtube"), "channel_avatar": avatar, "elapsed": 0,
        "original_url": url
    }
    data["loop_id"] += 1
    await apply_audio_source(guild_id)

    if channel := data.get("text_channel"):
        progress = f"00:00 {'▬' * 12}| {format_time(data['now_playing']['duration'])}"
        msg = await channel.send(view=NowPlayingView(data["now_playing"], progress, guild_id))
        bot.loop.create_task(update_embed_loop(guild_id, msg, data["loop_id"]))

async def update_embed_loop(guild_id: int, message: discord.Message, loop_id: int):
    data = get_guild_data(guild_id)
    while data.get("loop_id") == loop_id and data.get("now_playing"):
        if not (vc := data.get("voice")) or not vc.is_connected(): break
        song = data["now_playing"]; duration = song.get("duration", 0)
        if vc.is_playing(): song["elapsed"] += 1
        elapsed = song["elapsed"]
        bar = "▬" * int((elapsed/duration)*12) + "|" + "▬" * (12-int((elapsed/duration)*12)-1) if duration > 0 else f"Live"
        progress = f"{format_time(elapsed)} {bar} {format_time(duration)}" if duration > 0 else f"Live {format_time(elapsed)}"
        try: await message.edit(view=NowPlayingView(song, progress, guild_id))
        except: break
        await asyncio.sleep(1)

# ═══════════════════════════════════════════════════════════════════════════════
# SLASH COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="play", description="Play song")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer(ephemeral=True); data = get_guild_data(interaction.guild.id); voice = await ensure_voice(interaction)
    if not voice: await interaction.followup.send(view=InfoView("No voice channel."), ephemeral=True); return
    data["queue"].append(url); data["text_channel"] = interaction.channel
    await interaction.followup.send(view=InfoView(f"<:icon_music:1372375041542721638> Zur Queue hinzugefügt: {url}"), ephemeral=True)
    if not voice.is_playing() and not voice.is_paused(): await _play_next(interaction.guild.id)

@bot.tree.command(name="skip")
async def skip(interaction: discord.Interaction):
    if vc := get_guild_data(interaction.guild.id).get("voice"): vc.stop()
    await interaction.response.send_message(view=InfoView("Skipped."), ephemeral=True)

@bot.tree.command(name="stop")
async def stop(interaction: discord.Interaction):
    data = get_guild_data(interaction.guild.id); data["queue"].clear()
    if vc := data.get("voice"): vc.stop()
    await interaction.response.send_message(view=InfoView("Stopped."), ephemeral=True)

@bot.tree.command(name="restart")
async def restart(interaction: discord.Interaction):
    await interaction.response.send_message(view=InfoView("Restarting..."), ephemeral=True); await bot.close(); os.execv(sys.executable, ["python"] + sys.argv)

@bot.tree.command(name="commands")
async def commands_list(interaction: discord.Interaction): await interaction.response.send_message(view=CommandsView("overview"), ephemeral=True)

@bot.event
async def on_ready():
    global BOT_START_TIME; BOT_START_TIME = time.time(); await bot.tree.sync()
    print(f"Bot online als {bot.user}")

bot.run(TOKEN)
