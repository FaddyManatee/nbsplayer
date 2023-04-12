# nbsplayer
A discord.py cog that adds Minecraft note block song playback functionality to your bot.

## Getting started
1) Setup required folders. You can name them as you like:<br/>
    - `cache`: Stores .mp3 files generated from .nbs files by nbsplayer. 
    - `nbs`: Stores the .nbs (note block song file format) files that you want the bot to be able to play.
    - `sounds`: Stores the .ogg files required by nbsplayer to generate a .mp3 file from a .nbs file.
    
    #### Examples
    - [Songs](https://github.com/FaddyManatee/ForumBot/tree/main/nbs)
    - [More songs](https://github.com/nickg2/NBSsongs/tree/master/songs)
    - [Commonly required sounds](https://github.com/FaddyManatee/ForumBot/tree/main/sounds)

2) Create a extension that uses the `nbsplayer` cog.
    ### player.py
    ```python
    import os
    from nbsplayer import Player
    from discord.ext import commands


    async def setup(bot: commands.Bot):
        cache = os.path.join(os.path.dirname(__file__), os.path.join("..", "cache"))    # Path to cache/
        nbs = os.path.join(os.path.dirname(__file__), os.path.join("..", "nbs"))        # Path to nbs/
        sounds = os.path.join(os.path.dirname(__file__), os.path.join("..", "sounds"))  # Path to sounds/

        await bot.add_cog(Player(bot, nbs_path=nbs, sound_path=sounds, cache_path=cache))

    ```
3) Add the extension to your bot.
    ### bot.py
    ```python
    import os
    import asyncio
    import discord
    from discord.ext import commands
    from dotenv import load_dotenv


    # Load cogs
    async def load():
        await bot.load_extension("player")  # Looks for extension in player.py
        await bot.load_extension("other")   # Looks for extension in other.py


    load_dotenv()
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = commands.Bot(command_prefix="! ", intents=intents)
                   
    asyncio.run(load())
    bot.run(os.getenv("TOKEN"))
    ```

## Commands

### /nbsongs
Lists the names of all playable songs from the `nbs` directory.

### /nbplay `songname`
Plays `songname` in your current voice channel.

### /nbleave
Disconnects the bot from its voice channel.

### /nbstop
Stops the currently playing song or shuffled playlist.

### /nbloop
Loops the currently playing song until /nbstop is called.

### /nbshuffle
Continues to play random songs from the playlist in your current voice channel.

### /nbskip
Skips to the next song when shuffling.
