__author__ = "Samy Mellouki"
__version__ = "1.0.0"
__maintainer__ = "Samy Mellouki"
__email__ = "samymel@hotmail.fr"


import discord
from MusicBot import TalkingBot
import asyncio
from pytubefix import YouTube
import os
from gtts import gTTS
from pydub import AudioSegment
from openai import OpenAI
import requests

api_key = os.environ["OPENAI_API_KEY"]
ytb_api_key = os.environ["YOUTUBE_API_KEY"]
discord_token = os.environ["DISCORD_TOKEN"]


client = OpenAI(api_key = api_key)

FIRST_SYSTEM_MESSAGE = "GPT prompt here."


intents = discord.Intents.all()

bot = TalkingBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"\n\n\nBOT {bot.user.name} IS CONNECTED\n\n\n")


@bot.listen
async def on_message(message):
    await bot.get_context(message)




#
# Function play(ctx,*args)
#
# Parameters :
# - ctx : Discord bot context
# - args : YouTube video or title
#
# This function handles music with those features:
#
# If the bot isn't connected to a channel, it connects and plays the video.
# If the bot is connected but not playing anything, it plays the video.
# If the bot is connected and playing something, it adds the video to the queue.
#
#
@bot.command()
async def play(ctx, *args):


#======================================================================================

    if args[0][:5] == "https": #2 cases : if you use a link, direct use

        url_to_download = args[0]
    else: # else, we go by using YouTube Data v3 API.
        research = " ".join(args)
        api_link = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": research,
            "key": os.environ["YOUTUBE_API_KEY"],
            "type": "video",
            "maxResults": 1,
        }
        response = requests.get(api_link, params=params)
        results = response.json().get("items", [])
        video_id = results[0]["id"]["videoId"]
        url_to_download = f"https://youtube.com/watch?v={video_id}" #Then we deduce the link with the ID

        print("Playing video :", YouTube(url_to_download).title)

#=======================================================================================

    vc = ctx.voice_client #We fetch the state of the context (if the bot is already connected in a channel). 

    if not vc: #If it's not the case, we connect to the command's author channel.
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        bot.add_music_to_queue(url_to_download)
        try:
            YouTube(bot.get_next_music()).streams.get_audio_only().download( #We try to find if the video is available. Else, we send a message.
                mp3=True, filename="temp"
            )
        except:
            await ctx.send("Video couldn't be loaded, maybe it's unavailable for the bot.")
            bot.music_queue.remove(url_to_download)
            return

        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="temp.mp3")) #We play the mp3 file.

        embed = discord.Embed( #We send a nice embedded discord message about the playlist state.
            title="JukeBox",
            description=f"_{YouTube(url_to_download).title}_ was added to the playlist.", 
            color=0x66001F,
        )
        embed.set_author(
            name="!play",
            icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
        )
        embed.set_thumbnail(url=YouTube(url_to_download).thumbnail_url) #Add the video thumbnail to the embedded message.
        queue_list = bot.music_queue
        current_title, tail = queue_list[0], queue_list[1:]
        embed.add_field(
            name="Currently playing :", value=YouTube(current_title).title, inline=False
        )
        embed.add_field(
            name="Queue :",
            value=f"Queue length : {len(tail)}",
            inline=False,
        )

        for i in range(len(tail)): #We add the wait list inside the embed message to allow the user to know about the current state of the list. 
            embed.add_field(name=str(i + 1), value=YouTube(tail[i]).title, inline=False)

        await ctx.send(embed=embed)

        while vc.is_playing(): #While the music is playing, the bot can't to anything so we put it to sleep.
            await asyncio.sleep(1)
        bot.pass_to_next_music()

        while not bot.music_queue_is_empty(): #While the queue isn't empty, the bot continues to play.
            try:
                YouTube(bot.get_next_music()).streams.get_audio_only().download(
                    mp3=True, filename="temp"
                )
            except:
                await ctx.send("Video couldn't be loaded, maybe it's unavailable for the bot.")
                bot.music_queue.remove(url_to_download)
                pass

            embed = discord.Embed(title="JukeBox", description="", color=0x66001F) #Sends a embedded message to notify about the next music.
            embed.set_author(
                name="!play",
                icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
            )
            embed.set_thumbnail(url=YouTube(bot.get_next_music()).thumbnail_url)
            queue_list = bot.music_queue
            current_title, tail = queue_list[0], queue_list[1:]
            embed.add_field(
                name="Currently playing :",
                value=YouTube(current_title).title,
                inline=False,
            )
            embed.add_field(
                name="Queue :",
                value=f"Queue length : {len(tail)}",
                inline=False,
            )

            for i in range(len(tail)): #Manages the queue inside the embed
                embed.add_field(
                    name=str(i + 1), value=YouTube(tail[i]).title, inline=False
                )

            await ctx.send(embed=embed)

            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="temp.mp3"))
            while vc.is_playing():
                await asyncio.sleep(1)
            bot.pass_to_next_music()
    elif vc and vc.is_playing(): #Here is the case if the bot is already playing.

        try:
            YouTube(url_to_download).check_availability() #We check if the added music is available for the bot.
        except:
            await ctx.send("Video couldn't be loaded, maybe it's unavailable for the bot.")
            return

        bot.add_music_to_queue(url_to_download)

        embed = discord.Embed( #We send a embedded message to notify that the music was added.
            title="JukeBox",
            description=f"_{YouTube(url_to_download).title}_ was added to the playlist",
            color=0x66001F,
        )
        embed.set_author(
            name="!play",
            icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
        )
        embed.set_thumbnail(url=YouTube(url_to_download).thumbnail_url)
        queue_list = bot.music_queue
        current_title, tail = queue_list[0], queue_list[1:]
        embed.add_field(
            name="Currently playing :", value=YouTube(current_title).title, inline=False
        )
        embed.add_field(
            name="Queue :",
            value=f"Queue length : {len(tail)}",
            inline=False,
        )

        for i in range(len(tail)):
            embed.add_field(name=str(i + 1), value=YouTube(tail[i]).title)

        await ctx.send(embed=embed)

    elif vc and not vc.is_playing(): #Handles the case when the bot is connected but not playing.
        

        try:
            YouTube(url_to_download).streams.get_audio_only().download(
                mp3=True, filename="temp"
            )
        except:
            await ctx.send("Video couldn't be loaded, maybe it's unavailable for the bot.")
            return
        
        bot.add_music_to_queue(url_to_download)

        embed = discord.Embed(
            title="JukeBox",
            description=f"_{YouTube(url_to_download).title}_ was added to the playlist.",
            color=0x66001F,
        )
        embed.set_author(
            name="!play",
            icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
        )
        embed.set_thumbnail(url=YouTube(url_to_download).thumbnail_url)
        queue_list = bot.music_queue
        current_title, tail = queue_list[0], queue_list[1:]
        embed.add_field(
            name="Currently playing :", value=YouTube(current_title).title, inline=False
        )
        embed.add_field(
            name="Queue :",
            value=f"Queue length : {len(tail)}",
            inline=False,
        )

        for i in range(len(tail)):
            embed.add_field(name=str(i + 1), value=YouTube(tail[i]).title, inline=False)

        await ctx.send(embed=embed)

        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="temp.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
        bot.pass_to_next_music()

#
# Function clear(ctx)
#
# Parameters :
# 
# - ctx : Discord bot context
#
# Clears the queue
#
#
@bot.command() 
async def clear(ctx):
    bot.clear_music_queue()
    await ctx.send("Queue was cleared.")

#
# Function stop(ctx)
#
# Parameters :
# 
# - ctx : Discord bot context
#
# Stops the music, clears the queue and leave the channel
#
#
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        bot.clear_music_queue()
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Bot left and cleared the playlist.")
    else:
        await ctx.send(
            "I am not in the channel, use a command such as !play or !gpt(3 or 4) to connect me to your channel."
        )

#
# Function skip(ctx)
#
# Parameters :
# 
# - ctx : Discord bot context
#
# Skips the current music and goes for the next one, if there isn't a next one, it stops.
#
#
@bot.command()
async def skip(ctx):
    vc = ctx.voice_client
    if vc: #Checks if the bot is connected
        if bot.music_queue_is_empty():
            await ctx.send("Queue is empty, music stopped.") #Case if the queue is empty
            vc.stop()
        else:
            next_music = bot.get_next_music()
            vc.stop() #Stops the music
            YouTube(next_music).streams.get_audio_only().download( #Fetch and plays the next music
                mp3=True, filename="temp"
            )

            embed = discord.Embed( #Sends an embedded message to notify about the state of the jukebox
                title="JukeBox", description=f"Music was skipped.", color=0x66001F
            )
            embed.set_author(
                name="!skip",
                icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
            )
            embed.set_thumbnail(url=YouTube(next_music).thumbnail_url)
            queue_list = bot.music_queue
            current_title, tail = queue_list[0], queue_list[1:]
            embed.add_field(
                name="Currently playing :",
                value=YouTube(current_title).title,
                inline=False,
            )
            embed.add_field(
                name="Queue :",
                value=f"Queue length : {len(tail)}",
                inline=False,
            )

            for i in range(len(tail)):
                embed.add_field(
                    name=str(i + 1), value=YouTube(tail[i]).title, inline=False
                )

            await ctx.send(embed=embed)


#
# Function pause(ctx)
#
# Parameters :
# 
# - ctx : Discord bot context
#
# Pauses the music
#
#
@bot.command()
async def pause(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("Music is paused")

#
# Function resume(ctx)
#
# Parameters :
# 
# - ctx : Discord bot context
#
# Resumes the music
#
#
@bot.command()
async def resume(ctx):
    vc = ctx.voice_client
    if vc.is_paused():
        vc.resume()
        await ctx.send("Music is resumed")
    elif not bot.music_queue_is_empty(): #Here is in the case there is a problem with the queue management.
        next_music = bot.get_next_music()
        YouTube(next_music).streams.get_audio_only().download(mp3=True, filename="temp")
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="temp.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
        bot.pass_to_next_music()




#
# Function gpt4(ctx,*args)
#
# Parameters :
# 
# - ctx : Discord bot context
# - args : prompt for gpt
# 
# Sends a prompt to OpenAI API GPT4 model, and answers in your channel
#
@bot.command()
async def gpt4(ctx, *args):
    vc = ctx.guild.voice_client
    if not vc: #If the bot is not connected we connect it
        channel = ctx.author.voice.channel
        vc = await channel.connect()
    else:
        if vc.is_playing(): #If the bot is already speaking, we notify the user to not bother it.
            await ctx.send(
                "Already speaking, don't interrupt me."
            )

    text = " ".join(args)
    user = ctx.author.nick if ctx.author.nick else ctx.author.name
    response = (
        client.chat.completions.create(
            messages=[ #We send the prompt
                {"role": "system", "content": FIRST_SYSTEM_MESSAGE},
                {"role": "user", "content": f"[{user}]:{text}"},
            ],
            model="gpt-4-turbo",
        )
        .choices[0]
        .message.content
    )
    print(f"[{user}]:{text}\n\n")
    print(f"Answer : {response}")

    tts = gTTS(text=response, lang="fr", slow=False) #We create a TTS mp3 file to play it through the bot.
    tts.save("output.mp3")

    audio = AudioSegment.from_mp3("output.mp3")

    audio.speedup(playback_speed=2.0)

    audio.export("output.mp3", format="mp3")

    embed = discord.Embed( #We create an embedded message to have a trace of the prompt.
        title="GPT4", description=f"Answer to {ctx.author.name}", color=0x0DD717
    )
    embed.set_author(
        name="!gpt4",
        icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.add_field(name=text, value=response, inline=False)

    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="output.mp3"))
        await ctx.send(embed=embed)
    while vc.is_playing():
        await asyncio.sleep(1)

#
# Function gpt3(ctx,*args)
#
# Parameters :
# 
# - ctx : Discord bot context
# - args : prompt for gpt
# 
# Sends a prompt to OpenAI API GPT3.5 turbo model, and answers in your channel
#
@bot.command() #Same as gpt4
async def gpt3(ctx, *args):
    vc = ctx.guild.voice_client
    if not vc:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
    else:
        if vc.is_playing():
            await ctx.send(
                "Already speaking, don't interrupt me."
            )

    text = " ".join(args)
    user = ctx.author.nick if ctx.author.nick else ctx.author.name
    response = (
        client.chat.completions.create(
            messages=[
                {"role": "system", "content": FIRST_SYSTEM_MESSAGE},
                {"role": "user", "content": f"[{user}]:{text}"},
            ],
            model="gpt-3.5-turbo",
        )
        .choices[0]
        .message.content
    )
    print(f"[{user}]:{text}\n\n")
    print(f"Answer : {response}")

    tts = gTTS(text=response, lang="fr", slow=False)
    tts.save("output.mp3")

    audio = AudioSegment.from_mp3("output.mp3")

    audio.speedup(playback_speed=2.0)

    audio.export("output.mp3", format="mp3")

    embed = discord.Embed(
        title="GPT3", description=f"Answer to {ctx.author.name}", color=0x0DD717
    )
    embed.set_author(
        name="!gpt3",
        icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.add_field(name=text, value=response, inline=False)

    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="output.mp3"))
        await ctx.send(embed=embed)
    while vc.is_playing():
        await asyncio.sleep(1)

#
# Function queue(ctx)
#
# Parameters :
# 
# - ctx : Discord bot context
# 
# Gives information about the queue
#
@bot.command()
async def queue(ctx):
    if bot.music_queue_is_empty():
        await ctx.send("Queue is already empty.")
        return
    queue = bot.music_queue
    current_title = queue[0]
    embed = discord.Embed(
        title="JukeBox", description="Current jukebox state.", color=0x66001F
    )
    embed.set_author(
        name="!queue",
        icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
    )
    embed.set_thumbnail(url=YouTube(current_title).thumbnail_url)
    embed.add_field(
        name="Currently playing :",
        value="__" + YouTube(current_title).title + "__",
        inline=False,
    )
    embed.add_field(
        name="Queue :",
        value=f"Queue length : __{len(queue[1:])}__",
        inline=False,
    )

    tail = queue[1:]
    for i in range(len(tail)):
        number = i + 1
        embed.add_field(name=str(number), value=YouTube(tail[i]).title, inline=False)
    await ctx.send(embed=embed)

#
# Function commands(ctx)
#
# Parameters :
# 
# - ctx : Discord bot context
# 
# Sends an embedded message about all the commands you can do 
#
@bot.command()
async def commands(ctx):
    embed = discord.Embed(
        title="Commands",
        description="This guide will show you all the commands you need to operate the bot.",
        color=0x001D75,
    )
    embed.set_author(
        name="!help",
        icon_url="https://cdn.discordapp.com/avatars/989958012988948560/efb8847b4b2e4847430c5ca4fbef651f?size=1024",
    )
    embed.add_field(
        name="!play",
        value="_!play [music-name/youtube-url]_ : Adds a music in the queue, or plays it if the queue is empty.",
        inline=False,
    )
    embed.add_field(
        name="!clear",
        value="_!clear_ : Clears the music queue.",
        inline=False,
    )
    embed.add_field(
        name="!stop",
        value="_!stop_ : Stop the music, clears the queue and leaves the channel.",
        inline=False,
    )
    embed.add_field(
        name="!skip",
        value="_!skip_ : Skips the current music and goes for the next one.",
        inline=False,
    )
    embed.add_field(
        name="!pause",
        value="_!pause_ : Pauses the current music.",
        inline=False,
    )
    embed.add_field(name="!resume", value="_!resume_ : Resumes the music.", inline=False)
    embed.add_field(
        name="!gpt3",
        value="_!gpt3 [prompt]_ : Sends a prompt to GPT 3.5 OpenAI API and answers you using TTS in your channel.",
        inline=False,
    )
    embed.add_field(
        name="!gpt4",
        value="_!gpt4 [prompt]_ : Sends a prompt to GPT 3.5 OpenAI API and answers you using TTS in your channel.",
        inline=False,
    )
    embed.add_field(
        name="!queue",
        value="_!queue_ : Checks the queue state.",
        inline=False,
    )
    embed.set_footer(
        text="You can't prompt to GPT if the bot is already speaking."
    )
    await ctx.send(embed=embed)

#And then we run it
bot.run(discord_token)
