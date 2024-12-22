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
queue = []


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
        filename = cache_line[1].removesuffix("\n")

        cache[yt_code] = filename


def cache_add(yt_code, filename):
    global cache
    cache[yt_code] = filename
    cache_file = open(".cache.txt", "a")
    cache_string = yt_code + " ./" + filename.replace("\\", "/") + "\n"
    cache_file.write(cache_string)


def init_cache():
    update_cache()
    load_cache()


def queue_add(yt_link, filename=None):
    global queue
    if not filename:
        queue.append([yt_link])
    else:
        queue.append([yt_link, filename])


def queue_insert(queue_num, yt_link):
    global queue
    queue.insert(int(queue_num) - 1, [yt_link])


def queue_remove(song_num):
    global queue
    # queue.remove(queue[int(song_num) - 1])
    queue[int(song_num) - 1] = "Removed"
    queue.remove("Removed")


def queue_clear():
    global queue
    queue.clear()


def queue_print():
    global queue
    if len(queue) == 0:
        return "Queue empty"

    string_builder = ""
    count = 1

    for song in queue:
        # print(count + ": " + song)
        string_builder += str(count) + ": " + song[0] + "\n"
        count += 1

    return string_builder


async def get_ytlink(command):
    youtube_pattern = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"

    return re.search(youtube_pattern, command)


async def get_file(yt_url):
    yt_code = re.search(r"v=.*\&|v=.*", yt_url).group(0).removeprefix("v=")

    if yt_code.find("&") != -1:
        yt_code = yt_code.split("&")[0]

    try:
        filename = cache[yt_code]
        print("Cache hit!")
    except:
        filename = await YTDLSource.from_url(url=yt_url, loop=bot.loop)
        cache_add(yt_code, filename)

    return filename


""" TODO:
    V1 List
  2. add song queue
  3. Fix stuttering issue when downloading a song at the same time as a song is playing
  4. finish adding all song related commands
  5. Add help page to each command
  6. Refactor to not use vclient global variable as it is shared between different servers

  COMPLETE:
  1. add cache for already downloaded songs by reading archive file and mapping each id to its filename to be returned in the from_url function
"""

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    activity=discord.CustomActivity("straight up jorkin it"),
)

vclient = None


def play_next(error):
    global queue
    # try:
    vclient.play(
        discord.FFmpegPCMAudio(executable=FFMPEG, source=queue[1][1]), after=play_next
    )

    # fut = asyncio.run_coroutine_threadsafe(
    #     vclient.play(
    #         discord.FFmpegPCMAudio(executable=FFMPEG, source=queue[1][1]),
    #         after=play_next(),
    #     ),
    #     bot.loop,
    # )

    # fut.result()
    # except (Exception e):
    #     print("what the fuck")


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
                vclient.stop()
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

    if vclient.is_paused() and len(msg.split()) == 1:
        vclient.resume()
        return

    yt_url = await get_ytlink(msg)

    if not yt_url:
        await message.channel.send(
            "Could not find your youtube link. Try using a different link or ping ray to fix it"
        )
        return

    filename = await get_file(yt_url.group(1))

    queue_add(yt_url.group(1), filename)

    # vclient.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=filename))
    vclient.play(
        discord.FFmpegPCMAudio(executable=FFMPEG, source=filename),
        after=play_next,
    )


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
        vclient.pause()
        await msg.channel.send("Song paused.")
    else:
        await msg.channel.send("No song playing to pause.")


@bot.command()
async def add(ctx):
    message = ctx.message
    msg = ctx.message.content
    command_args = msg.split()

    if len(command_args) == 2:
        filename = await get_file(command_args[1])
        queue_add(command_args[1], filename)
    else:
        await message.channel.send("Please only add one song at a time.")
        return

    # if vclient.is_playing():
    # asyncio.run_coroutine_threadsafe(get_file(command_args[1]), bot.loop)
    # await get_file(command_args[1])


@bot.command()
async def insert(ctx):
    message = ctx.message
    msg = ctx.message.content
    command_args = msg.split()

    if len(command_args) == 3:
        queue_insert(command_args[2], command_args[1])
    else:
        await message.channel.send(
            "Please add what position you'd like the song to be inserted at.\nExample: !insert [yt_link] [song_num]"
        )


@bot.command()
async def clear(ctx):
    queue_clear()


@bot.command()
async def remove(ctx):
    message = ctx.message
    msg = ctx.message.content
    command_args = msg.split()

    if len(command_args) == 2:
        queue_remove(command_args[1])
    else:
        await message.channel.send(
            "Please specify which song you'd like to remove by typing the song number in the queue.\nExample: !remove [song_num]"
        )


@bot.command()
async def show(ctx):
    await ctx.message.channel.send(queue_print())


if __name__ == "__main__":
    init_cache()
    bot.run(PRIV)
