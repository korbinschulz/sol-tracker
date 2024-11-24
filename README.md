# SolTracker

SolTracker is a Python CLI tool that allows you to monitor Solana wallet transactions in real-time. It provides notifications for token swaps and transfers through Discord and Telegram webhooks, making it easy to track activity on multiple wallets.

---

## Features

- Track multiple Solana wallets simultaneously.
- Detect token swaps and transfers.
- Send real-time notifications to Discord and Telegram.
- User-friendly CLI interface for managing wallets and configurations.
- Easy setup and configuration with JSON files.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/korbinschulz/sol-tracker.git
   cd sol-tracker
___
**CLI Commands**

<img width="446" alt="Screenshot 2024-11-24 at 3 39 16 PM" src="https://github.com/user-attachments/assets/60a4221b-a167-4e05-a48b-f1f9f0854afb">
<img width="490" alt="Screenshot 2024-11-24 at 3 39 27 PM" src="https://github.com/user-attachments/assets/42ff7532-6538-41ba-ba15-7915ae6f6a62">

**Main Menu:**

* Start the CLI interface: `python main.py`

**Options:**

* **Start Tracking:** Begin monitoring your wallets.
* **Manage Wallets:** Add, remove, or list wallets.
* **Info:** Set or update API keys and webhook URLs.

**Start Tracking:**

* Monitors your wallets for token swaps and transfers.
* Sends notifications to Discord or Telegram.

**Manage Wallets:**

* **Add wallets:**
    * Enter wallet name: My Wallet
    * Enter wallet address: <wallet_address>
* **Remove wallets:** Select a wallet from the list to delete it.

**Manage Info:**

* Set your Helius API Key, Discord Webhook URL, and Telegram Webhook URL.

**Configuration**

SolTracker uses two JSON files for configuration:

* **wallets.json:** Stores wallet information:

```json
[
  {
    "name": "My Wallet",
    "address": "YourSolanaWalletAddress"
  }
]
```

* **info.json:** Stores API keys and webhook URLs:

```json
{
  "helius_api_key": "YourHeliusAPIKey",
  "discord_webhook": "YourDiscordWebhookURL",
  "telegram_webhook": "YourTelegramWebhookURL"
}
```

**Notifications**

SolTracker sends notifications in the following format:

**Discord**

* Embed Title: Wallet Name - **BOUGHT/SOLD**
* Fields:
    * Token Mint: Token address.
    * Token Amount: Amount of tokens transferred.
    * Sol Amount: Amount of SOL transferred (converted from lamports).
    * Transaction: Link to view the transaction on Solscan.
 
<img width="400" height="400" alt="Screenshot 2024-11-24 at 3 38 29 PM" src="https://github.com/user-attachments/assets/074d4015-b950-4ccf-9e04-dad665a4e738">

