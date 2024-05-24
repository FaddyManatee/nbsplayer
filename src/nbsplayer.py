import os
import random
import nbswave as nbs
import discord
from discord import app_commands
from discord.ext import commands
from collections import deque
from paginator import Paginator
from string import capwords
from asyncio import sleep


class Player(commands.Cog):
    icon = "<:jukebox:1063164063590404207>"
    error_emoji = "<:whygod:1061614468234235904>"

    def __init__(self, bot: commands.Bot, nbs_path: str, sound_path: str, cache_path: str) -> None:
        self._bot = bot
        self._nbs_path = nbs_path
        self._sound_path = sound_path
        self._cache_path = cache_path
        self._song = str
        self._audio = discord.FFmpegPCMAudio
        self._shuffling = False


    def _song_list(self) -> list[str]:
        return sorted(os.listdir(self._nbs_path), reverse=True)


    async def _load_song(self) -> discord.FFmpegPCMAudio:
        # Generate .nbs song mp3 cache folder if it does not yet exist.
        if not os.path.isdir(self._cache_path):
            os.mkdir(self._cache_path)

        # Generate the mp3 file for the song if it has not already been generated.
        cache_file = os.path.join(self._cache_path, "{}.mp3".format(self._song))
        if not os.path.isfile(os.path.join(self._cache_path, "{}.mp3".format(self._song))):
            nbs_file = os.path.join(self._nbs_path, "{}.nbs".format(self._song))

            nbs.render_audio(song_path=nbs_file,
                             output_path=cache_file,
                             custom_sound_path=self._sound_path,
                             format="mp3")

        return discord.FFmpegPCMAudio(cache_file)


    @app_commands.command(name="nbplay", description="Play a noteblock song in your current voice channel")
    @app_commands.describe(song="Name of the noteblock song to play")
    async def play_song(self, interaction: discord.Interaction, song: str):
        voice_state = interaction.user.voice
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
            return

        if self._shuffling:
            await interaction.response.send_message("A shuffled playlist is currently playing", ephemeral=True)
            return

        # Check if a bot voice connection to the guild already exists
        voice_channel = voice_state.channel
        voice_client = discord.utils.get(self._bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_connected():
            voice = voice_client
        else:
            # Make bot connect to the user's voice channel.
            voice = await voice_channel.connect()

        # Capitalize each word in song title input.
        self._song = capwords(song)

        await interaction.response.defer()
        try:
            voice.pause()
            self._audio = await self._load_song()
            voice.play(self._audio)
            await interaction.followup.send("{} Now playing: `{}`".format(Player.icon, self._song))

        except FileNotFoundError:
            voice.resume()
            await interaction.followup.send("I'm sorry, I don't know `{}` {}".format(self._song, Player.error_emoji))
            return


    @app_commands.command(name="nbshuffle", description="Play random songs continuously")
    async def shuffle(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
            return

        # Check if a bot voice connection to the guild already exists.
        voice_channel = voice_state.channel
        voice_client = discord.utils.get(self._bot.voice_clients, guild=interaction.guild)

        if voice_client and voice_client.is_connected():
            voice = voice_client
        else:
            # Make bot connect to the user's voice channel.
            voice = await voice_channel.connect()

        await interaction.response.defer()
        await interaction.followup.send("**Shuffling**")
        voice.stop()
        self._song = random.choice(self._song_list())[:-4]
        self._shuffling = True

        while self._shuffling:
            # Delay 2 seconds between songs.
            await sleep(2.0)

            if not voice.is_playing() and self._shuffling:
                voice.stop()
                self._audio = await self._load_song()
                voice.play(self._audio)
                await interaction.channel.send("{} Now playing: `{}`".format(Player.icon, self._song))
                self._song = random.choice(self._song_list())[:-4]
        return


    @app_commands.command(name="nbskip", description="Skips to the next song when shuffling")
    async def skip(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
            return

        # Check if a bot voice connection to the guild already exists.
        voice_client = discord.utils.get(self._bot.voice_clients, guild=interaction.guild)
        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("I'm not connected to a voice channel!", ephemeral=True)
            return

        voice = voice_client
        if not voice.is_playing():
            await interaction.response.send_message("Nothing to skip", ephemeral=True)

        # Skip shuffled song.
        elif self._shuffling:
            await interaction.response.defer()
            await interaction.followup.send("**Skipping**")

            self._song = random.choice(self._song_list())[:-4]
            voice.stop()
            self._audio = await self._load_song()
            voice.play(self._audio)
            await interaction.channel.send("{} Now playing: `{}`".format(Player.icon, self._song))

        else:
            await interaction.response.send_message("You can't skip when not in shuffle mode!", ephemeral=True)


    @app_commands.command(name="nbstop", description="Stops the current song")
    async def stop(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
            return

        # Check if a bot voice connection to the guild already exists.
        voice_client = discord.utils.get(self._bot.voice_clients, guild=interaction.guild)
        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("I'm not connected to a voice channel!", ephemeral=True)
            return

        voice = voice_client
        if not voice.is_playing():
            await interaction.response.send_message("Nothing to stop", ephemeral=True)

        # Stop shuffling songs.
        elif self._shuffling:
            self._shuffling = False
            voice.stop()
            await interaction.response.send_message("**Stopped shuffling**")

        # Stop the currently playing song.
        elif not self._shuffling:
            self._shuffling = False
            voice.stop()
            await interaction.response.send_message("**Stopped playing**")


    @app_commands.command(name="nbsongs", description="Lists all playable songs")
    async def song_list(self, interaction: discord.Interaction):
        embeds = []

        # Build up a paginator with each embed containing no more than 10 songs.
        q = deque(self._song_list())
        while len(q) != 0:
            e = discord.Embed(title="Songs", color=discord.Color.from_str("#555555"))
            e.set_author(name="NBS Player")
            e.description = ""

            for _ in range(0, 9):
                if len(q) == 0:
                    break
                e.description += Player.icon + " " + q.pop()[:-4] + "\n"
            embeds.append(e)

        next_button = discord.ui.Button(label="\u25ba", style=discord.ButtonStyle.primary)
        prev_button = discord.ui.Button(label="\u25c4", style=discord.ButtonStyle.primary)

        await Paginator(next_button=next_button, previous_button=prev_button, delete_on_timeout=True).start(interaction, embeds)


    @app_commands.command(name="nbleave", description="Disconnects the bot from voice channels")
    async def disconnect(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        if voice_state is None:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
            return

        # Check if a bot voice connection to the guild already exists.
        voice_client = discord.utils.get(self._bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_connected():
            self._shuffling = False
            voice = voice_client
            voice.stop()
            voice.cleanup()
            await voice.disconnect()
            await interaction.response.send_message("Ciao!")

        else:
            await interaction.response.send_message("I'm not connected to a voice channel!", ephemeral=True)


    @app_commands.command(name="nbdev", description="Get the link to NBS Player's source code")
    async def credits(self, interaction: discord.Interaction):
        await interaction.response.send_message("Thank the Maker: https://github.com/FaddyManatee/nbsplayer")
