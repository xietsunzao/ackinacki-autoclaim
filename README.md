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
cd ackinacki-auto-claim
```

### Step 2: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 3: Get Your Token

To get your Telegram token from the Acki Nacki web app:

1. Open Acki Nacki in Telegram Web App (https://twa.ackinacki.org/)
2. Open Developer Tools (F12 or right-click and select "Inspect")
3. Go to the "Network" tab
4. Look for requests to `/api/users/me` endpoint
5. Click on the request
6. In the "Headers" section, find "telegram-data" under Request Headers
7. Copy the entire token value (starts with 'eyJ')

Example of where to find the token:

![Token Location Guide](https://github.com/user-attachments/assets/0bed9884-3ade-4418-a010-379b6e68c11b)

**Note**: The token is sensitive information. Never share it with anyone.

Place your token in `token.txt` file or the bot will prompt you to enter it when first running.

### Step 4: Run the Bot

```bash
python main.py
```

## How It Works

The bot performs the following operations:

1. Validates and manages your Telegram authentication token
2. Connects to the Acki Nacki API
3. Monitors your farming status
4. Automatically starts farming sessions when needed
5. Displays real-time information including:
   - Username and points
   - Friends count
   - Farm boost level
   - Boost progress boxes
   - Countdown timer

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

## Support

If you find this bot helpful, consider supporting the developer:

0x12aab224FA1D30Ee44575335B7767D8c89cD70A9

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The developer is not responsible for any consequences of using this bot.
