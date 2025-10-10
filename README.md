# Acki Nacki Auto Claim Bot

A Python-based automation bot for claiming rewards from the Acki Nacki Telegram Web App.

![Acki Nacki Bot Demo](https://cdn.prod.website-files.com/668d27deabaf19c425217a24/66979cdce6212609480c88fa_Phone%20pic.png)

![Acki Nacki Bot Demo](https://github.com/user-attachments/assets/5f86aad7-d5eb-4724-a3d1-02f2e1a57952)

## Features

- **Automatic Reward Claiming**: Automatically claims rewards when farming session expires
- **User-Friendly Display**: Shows real-time countdown timer and farming progress
- **Token Management**: Securely stores and manages your Telegram authentication token
- **Error Handling**: Robust error handling with automatic retries
- **Colorful Console Interface**: Rich console output for better user experience

## Requirements

- Python 3.8+
- pip (Python package installer)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/xietsunzao/ackinacki-autoclaim.git
cd ackinacki-autoclaim
```

### Step 2: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 3: Get Your Session Data

To get your session data from the Acki Nacki web app:

1. Open Telegram and start the Acki Nacki bot
2. When you get the start link, it will look like: `https://t.ackinacki.com/?startapp=eyJ...`
3. Copy **only the base64 part** after `startapp=` (starts with 'eyJ')

   Example:
   ```
   eyJzZXNzaW9uX2lkIjoiNDQ5MzNmYzctZjQ5Yi00MmRlLWFkNTQtNDYxMTJjZDM3YWU4IiwibG9jYWxlIjoiZW4iLCJyZWRpcmVjdCI6bnVsbH0
   ```

4. Place this session data in `token.txt` file (or paste it when the bot prompts you)

**Alternative method** - Get from browser:
1. Open Acki Nacki in browser: https://t.ackinacki.com
2. Open Developer Tools (F12)
3. Go to Network tab
4. Look for the initial page load
5. Find the URL parameter `startapp=` and copy the base64 value

**Note**: The session data is sensitive information. Never share it with anyone.

### Step 4: Run the Bot

```bash
python main.py
```

## How It Works

The bot performs the following operations:

1. Reads session data from `token.txt`
2. Exchanges session ID for a fresh access token
3. Connects to the Acki Nacki API
4. Monitors your farming task status
5. Automatically claims rewards when farming completes
6. Automatically starts new farming sessions
7. Displays real-time information including:
   - Username and points
   - Friends count
   - Farm boost level (1-∞)
   - Boost progress boxes (5 per day)
   - Countdown timer until next claim

## Display Information

The bot shows:
- 🎮 Username and ⭐ Points
- 👥 Friends Count
- Farm Boost Level
- Progress Boxes (⭐)
- Countdown Timer

## Error Handling

The bot includes comprehensive error handling for:
- Token expiration
- Invalid tokens
- Network issues
- API errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The developer is not responsible for any consequences of using this bot.
