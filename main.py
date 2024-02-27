


import discord
from discord.ext import commands
from discord.commands import Option
import wavelink
from wavelink import Player, YouTubeTrack, YouTubePlaylist, SoundCloudTrack, SoundCloudPlaylist
from wavelink.ext import spotify
import requests, io, os, re
from PIL import Image
from pymongo import MongoClient
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client and database
mongo_url = os.getenv("MONGO_URL")

# Replace these with your MongoDB connection details in the .env
username = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")
db_url = f"mongodb://{username}:{password}@cluster.mongodb.net:27017/"
# Create a MongoClient object
client = MongoClient(db_url)
db = client["hydra_revived"]

# load config
config = {
    "embed": {
        "footer_text": "Hydra Revived v1.0",
        "error_photo": "https://i.ytimg.com/vi/cJWojzF3wq8/hqdefault.jpg"
    },
    "music": {
        "host": "your lavalink server ip with port here",
        "pass": "your lavalink server pass here",
        "footer": "PixlFlip Enterprises 2023"
    },
}

# variables for the players in each guild. UI not player proper
setup_channels = []
views = {}

# Initialize Discord bot using env variable
discord_token = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(command_prefix='/', intents=discord.Intents.default())


"""
Music View Class
"""


class MusicView(discord.ui.View):  # Class MusicView (subclasses discord.ui.View)
    def __init__(self):
        super().__init__(timeout=None)

    """All Buttons you create in here will have no timeout"""

    @discord.ui.button(label="", row=0, style=discord.ButtonStyle.primary, emoji="⏯")
    async def play_button_callback(self, button, interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)
        if player is not None:
            if player.is_paused():
                await player.resume()
                await interaction.response.send_message("Music resumed!", ephemeral=True, delete_after=3)
            else:
                await player.pause()
                await interaction.response.send_message("Music paused!", ephemeral=True, delete_after=3)
        else:
            await interaction.response.send_message("I'm not in a voice channel right now!", delete_after=5)

    @discord.ui.button(label="", row=0, style=discord.ButtonStyle.primary, emoji="⏭")
    async def next_track_button_callback(self, button, interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)
        if not player:
            await interaction.response.send_message("I am not in a voice channel", ephemeral=True, delete_after=5)
            return
        if player.is_paused():
            await interaction.response.send_message("Music is paused.", ephemeral=True, delete_after=5)
            return
        if not player.is_playing():
            await interaction.response.send_message("I am not playing anything right now.", ephemeral=True, delete_after=5)
            return
        await player.stop()

    @discord.ui.button(label="", row=0, style=discord.ButtonStyle.primary, emoji="⏹")
    async def stop_button_callback(self, button, interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)
        if player is not None:
            # get the message with the embed
            message = views[interaction.guild.id]
            # create discord object for image
            file = discord.File("resources/static.png", filename='music_artwork.png')
            # build and return the embed
            embed = discord.Embed(title="Music Player", description="No song playing currently",
                                  color=discord.Colour.blue())
            embed.set_footer(text=config['music']['footer'])
            embed.set_image(url="attachment://music_artwork.png")
            # update the message with the new embed
            await message.edit("Queue is empty", file=file, embed=embed)
            await player.disconnect()
            await interaction.response.send_message("Bot has been disconnected from the voice channel!", ephemeral=True, delete_after=5)

    @discord.ui.button(label="", row=0, style=discord.ButtonStyle.primary, emoji="🔁")
    async def loop_button_callback(self, button, interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)
        if not player:
            await interaction.response.send_message("I am not in a voice channel", ephemeral=True, delete_after=5)
            return
        if player.is_paused():
            await interaction.response.send_message("Music is paused.", ephemeral=True, delete_after=5)
            return
        if not player.is_playing():
            await interaction.response.send_message("I am not playing anything right now.", ephemeral=True,
                                                    delete_after=5)
            return
        # loop
        player.queue.loop_all = True
        await interaction.response.send_message("Looping the Queue", ephemeral=True, delete_after=5)

    @discord.ui.button(label="", row=0, style=discord.ButtonStyle.primary, emoji="🔀")
    async def shuffle_button_callback(self, button, interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)
        if not player:
            await interaction.response.send_message("I am not in a voice channel", ephemeral=True, delete_after=5)
            return
        if player.is_paused():
            await interaction.response.send_message("Music is paused.", ephemeral=True, delete_after=5)
            return
        if not player.is_playing():
            await interaction.response.send_message("I am not playing anything right now.", ephemeral=True,
                                                    delete_after=5)
            return
        # shuffle
        player.queue.shuffle()
        await interaction.response.send_message("Queue shuffled!", ephemeral=True, delete_after=5)

    @discord.ui.button(label="", row=1, style=discord.ButtonStyle.primary, emoji="💙")
    async def favorite_button_callback(self, button, interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)
        if not player:
            await interaction.response.send_message("I am not in a voice channel", ephemeral=True, delete_after=5)
            return
        if not player.is_playing():
            await interaction.response.send_message("I am not playing anything right now.", ephemeral=True,
                                                    delete_after=5)
            return

        # Remove favorite from the database of the user
        try:
            pq = player.queue.history.get()
        except wavelink.exceptions.QueueEmpty:
            await interaction.response.send_message("The queue is empty. No song to remove from favorites.",
                                                    ephemeral=True, delete_after=5)
            return
        # add favorite to db of user
        if pq is not None:
            # add to db
            music_favorites = db['music_favorites']
            music_favorites.insert_one({
                "user_id": interaction.user.id,  # Add the user_id to the database
                "song_uri": pq.uri,
                "song_title": pq.title
            })
        await interaction.response.send_message("Added to your favorites playlist!", ephemeral=True, delete_after=5)

    @discord.ui.button(label="", row=1, style=discord.ButtonStyle.primary, emoji="💔")
    async def unfavorite_button_callback(self, button, interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)
        if not player:
            await interaction.response.send_message("I am not in a voice channel", ephemeral=True, delete_after=5)
            return
        if not player.is_playing():
            await interaction.response.send_message("I am not playing anything right now.", ephemeral=True,
                                                    delete_after=5)
            return

        # Remove favorite from the database of the user
        try:
            pq = player.queue.history.get()
        except wavelink.exceptions.QueueEmpty:
            await interaction.response.send_message("The queue is empty. No song to remove from favorites.",
                                                    ephemeral=True, delete_after=5)
            return

        if pq is not None:
            # Query the database
            music_favorites = db['music_favorites']

            # Delete the record
            result = music_favorites.delete_one({
                "user_id": interaction.user.id,  # Match the user_id
                "song_title": pq.title,
            })

            if result.deleted_count > 0:
                await interaction.response.send_message("Removed from your favorites playlist!", ephemeral=True,
                                                        delete_after=5)
            else:
                await interaction.response.send_message("Song not found in your favorites.", ephemeral=True,
                                                        delete_after=5)

    @discord.ui.button(label="", row=1, style=discord.ButtonStyle.primary, emoji="🎼")
    async def start_favorites_playlist_button_callback(self, button, interaction):
        # # Check if the user is in a voice channel
        if interaction.user.voice is None:
            return await interaction.response.send_message("You must be in a voice channel to use this command.", delete_after=12)
        # Initialize the player or get the existing one
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id) or await interaction.user.voice.channel.connect(cls=wavelink.Player)
        # Access the database collection
        music_favorites = db['music_favorites']
        # Fetch all favorite songs of the user from the database and convert to a list
        favorite_songs_list = music_favorites.find({"user_id": interaction.user.id})
        # Iterate over the list of favorite songs
        for song in favorite_songs_list:
            # Search for the song
            song_search = await search_song(song['song_title'])
            song_searched = song_search[0].pop(0)
            # if player is playing, put into the queue, else play immediately
            if not player.is_playing():
                await player.play(song_searched)
                await update_music_message(player, config, views, song_searched)
                await interaction.response.send_message("Playing your favorites playlist!", ephemeral=True, delete_after=15)
            else:
                await player.queue.put_wait(song_searched)
                await update_music_message(player, config, views, song_searched)


async def setup_music(bot, channel_id, guild_id):
    channel = bot.get_channel(int(channel_id))
    # save the channel id
    setup_channels.append(int(channel_id))
    # update the channel description
    await channel.edit(reason="Music Channel Setup",
                       topic=":play_pause: Pause/Resume the song. :stop_button: Stop and empty the queue. :track_next: Skip the song. :arrows_counterclockwise: Switch between the loop modes. :twisted_rightwards_arrows: Shuffle the queue. :blue_heart: Add the current song to your private playlist. :broken_heart: Remove the current song from your private playlist.")
    # sending banner image
    with open('resources/musicbanner.png', 'rb') as f:
        file = discord.File(f)
        await channel.send(file=file)
    # create discord object for image
    file = discord.File("resources/static.png", filename='music_artwork.png')
    # build and return the embed
    embed = discord.Embed(title="Music Player", description="No song playing currently",
                          color=discord.Colour.blue())
    embed.set_footer(text=config['music']['footer'])
    embed.set_image(url="attachment://music_artwork.png")
    message = await channel.send("Queue is empty", file=file, embed=embed, view=MusicView())
    # Storing the message id in views dictionary
    views[guild_id] = message  # .id


async def connect_nodes():
    """Connect to our Lavalink nodes."""
    await bot.wait_until_ready()  # wait until the bot is ready
    # create a node
    # await wavelink.NodePool.create_node(bot=self.bot, host=config['music']['host'], port=config['music']['port'], password=config['music']['pass'])
    node: wavelink.Node = wavelink.Node(uri=config['music']['host'], password=config['music']['pass'])
    await wavelink.NodePool.connect(client=bot, nodes=[node])

# function for searching songs
async def search_song(search_query):
    youtube_pattern = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/')
    spotify_pattern = re.compile(r'(https?://)?(open\.spotify\.com/|spotify:)(track|playlist|album)/')
    soundcloud_pattern = re.compile(r'(https?://)?(www\.)?(soundcloud\.com)/')
    try:
        if youtube_pattern.match(search_query):
            # Handle playlists
            if 'list=' in search_query:
                playlists = await wavelink.YouTubePlaylist.search(search_query)
                if playlists:
                    return playlists.tracks, None  # Return the list of tracks in the first playlist
            else:
                tracks = await wavelink.YouTubeTrack.search(search_query)
                if tracks:
                    return [tracks[0]], None  # Return a single track as a list
        elif spotify_pattern.match(search_query):
            return None, "Spotify links are unsupported. Use Youtube for now!"
        elif soundcloud_pattern.match(search_query):
            # Handle SoundCloud playlists (assuming it works like YouTubePlaylist)
            if '/sets/' in search_query:
                playlists = await wavelink.SoundCloudPlaylist.search(search_query)
                if playlists:
                    return playlists.tracks, None  # Return the list of tracks in the playlist
            else:
                tracks = await wavelink.SoundCloudTrack.search(search_query)
                if tracks:
                    return [tracks[0]], None  # Return a single track as a list
        else:
            tracks = await wavelink.YouTubeTrack.search(search_query)
            if tracks:
                return [tracks[0]], None  # Return a single track as a list
    except:
        print("track could not be found")
    return None, "No song found or error playing track"


async def update_music_message(player, config, views, next_song=None, empty_queue=False):
    # Initialize variables
    message = views[player.guild.id]
    song_title = "No song playing currently" if next_song == None else str(next_song.title)
    color = discord.Colour.blue()

    # Determine if the next_song is from YouTube or SoundCloud
    is_youtube = 'youtube' in str(next_song.uri).lower() if next_song else False
    is_soundcloud = 'soundcloud' in str(next_song.uri).lower() if next_song else False

    # Process the image
    if is_soundcloud:
        image_url = "resources/soundcloud.png"
        file = discord.File(image_url, filename='music_artwork.png')
    elif is_youtube:
        image_url = f"https://img.youtube.com/vi/{str(next_song.uri).split('v=')[1]}/0.jpg"
        img = Image.open(io.BytesIO(requests.get(image_url).content))
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        file = discord.File(output, filename='music_artwork.png')
    else:
        image_url = "resources/static.png"
        file = discord.File(image_url, filename='music_artwork.png')

    # Create the embed
    embed = discord.Embed(title="Music Player", description=song_title, color=color)
    embed.set_footer(text=config['music']['footer'])
    embed.set_image(url="attachment://music_artwork.png")

    # Prepare the queue message
    return_msg = ""
    if not empty_queue:
        return_msg = ""
        song_no = len(player.queue)
        total_length = 0
        additional_songs = 0

        for song in reversed(player.queue):
            line = f"{song_no}) {song.title}\n"
            line_length = len(line)

            if total_length + line_length > 1900:  # Limiting the message length
                additional_songs += 1
            else:
                return_msg = line + return_msg
                total_length += line_length

            song_no -= 1

        if additional_songs > 0:
            return_msg += f"...and {additional_songs} more"
    else:
        return_msg = "Queue is empty"

    # Update the message with the new embed
    await message.edit(content=return_msg, file=file, embed=embed)

@bot.event
async def on_ready():
    print('{0.user.name} logged in with no issues \nWith ID:{0.user.id}'.format(bot))

    # guilds from mongo
    guilds_collection = db['guilds']
    # go through guilds bot is in
    for guild in bot.guilds:
        # Check if the bot's guild exists in the registered servers in MongoDB
        registered_guild = guilds_collection.find_one({"id": guild.id})
        # if bot not registered, continue on

        if not registered_guild:
            print(f"Leaving unregistered guild: {guild.name}")
            await guild.leave()
            continue

        # get music channel id
        music_channel_id = int(registered_guild.get("music_channel"))
        # if no id then continue
        if not music_channel_id:
            print(f"Failed to find music channel for guild {guild.name}")
            continue
        # Delete previous messages in the music channel
        music_channel = bot.get_channel(music_channel_id)
        if music_channel is None:
            print(f"Failed to find music channel for guild {guild.name}")
            continue
        # remove all messages in music channel
        await music_channel.purge()
        # Run setup command
        await setup_music(bot, channel_id=music_channel_id, guild_id=guild.id)
        print('connected to music nodes')
        await connect_nodes()  # connect to the server


@bot.event
async def on_guild_join(guild):
    # This function will run whenever the bot joins a new server
    print(f"Joined {guild.name} (ID: {guild.id})")
    # Here you can include any additional code you want to run when the bot joins a new server
    # Define the welcome message
    message = f"To set up my music abilities please run `/setup`"
    # Send a welcome message to the general channel of the new server
    general_channel = discord.utils.get(guild.channels, name='general')
    if general_channel is not None:
        await general_channel.send(message)


@bot.event
async def on_guild_remove(guild):
    # This function will run whenever the bot is removed from a server
    print(f"Left Server: {guild.name} (ID: {guild.id})")


@bot.event
async def on_message(message):
    if message.channel.id in setup_channels and message.author.id != bot.user.id:
        # delete the message
        await message.delete()

        # Check if the user is in a voice channel
        if message.author.voice is None:
            return await message.channel.send("You must be in a voice channel to use this command.",
                                              delete_after=12)

        # Initialize the player or get the existing one
        node = wavelink.NodePool.get_node()
        player = node.get_player(message.guild.id) or await message.author.voice.channel.connect(
            cls=wavelink.Player)

        # Search for the song
        songs, error_message = await search_song(message.content + " ")
        if error_message:
            return await message.channel.send(error_message, delete_after=12)
        if not songs:
            return await message.channel.send("No song found.", delete_after=12)

        # Play the first song in voice or add to queue
        first_song = songs.pop(0)
        if not player.is_playing():
            await player.play(first_song)
            await update_music_message(player, config, views, first_song)
            await message.channel.send(f"Now playing: `{first_song.title}`", delete_after=12)
        else:
            await player.queue.put_wait(first_song)
            await update_music_message(player, config, views, first_song)
            await message.channel.send(f"Added `{first_song.title}` to the queue", delete_after=12)

        # Queue the remaining songs (if any)
        for song in songs:
            await player.queue.put_wait(song)
        if songs:
            await update_music_message(player, config, views)



async def on_wavelink_track_end(self, payload):
    player = payload.player  # Access the player directly from the payload
    # Check if the queue is empty
    if not player.queue:
        # Disconnect the player if the queue is empty
        await player.disconnect()
        # update message
        await update_music_message(player, config, views, empty_queue=True)
        return
    # Get the next song from the queue
    next_song = player.queue.pop()
    # update message
    await update_music_message(player, config, views, next_song)
    # Play the next song
    await player.play(next_song)


bot.add_listener(on_wavelink_track_end, "on_wavelink_track_end")


@bot.slash_command(name="setup", description="Setup your server.")
async def setup(ctx, music_channel: Option(str, "ID of music channel", required=True, default="wrong"),
                mod_role: Option(str, "ID of role that can use mod commands", required=True, default="I am.")):
    # should take a moderation role id and the music channel id
    channel = bot.get_channel(ctx.channel.id)
    member = ctx.author
    guilds = db['guilds']
    guilds.insert_one(
        {"id": channel.guild.id, "music_channel": music_channel, "mod_role": mod_role})
    # perform operation and return msg

    # remove all messages in music channel
    await music_channel.purge()
    # Run setup command
    await setup_music(bot, channel_id=int(music_channel), guild_id=ctx.guild.id)
    await ctx.respond('Server Profile Created!')

# Run the bot using env variable
bot.run(discord_token)
