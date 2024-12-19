import discord, os, yt_dlp, asyncio, re, socket
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
    "noplaylist": False,
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
        if "entries" in data and len(data["entries"]) != 0:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["title"] if stream else ytdl.prepare_filename(data)
        return filename


# TODO:
#    V1 List
#  1. add cache for already downloaded songs by reading archive file and mapping each id to its filename to be returned in the from_url function
#  2. add song queue
#  3. Fix stuttering issue when downloading a song at the same time as a song is playing
#  4. finish adding all song related commands
#  5. Add help page to each command
#  6. Refactor to not use vclient global variable as it is shared between different servers

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    activity=discord.CustomActivity("straight up jorkin it"),
)

vclient = None
shared_num = 0


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
                # filename = await YTDLSource.from_url(
                #     url="https://www.youtube.com/watch?v=oft2kC6xQvw", loop=bot.loop
                # )

                filename = await YTDLSource.from_url(
                    url="https://www.youtube.com/watch?v=uMGyPutPoOk", loop=bot.loop
                )

                vclient.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=filename))

                # await message.channel.send(yt_url.group(1))
            else:
                await message.channel.send("omg hi ray :)")
        else:
            await message.channel.send("ew. :skull:")


@bot.command()
async def joinme(ctx):
    global vclient
    vchannel = ctx.message.author.voice or None

    if vchannel:
        await ctx.message.channel.send("omw !")
        vclient = await vchannel.channel.connect(self_deaf=True)
    else:
        await ctx.message.channel.send("ur not even in a voice chanel man")


# @bot.command()
# async def help(ctx):
#     await ctx.message.channel.send(
#         "say hi to me by typing ``hi bot`` ! other than that, i cant do much rn\nyell at ray if you want me to be able to do more"
#     )


@bot.command()
async def kys(ctx):
    global vclient
    if ctx.message.author.name == "bluuray":
        await ctx.message.channel.send(":((")
        if vclient:
            if vclient.is_playing():
                await vclient.stop()
            await vclient.disconnect()
        await bot.close()
        return
    else:
        await ctx.message.channel.send("hehe nah :stuck_out_tongue:")


@bot.command()
async def play(ctx):
    global vclient
    message = ctx.message
    msg = message.content
    vchannel = message.author.voice or None
    if not vchannel:
        return
    if not vclient:
        vclient = await vchannel.channel.connect(self_deaf=True)

    if vclient.is_paused():
        vclient.resume()
        return

    youtube_pattern = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
    yt_url = re.search(youtube_pattern, msg)
    if not yt_url:
        await message.channel.send(
            "Could not find your youtube link. Try using a different link or just ping ray"
        )
        return

    filename = await YTDLSource.from_url(url=yt_url.group(1), loop=bot.loop)

    # for i in range(0, yt_url.endpos):
    print(yt_url.group(1))

    vclient.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=filename))


@bot.command()
async def stop(ctx):
    global vclient
    msg = ctx.message

    if not vclient:
        await msg.channel.send("You're not in a voice channel..")
        return

    if vclient.is_playing():
        await vclient.stop()
        await msg.channel.send("Song stopped.")
    else:
        await msg.channel.send("No song playing to stop.")


@bot.command()
async def pause(ctx):
    global vclient
    msg = ctx.message

    if not vclient:
        await msg.channel.send("You're not in a voice channel..")
        return

    if vclient.is_playing():
        await vclient.pause()
        await msg.channel.send("Song paused.")
    else:
        await msg.channel.send("No song playing to pause.")


@bot.command()
async def add(ctx):
    global shared_num
    shared_num += 1


@bot.command()
async def show(ctx):
    global shared_num
    await ctx.message.channel.send(shared_num)


if __name__ == "__main__":
    bot.run(PRIV)
