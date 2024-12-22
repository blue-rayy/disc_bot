import yt_dlp, asyncio, discord

yt_dlp.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    # "nopart": True,
    # "nocheckcertificate": True,
    # "ignoreerrors": False,
    # "logtostderr": False,
    # "quiet": True,
    # "no_warnings": True,
    # "default_search": "auto",
    # "source_address": socket.gethostbyname(
    #     socket.gethostname()
    # ),  # bind to ipv4 since ipv6 addresses cause issues sometimes
    # "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "paths": {"home": "./assets/sound/"},
    "download_archive": ".archive.txt",
    # "cookies": "./utils/cookies.txt",
    # "dump_user_agent": True,
    # "dump_json": True,
    # "verbose": True,
    # "print_traffic": True,
}
ffmpeg_options = {"options": "-vn"}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if data != None:
            if "entries" in data:
                # take first item from a playlist
                data = data["entries"][0]

        filename = data["title"] if stream else ytdl.prepare_filename(data)
        return filename
