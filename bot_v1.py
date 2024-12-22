import discord, os, yt_dlp, asyncio, re, socket, glob
from dotenv import load_dotenv
from discord.ext import commands, tasks

from utils.extractor import YTDLSource

load_dotenv()

PRIV = os.getenv("DISCORD_TOKEN")
FFMPEG = os.getenv("FFMPEG")

intents = discord.Intents.default()
intents.message_content = True


# sg = "./fousey.jpg"
# sen = discord.File(open(sg, "rb"), sg)
cache = {}


def update_cache():
    try:
        archive_file = open(".archive.txt", "r")
    except:
        print("No archive file")
        return

    current_files = glob.glob("./assets/sound/*.webm")
    cache_file = open(".cache.txt", "w")

    for archive in archive_file:
        for file in current_files:
            yt_code = archive.removesuffix("\n").split(" ")[1]
            file_code = (
                re.search(r"\[.*\.webm", file)
                .group(0)
                .removeprefix("[")
                .removesuffix("].webm")
                .removesuffix("\n")
            )

            if yt_code == file_code:
                cache_string = yt_code + " " + file.replace("\\", "/") + "\n"
                if cache_file.write(cache_string) != len(cache_string):
                    print("Cache file error")

    archive_file.close()
    cache_file.close()


def load_cache():
    global cache
    try:
        cache_file = open(".cache.txt", "r")
    except:
        print("Cache file not found")
        return

    for line in cache_file:
        cache_line = line.split(" ")
        yt_code = cache_line[0]
        file_name = cache_line[1].removesuffix("\n")

        cache[yt_code] = file_name


def init_cache():
    update_cache()
    load_cache()


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
    global vclient, cache

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
            "Could not find your youtube link. Try using a different link or ping ray to fix it"
        )
        return

    yt_code = re.search(r"v=.*\&|v=.*", yt_url.group(1)).group(0).removeprefix("v=")

    if yt_code.find("&") != -1:
        yt_code = yt_code.split("&")[0]

    filename = cache[yt_code]

    if not filename:
        filename = await YTDLSource.from_url(url=yt_url.group(1), loop=bot.loop)
    else:
        print("Cache hit!")
    # filename = await YTDLSource.from_url(url=yt_url.group(1), loop=bot.loop)

    # print(filename)
    vclient.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=filename))
    # vclient.play(discord.FFmpegPCMAudio(filename))


@bot.command()
async def stop(ctx):
    global vclient
    msg = ctx.message

    if not vclient:
        await msg.channel.send("You're not in a voice channel..")
        return

    if vclient.is_playing():
        vclient.stop()
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
    init_cache()
    bot.run(PRIV)
