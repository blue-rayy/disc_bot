import discord, os, yt_dlp, asyncio, re
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()

PRIV = os.getenv("DISCORD_TOKEN")
FFMPEG = os.getenv("ffmpeg")

intents = discord.Intents.default()
intents.message_content = True


# sg = "./fousey.jpg"
# sen = discord.File(open(sg, "rb"), sg)


yt_dlp.utils.bug_reports_message = lambda: ""
ytdl_format_options = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
    "paths": {"home": "./assets/sound/"},
}
ffmpeg_options = {"options": "-vn"}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=1):
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

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["title"] if stream else ytdl.prepare_filename(data)
        return filename


client = discord.Client(
    intents=intents, activity=discord.CustomActivity("straight up jorkin it")
)

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    activity=discord.CustomActivity("straight up jorkin it"),
)

vclient = None


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    global vclient
    msg = message.content
    sender = message.author.name
    vchannel = message.author.voice or None

    if msg.startswith("hi bot"):
        if sender == "bluuray":
            if vclient != None:
                youtube_pattern = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
                yt_url = re.search(youtube_pattern, msg)
                if not yt_url:
                    await message.channel.send(
                        "Could not find your youtube link. Try using a different link or just ping ray"
                    )
                    return

                print(yt_url.group(1))
                filename = await YTDLSource.from_url(url=yt_url.group(1), loop=bot.loop)

                # filename = await YTDLSource.from_url(
                #     url="https://www.youtube.com/watch?v=oft2kC6xQvw", loop=bot.loop
                # )

                # filename = await YTDLSource.from_url(
                #     url="https://www.youtube.com/watch?v=uMGyPutPoOk", loop=bot.loop
                # )

                vclient.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=filename))

                # await message.channel.send(yt_url.group(1))
            else:
                await message.channel.send("omg hi ray :)")
        else:
            await message.channel.send("ew. :skull:")

    elif msg.startswith("!joinme"):
        if vchannel:
            await message.channel.send("omw !")
            vclient = await vchannel.channel.connect(self_deaf=True)
        else:
            await message.channel.send("ur not even in a voice chanel man")

    elif msg.startswith("!kys"):
        if sender == "bluuray":
            await message.channel.send(":((")
            await bot.close()
            return
        else:
            await message.channel.send("hehe nah :stuck_out_tongue:")

    elif msg.startswith("!help"):
        await message.channel.send(
            "say hi to me by typing ``hi bot`` ! other than that, i cant do much rn\nyell at ray if you want me to be able to do more"
        )


@bot.command()
async def play(ctx):
    global vclient
    await ctx.send("hello i wokr")
    message = ctx.message
    msg = message.content
    sender = message.author.name
    vchannel = message.author.voice or None
    if not vchannel:
        return
    if not vclient:
        vclient = await vchannel.channel.connect(self_deaf=True)

    youtube_pattern = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
    yt_url = re.search(youtube_pattern, msg)
    if not yt_url:
        await message.channel.send(
            "Could not find your youtube link. Try using a different link or just ping ray"
        )
        return

    print(yt_url.group(1))
    filename = await YTDLSource.from_url(url=yt_url.group(1), loop=bot.loop)

    vclient.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=filename))


if __name__ == "__main__":
    bot.run(PRIV)
