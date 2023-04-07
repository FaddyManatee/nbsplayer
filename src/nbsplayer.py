import os
import asyncio
import botlog
import random
import nbswave as nbs
import discord
from discord import app_commands
from discord.ext import commands
from paginator import Paginator
from string import capwords
from collections import deque


class Player(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.shuffling = False

    
    async def _select_song(self, song):
        cache_path = os.path.join(os.path.dirname(__file__), os.path.join("..", "cache"))
        nbs_path = os.path.join(os.path.dirname(__file__), os.path.join("..", "nbs"))
        sound_path = os.path.join(os.path.dirname(__file__), os.path.join("..", "sounds"))

        # Generate .nbs song mp3 cache folder if it does not yet exist.
        if not os.path.isdir(cache_path):
            os.mkdir(cache_path)

        # Generate the mp3 file for the song if it has not already been generated.
        cache_file = os.path.join(cache_path, "{}.mp3".format(song))
        if not os.path.isfile(os.path.join(cache_path, "{}.mp3".format(song))):
            nbs_file = os.path.join(nbs_path, "{}.nbs".format(song))

            nbs.render_audio(song_path=nbs_file, 
                             output_path=cache_file,
                             custom_sound_path=sound_path,
                             format="mp3")

        return discord.FFmpegPCMAudio(cache_file)


    # Play a noteblock song from a selection of .nbs files.
    @app_commands.command(name="play", description="Play a noteblock song in your current voice channel")
    @app_commands.describe(song="Name of the noteblock song to play")
    async def play_song(self, interaction: discord.Interaction, song: str):
        await botlog.command_used(interaction.user.name + "#" + interaction.user.discriminator,
                                  interaction.command.name)
        
        voice_state = interaction.user.voice
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)

        if self.shuffling:
            await interaction.response.send_message("A shuffled playlist is currently playing", ephemeral=True)
        
        # Check if a ForumBot voice connection to the guild already exists
        voice_channel = voice_state.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if voice_client and voice_client.is_connected():
            voice = voice_client
        else:
            # Make ForumBot connect to the user's voice channel.
            voice = await voice_channel.connect()

        # Capitalize each word in song title input.
        song = capwords(song)

        await interaction.response.defer()
        try:
            voice.pause()
            audio = await self._select_song(song)
            voice.play(audio)
            await interaction.followup.send("<:jukebox:1063164063590404207> Now playing: `{}`".format(song))
        
        except FileNotFoundError:
            voice.resume()
            await interaction.followup.send("I'm sorry, I don't know `{}` <:whygod:1061614468234235904>".format(song))
            return

    
    # Continuosuly play random songs
    @app_commands.command(name="shuffle", description="Play random songs continuously")
    async def shuffle(self, interaction: discord.Interaction):
        await botlog.command_used(interaction.user.name + "#" + interaction.user.discriminator,
                                  interaction.command.name)
        
        voice_state = interaction.user.voice
        
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)

        # Check if a ForumBot voice connection to the guild already exists.
        voice_channel = voice_state.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if voice_client and voice_client.is_connected():
            voice = voice_client
        else:
            # Make ForumBot connect to the user's voice channel.
            voice = await voice_channel.connect()
        
        # Get the list of all song files found under ../nbs
        song_list = os.listdir(os.path.join(os.path.dirname(__file__), os.path.join("..", "nbs")))
        song = random.choice(song_list)[:-4]

        await interaction.response.defer()
        await interaction.followup.send("**Shuffling**")
        voice.stop()
        self.shuffling = True

        while self.shuffling:
            # Delay 2 seconds between songs.
            await asyncio.sleep(2.0)

            if not voice.is_playing() and self.shuffling:
                try:
                    voice.stop()
                    audio = await self._select_song(song)
                    voice.play(audio)
                    await interaction.channel.send("<:jukebox:1063164063590404207> Now playing: `{}`".format(song))
                except FileNotFoundError:
                    await interaction.followup.send("I'm sorry, I don't know `{}` <:whygod:1061614468234235904>".format(song))

                song = random.choice(song_list)[:-4]
        return


    @app_commands.command(name="stop", description="Stops the current song")
    async def stop(self, interaction: discord.Interaction):
        await botlog.command_used(interaction.user.name + "#" + interaction.user.discriminator,
                                  interaction.command.name)
        
        voice_state = interaction.user.voice
        
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)

        # Check if a ForumBot voice connection to the guild already exists.
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if not voice_client or not voice_client.is_connected():
            return
        
        voice = voice_client
        if not voice.is_playing():
            await interaction.response.send_message("Nothing to stop", ephemeral=True)

        # Stop shuffling songs.
        elif self.shuffling:
            self.shuffling = False
            voice.stop()
            await interaction.response.send_message("**Stopped shuffling**")

        # Stop the currently playing song.
        elif not self.shuffling:
            self.shuffling = False
            voice.stop()
            await interaction.response.send_message("**Stopped playing**")


    @app_commands.command(name="songs", description="Lists all playable songs")
    async def song_list(self, interaction: discord.Interaction):
        await botlog.command_used(interaction.user.name + "#" + interaction.user.discriminator,
                                  interaction.command.name)
        
        embeds = []
        song_list = os.listdir(os.path.join(os.path.dirname(__file__), os.path.join("..", "nbs")))
        song_list.sort(reverse=True)

        # Build up a paginator with each embed containing no more than 10 songs.
        q = deque(song_list)
        while len(q) != 0:
            e = discord.Embed(title="Songs", color=discord.Color.from_str("#555555"))
            e.set_author(name="NBS Player")
            e.description = ""

            for _ in range(0, 9):
                if len(q) == 0:
                    break
                e.description += "<:jukebox:1063164063590404207> " + q.pop()[:-4] + "\n"

            embeds.append(e)

        next_button = discord.ui.Button(label="\u25ba", style=discord.ButtonStyle.primary)
        prev_button = discord.ui.Button(label="\u25c4", style=discord.ButtonStyle.primary)
        
        await Paginator(next_button=next_button, previous_button=prev_button, delete_on_timeout=True).start(interaction, embeds)


    @app_commands.command(name="leave", description="Disconnects the bot from voice channels")
    async def disconnect(self, interaction: discord.Interaction):
        await botlog.command_used(interaction.user.name + "#" + interaction.user.discriminator,
                                  interaction.command.name)
        
        voice_state = interaction.user.voice
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
        
        # Check if a ForumBot voice connection to the guild already exists.
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_connected():
            self.shuffling = False
            voice = voice_client
            voice.stop()
            await voice.disconnect()
            await interaction.response.send_message("Ciao!")
        
        else:
            await interaction.response.send_message("I'm not connected to a voice channel!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Player(bot))
