import discord, os, yt_dlp, asyncio, re, socket, glob, concurrent.futures
from dotenv import load_dotenv
from discord.ext import commands, tasks

from utils.extractor import YTDLSource

load_dotenv()

PRIV = os.getenv("DISCORD_TOKEN")
FFMPEG = os.getenv("FFMPEG")
APP_ID = os.getenv("APP_ID")

intents = discord.Intents.default()
intents.message_content = True


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


def queue_add(yt_link, title=None, requester=None, requester_id=None, user=None):
    global queue
    queue.append([yt_link, title, requester, requester_id, user])


def queue_update_info(yt_link, title):
    global queue
    try:
        for song in queue:
            if song[0] == yt_link:
                song[1] = title
    except:
        pass


def queue_insert(queue_num, yt_link):
    global queue
    try:
        queue.insert(int(queue_num) - 1, [yt_link])
        return True
    except:
        return False


def queue_remove(song_num):
    global queue
    try:
        queue[int(song_num) - 1] = "Removed"
        queue.remove("Removed")
        return True
    except:
        return False


def queue_pop():
    global queue
    try:
        return queue.pop(0)
    except:
        return None


def queue_clear():
    global queue
    queue.clear()


def queue_next():
    global queue
    try:
        return queue[0]
    except:
        return None


def queue_len():
    global queue
    return len(queue)


def queue_print(amount):
    global queue
    string_builder = ""

    if len(queue) == 0:
        return "Queue empty"

    count = 1

    for song in queue:
        if vclient:
            requestor = song[4].nick or song[2]
            if vclient.is_playing() and count == 1:
                string_builder += (
                    "1: " + song[0] + " (Currently playing) [" + requestor + "]\n"
                )
            else:
                string_builder += str(count) + ": " + song[0] + " [" + requestor + "]\n"
        if count == amount:
            if queue_len() - count > 0:
                string_builder += str(queue_len() - count) + " songs not listed..."
            break
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
        filename = await YTDLSource.from_url(url=yt_url, loop=bot.loop, stream=True)[0]
        # cache_add(yt_code, filename)

    return filename


""" TODO:
    V1 List

  COMPLETE:
  1. add cache for already downloaded songs by reading archive file and mapping each id to its filename to be returned in the from_url function
  2. add song queue
  3. Fix stuttering issue when downloading a song at the same time as a song is playing (GIVEN UP ON, 
        SWITCHED TO STREAMING) Maybe bc it uses same socket to stream from and download info??
  4. finish adding all song related commands
  5. Add help page to each command
"""

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    activity=discord.CustomActivity("straight up jorkin it"),
    application_id=APP_ID,
)

vclient = None


async def play_next_async(ctx):
    if not queue_pop():
        await ctx.send("No more songs in queue")
        return

    next_song = queue_next()

    if not queue_next():
        await ctx.send("No more songs in queue")
        return

    status = await ctx.send("Loading next song")

    player = await YTDLSource.from_url(url=next_song[0], loop=bot.loop, stream=True)

    await status.edit(
        discord.utils.remove_markdown(
            "Now playing: \n"
            + player[1]["title"]
            + "\n"
            + next_song[0]
            + "\nRequested by: <@"
            + str(next_song[3])
            + ">"
        ),
        suppress=True,
    )

    queue_update_info(next_song[0], player[1]["title"])

    vclient.play(
        player[0],
        after=lambda e, ctx=ctx: play_next(ctx=ctx, error=e),
    )


def play_next(ctx, error):
    if not queue_pop():
        fut_message = asyncio.run_coroutine_threadsafe(
            ctx.send("No more songs in queue"), bot.loop
        )
        return fut_message.result()

    next_song = queue_next()

    if not queue_next():
        fut_message = asyncio.run_coroutine_threadsafe(
            ctx.send("No more songs in queue"), bot.loop
        )
        return fut_message.result()

    status = asyncio.run_coroutine_threadsafe(ctx.send("Loading next song"), bot.loop)
    status = status.result()

    fut_player = asyncio.run_coroutine_threadsafe(
        YTDLSource.from_url(url=next_song[0], loop=bot.loop, stream=True), bot.loop
    )
    player = fut_player.result()

    asyncio.run_coroutine_threadsafe(
        status.edit(
            discord.utils.remove_markdown(
                "Now playing: \n"
                + player[1]["title"]
                + "\n"
                + queue_next()[0]
                + "\nRequested by: <@"
                + str(queue_next()[3])
                + ">"
            ),
            suppress=True,
        ),
        bot.loop,
    ).result()

    queue_update_info(next_song[0], player[1]["title"])

    vclient.play(
        player[0],
        after=lambda e, ctx=ctx: play_next(ctx=ctx, error=e),
    )


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    global vclient
    msg = message.content
    sender = message.author.name
    vchannel = message.author.voice or None

    if msg.startswith("whos home"):
        if sender == "bluuray":
            if vclient != None:
                # filename = await YTDLSource.from_url(
                #     url="https://www.youtube.com/watch?v=oft2kC6xQvw", loop=bot.loop
                # )

                filename = await YTDLSource.from_url(
                    url="https://www.youtube.com/watch?v=uMGyPutPoOk", loop=bot.loop
                )[0]

                vclient.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=filename))

            else:
                await message.channel.send("omg hi ray :)")
        else:
            await message.channel.send("ew. :skull:")


@bot.command(
    name="summon", aliases=["sum", "su", "summ", "summo"], help="this shouldnt be here"
)
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


@bot.command(name="kys", aliases=["die", "bye", "q"], help="only for ray :)")
async def kys(ctx):
    global vclient
    if await bot.is_owner(ctx.author):
        await ctx.send(":((")
        if vclient:
            if vclient.is_playing():
                queue_clear()
                vclient.stop()
            await vclient.disconnect()
        await bot.close()
        return
    else:
        file = open("./assets/image/fousey.jpg", "rb")
        sen = discord.File(file, "./assets/image/fousey.jpg")
        await ctx.send("hehe nah :stuck_out_tongue:", file=sen)
        file.close()


@bot.command(
    name="play",
    aliases=["pl", "pla", "start"],
    help="Plays first song in queue if no link is given and nothing is paused or playing at the moment."
    + "Otherwise, will start playing song in youtube link. If something is being played and a link is given, song"
    + "will be added to queue instead.\nUsages:\n   !play [youtube_link]\n   !play",
)
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

    if (
        not vclient.is_paused()
        and not vclient.is_playing()
        and queue_next()
        and len(msg.split()) == 1
    ):
        yt_url = queue_next()[0]
    else:
        yt_url = await get_ytlink(msg)

        if not yt_url:
            await message.channel.send(
                "Could not find your youtube link. Try using a different link or ping ray to fix it"
            )
            return

        yt_url = yt_url.group(1)
        queue_add(
            yt_url,
            requester=message.author.name,
            requester_id=message.author.id,
            user=message.author,
        )

    if vclient.is_playing() and len(msg.split()) == 1:
        await message.channel.send("Something is currently being played.")
        return

    elif vclient.is_playing() and len(msg.split()) != 1:
        await message.channel.send(
            "Something is currently being played. Requested song has been added to queue."
        )
        return

    status = await message.channel.send("Loading song...")

    async with ctx.typing():
        player = await YTDLSource.from_url(yt_url, loop=bot.loop, stream=True)

    await status.edit(
        content=(
            discord.utils.remove_markdown(
                "Now playing: \n"
                + player[1]["title"]
                + "\n"
                + queue_next()[0]
                + "\nRequested by: <@"
                + str(queue_next()[3])
                + ">"
            ),
        ),
        suppress=True,
    )

    queue_update_info(yt_url, player[1]["title"])

    ctx.voice_client.play(
        player[0],
        after=lambda e, ctx=ctx: play_next(error=e, ctx=ctx),
    )


@bot.command(
    name="skip",
    aliases=["sk", "ski", "next", "nex", "ne", "n"],
    help="Skips current song\nUsages:\n     !skip",
)
async def skip(ctx):
    global vclient
    msg = ctx.message

    if not vclient:
        await msg.channel.send("You're not in a voice channel..")
        return

    if queue_next():
        if vclient.is_playing() or vclient.is_paused():
            await ctx.message.add_reaction("⏭")
            # await msg.channel.send("Song skipped.")
            vclient.stop()

        # await play_next_async(ctx=ctx)
    else:
        await msg.channel.send("No song to skip.")


@bot.command(
    name="pause",
    aliases=["pa", "pau", "paus"],
    help="Pauses current song.\nUsages:\n   !pause",
)
async def pause(ctx):
    global vclient
    msg = ctx.message

    if not vclient:
        await msg.channel.send("You're not in a voice channel..")
        return

    if vclient.is_playing():
        vclient.pause()
        await ctx.message.add_reaction("⏸")
        # await msg.channel.send("Song paused.")
    else:
        await msg.channel.send("No song playing to pause.")


@bot.command(
    name="resume",
    aliases=["res", "resu", "resum"],
    help="Resumes the song if it was paused.\nUsages:\n     !resume",
)
async def resume(ctx):
    global vclient
    msg = ctx.message

    if not vclient:
        await msg.channel.send("You're not in a voice channel..")
        return

    if vclient.is_paused():
        vclient.resume()
        await ctx.message.add_reaction("⏯")
        # await msg.channel.send("Song resumed.")
    else:
        await msg.channel.send("No song to resume.")


@bot.command(
    name="add",
    aliases=["a", "ad"],
    help="Adds a song link to the end of the queue."
    + " Will start playing song added is the first song to be added to the queue.\nUsages:\n     !add [youtube_link]",
)
async def add(ctx):
    global vclient
    message = ctx.message
    vchannel = message.author.voice or None
    msg = ctx.message.content
    command_args = msg.split()

    yt_link = await get_ytlink(command_args[1])
    yt_link = yt_link.group(1)

    if len(command_args) == 2:
        queue_add(
            yt_link,
            requester=message.author.name,
            requester_id=message.author.id,
            user=message.author,
        )
        await ctx.message.add_reaction("✅")

        if queue_len() == 1:
            if vchannel:
                if not vclient:
                    vclient = await vchannel.channel.connect(self_deaf=True)

                status = await message.channel.send("Loading song...")

                async with ctx.typing():
                    player = await YTDLSource.from_url(
                        queue_next()[0], loop=bot.loop, stream=True
                    )

                await status.edit(
                    content=(
                        discord.utils.remove_markdown(
                            "Now playing: \n"
                            + player[1]["title"]
                            + "\n"
                            + queue_next()[0]
                            + "\nRequested by: <@"
                            + str(queue_next()[3])
                            + ">"
                        )
                    ),
                    suppress=True,
                )

                queue_update_info(queue_next()[0], player[1]["title"])

                ctx.voice_client.play(
                    player[0],
                    after=lambda e, ctx=ctx: play_next(error=e, ctx=ctx),
                )

            else:
                await message.channel.send(
                    "Send the !play command to start the music once you join a voice channel"
                )
        return

    else:
        await message.channel.send("Please only add one song at a time.")
        return


@bot.command(
    name="insert",
    aliases=["in", "ins", "inse", "inser"],
    help="Inserts a song to the position given in the queue (ie '!insert youtube_link 2' will shift all songs after 2 down one and the given youtube_link"
    + "will become the new second song in queue).\nUsage:\n    !insert [youtube_link] [queue_position]",
)
async def insert(ctx):
    message = ctx.message
    msg = ctx.message.content
    command_args = msg.split()

    if len(command_args) == 3:
        if queue_insert(command_args[2], command_args[1]):
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("❌")
            await ctx.send(
                "Something went wrong when trying to insert your song. Make sure the position you're giving exists in the queue :)"
            )
    else:
        await message.channel.send(
            "Please add what position you'd like the song to be inserted at.\nExample: !insert [yt_link] [song_num]"
        )


@bot.command(
    name="clear_queue",
    help="Clears the entire queue. As in, deletes it. Dont use this if you have no reason to.\nUsages:\n    !clear_queue",
)
async def clear(ctx):
    queue_clear()


@bot.command(
    name="remove",
    aliases=["rem", "remo", "remov"],
    help="Removes the song at the given queue position.\nUsages:\n     !remove [queue_position_number]",
)
async def remove(ctx):
    message = ctx.message
    msg = ctx.message.content
    command_args = msg.split()

    if len(command_args) == 2:
        if queue_remove(command_args[1]):
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("❌")
            await ctx.send(
                "Something went wrong when trying to remove your song. Make sure the position you're giving exists in the queue :)"
            )
    else:
        await message.channel.send(
            "Please specify which song you'd like to remove by typing the song number in the queue.\nExample: !remove [song_num]"
        )


@bot.command(
    name="show",
    aliases=["sh", "sho", "list", "ls", "queue"],
    help="Lists out the first 25 songs in queue.\nUsages:\n     !show",
)
async def show(ctx):
    await ctx.message.channel.send(queue_print(25), suppress_embeds=True)


@bot.command(
    name="show_all",
    help="Lists out all the songs in queue.\nUsages:\n      !show_all",
)
async def show(ctx):
    await ctx.message.channel.send(queue_print(9999), suppress_embeds=True)


@bot.command(
    name="song",
    aliases=["current", "so", "son", "wtf"],
    help="Prints the current song being played.\nUsages:\n      !song",
)
async def current_song(ctx):
    await ctx.message.channel.send(
        discord.utils.remove_markdown(
            "Currently playing: \n"
            + queue_next()[1]
            + "\n"
            + queue_next()[0]
            + "\nRequested by: <@"
            + str(queue_next()[3])
            + ">"
        ),
        suppress_embeds=True,
    )


@bot.event
async def on_ready():
    await bot.tree.sync()


if __name__ == "__main__":
    init_cache()
    bot.run(PRIV)
