# Hydra-Revived

Hydra-Revived is an open-source Discord music bot, inspired by the now-defunct Hydra bot. This reworked version aims to provide a robust and customizable music playback experience for Discord servers, utilizing the Discord.py library with the Wavelink extension.

## Features

- **Music Playback:** Enjoy seamless music playback with commands for playing, pausing, stopping, skipping, looping, shuffling, and more.
- **Interactive Controls:** Use the interactive buttons to control the music playback conveniently.
- **Favorites Playlist:** Save you or other user's favorite songs to a private playlist stored in a MongoDB database.
- **Server Configuration:** Set up and configure the bot for your Discord server, including defining a music channel and specifying a moderation role.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Discord.py library
- Wavelink extension
- MongoDB database

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/PixlFlip-Enterprises/Hydra-Revived.git
   cd Hydra-Revived
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   Create a `.env` file in the project root and add the following:

   ```env
   DISCORD_TOKEN=your_discord_bot_token
   MONGO_URL=your_mongodb_connection_url
   MONGO_USER=your_username
   MONGO_PASS=your_password
   ```

4. Run the bot:

   ```bash
   python main.py
   ```

## Usage

1. Invite the bot to your Discord server.
2. Set up the server profile using the `/setup` slash command to define the music channel and moderation role.
3. Interact with the bot using commands like play, pause, stop, skip, etc., in the designated music channel.

For detailed command usage and customization options, refer to the code documentation and comments in the `main.py` file.

## Contributing

Contributions are welcome! If you have suggestions, bug reports, or would like to contribute new features, please follow the guidelines outlined in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- Thanks to the original creators of the Hydra bot for the inspiration.
- Special appreciation to the Discord.py and Wavelink communities for their excellent resources.

Feel free to explore, customize, and contribute to Hydra-Revived! If you encounter any issues or have questions, create an issue on GitHub, and we'll be happy to assist.