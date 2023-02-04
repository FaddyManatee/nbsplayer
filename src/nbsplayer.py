import os
import asyncio
import random
import paginator
import nbswave as nbs
import discord
from discord import app_commands
from discord.ext import commands
from collections import deque


class Player(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.shuffling = False

    
    async def _song_selector(self, song):
        if not os.path.isdir(os.path.join(os.path.dirname(__file__), os.path.join("..", "cache"))):
            os.mkdir(os.path.join(os.path.dirname(__file__), os.path.join("..", "cache")))
        
        # Capitalize each word in song title input.
        title = song.split(" ")
        song = ""
        for word in title:
            song += word.upper() + " "
        song = song.strip()

        # https://ffbinaries.com/downloads
        if not os.path.isfile(os.path.join(os.path.dirname(__file__), os.path.join("..", "cache", "{}.mp3".format(song)))):
            nbs_file = os.path.join(os.path.dirname(__file__), os.path.join("..", "nbs", "{}.nbs".format(song)))
            nbs.render_audio(nbs_file, os.path.join(os.path.dirname(__file__), os.path.join("..", "cache", "{}.mp3".format(song))),
                                format="mp3")

        return discord.FFmpegPCMAudio(os.path.join(os.path.dirname(__file__), os.path.join("..", "cache", "{}.mp3".format(song))))


    # Play a noteblock song from a selection of .nbs files.
    @app_commands.command(name="play", description="Play a noteblock song in your current voice channel")
    @app_commands.describe(song="Name of the noteblock song to play")
    async def play_song(self, interaction: discord.Interaction, song: str):
        voice_state = interaction.user.voice
        
        if voice_state is not None and not self.shuffling:
            voice_channel = voice_state.channel

            # Check if a ForumBot voice connection to the guild already exists.
            voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

            if voice_client and voice_client.is_connected():
                voice = voice_client
            else:
                voice = await voice_channel.connect()

            await interaction.response.defer()
            try:
                voice.stop()
                audio = await self._song_selector(song)
                voice.play(audio)
                await interaction.followup.send("<:jukebox:1063164063590404207> Now playing: `{}`".format(song))
            except FileNotFoundError:
                await interaction.followup.send("I'm sorry, I don't know `{}` <:whygod:1061614468234235904>".format(song))
                return

        elif self.shuffling:
            await interaction.response.send_message("A shuffled playlist is currently playing", ephemeral=True)
            
        else:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)

    
    # Continuosuly play random songs
    @app_commands.command(name="shuffle", description="Play random songs continuously")
    async def shuffle(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        
        if voice_state is not None:
            voice_channel = voice_state.channel

            # Check if a ForumBot voice connection to the guild already exists.
            voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

            if voice_client and voice_client.is_connected():
                voice = voice_client
            else:
                voice = await voice_channel.connect()
            
            song_list = os.listdir(os.path.join(os.path.dirname(__file__), os.path.join("..", "nbs")))
            song = random.choice(song_list)[:-4]

            await interaction.response.defer()
            await interaction.followup.send("**Shuffling**")
            voice.stop()
            self.shuffling = True

            while self.shuffling:
                await asyncio.sleep(2.0)
                if not voice.is_playing() and self.shuffling:
                    try:
                        voice.stop()
                        audio = await self._song_selector(song)
                        voice.play(audio)
                        await interaction.channel.send("<:jukebox:1063164063590404207> Now playing: `{}`".format(song))
                    except FileNotFoundError:
                        await interaction.followup.send("I'm sorry, I don't know `{}` <:whygod:1061614468234235904>".format(song))

                    song = random.choice(song_list)[:-4]

            return
        
        else:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)


    @app_commands.command(name="stop", description="Stop playing the shuffled playlist")
    async def stop(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        
        if voice_state is not None and self.shuffling:
            # Check if a ForumBot voice connection to the guild already exists.
            voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

            if voice_client and voice_client.is_connected():
                voice = voice_client
                self.shuffling = False
                voice.stop()
                await interaction.response.send_message("**Stopped shuffling**")

        elif voice_state is not None and not self.shuffling:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

            if voice_client and voice_client.is_connected():
                voice = voice_client
                self.shuffling = False
                voice.stop()
                await interaction.response.send_message("**Stopped playing**")

        elif not self.shuffling:
            await interaction.response.send_message("Nothing to stop", ephemeral=True)

        else:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)


    @app_commands.command(name="songs", description="Lists all playable songs")
    async def song_list(self, interaction: discord.Interaction):
        embeds = []
        song_list = os.listdir(os.path.join(os.path.dirname(__file__), os.path.join("..", "nbs")))
        song_list.sort(reverse=True)

        q = deque(song_list)

        while len(q) != 0:
            e = discord.Embed(title="Songs", color=discord.Color.random())
            e.set_author(name="NBS Player")
            e.description = ""

            for _ in range(0, 9):
                if len(q) == 0:
                    break
                e.description += "<:jukebox:1063164063590404207> " + q.pop()[:-4] + "\n"

            embeds.append(e)

        next_button = discord.ui.Button(label="\u25ba", style=discord.ButtonStyle.primary)
        prev_button = discord.ui.Button(label="\u25c4", style=discord.ButtonStyle.primary)
        
        await paginator.Simple(NextButton=next_button, PreviousButton=prev_button, DeleteOnTimeout=True).start(interaction, embeds)


    @app_commands.command(name="leave", description="Disconnects the bot from voice channels")
    async def disconnect(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        
        if voice_state is not None:
            # Check if a ForumBot voice connection to the guild already exists.
            voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

            if voice_client and voice_client.is_connected():
                self.shuffling = False
                voice = voice_client
                voice.stop()
                await voice.disconnect()
                await interaction.response.send_message("Ciao!")

        else:
            await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Player(bot))
