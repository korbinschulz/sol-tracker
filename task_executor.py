import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import click
import time

#global set for tracking last processed slot for the wallets being tracked
last_processed_slots = {}

def send_discord_notification(webhook_url, wallet_name, action, token_mint, token_amount, sol_amount, transaction_signature, coin_cap, coin_name, coin_ticker):
    """Send a Discord notification with a formatted embed."""
    try:
        embed_color = 65280 if action == "BOUGHT" else 16711680  # Green for BOUGHT, Red for SOLD
        embed = {
            "embeds": [
                {
                    "title": f"{wallet_name} - **{action}**",
                    "color": embed_color,
                    "fields": [
                        {
                            "name": "**Token**",
                            "value": f'${coin_ticker} - {coin_name}',
                            "inline": True
                        },
                        {
                            "name": "**Market Cap**",
                            "value": f'${coin_cap}',
                            "inline": False
                        },
                        {
                            "name": "**Token Mint**",
                            "value": token_mint,
                            "inline": False
                        },
                        {
                            "name": "**Token Amount**",
                            "value": str(token_amount),
                            "inline": False
                        },
                        {
                            "name": "**Sol Amount**",
                            "value": f"{sol_amount} SOL",
                            "inline": False
                        },
                        {
                            "name": "**Transaction**",
                            "value": f"[View Transaction](https://solscan.io/tx/{transaction_signature})",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": "Transaction Notification"
                    },
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())  # ISO 8601 format
                }
            ]
        }
        response = requests.post(webhook_url, json=embed)
        response.raise_for_status()
    except requests.RequestException as e:
        click.echo(f"Error sending Discord notification: {e}")


def send_telegram_notification(webhook_url, message):
    """Send a Telegram notification."""
    # filler logic, need to correct later
    try:
        response = requests.post(webhook_url, json={"text": message})
        response.raise_for_status()
    except requests.RequestException as e:
        click.echo(f"Error sending Telegram notification: {e}")


def execute_monitoring(wallet, helius_key, discord_webhook, telegram_webhook):
    wallet_name = wallet["name"]
    wallet_address = wallet["address"]

    # Initialize the last processed slot for this wallet
    if wallet_address not in last_processed_slots:
        last_processed_slots[wallet_address] = None

    while True:
        base_url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/transactions"
        params = {
            "api-key": helius_key,
            "types": ["TRANSFER", "SWAP"],
            "limit": 5,
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            transactions = response.json()

            # Process transactions
            if transactions:
                last_processed_slots[wallet_address] = process_transactions(
                    wallet, transactions, discord_webhook, telegram_webhook, last_processed_slots[wallet_address]
                )
            else:
                click.echo(f"No new transactions for {wallet_name} ({wallet_address}).")

            # Add a delay to avoid excessive API calls
            time.sleep(30)
        except requests.exceptions.RequestException as e:
            click.echo(f"Error fetching transactions for {wallet_name} - {wallet_address}: {e}")
            time.sleep(60)  # Retry after a delay

def process_transactions(wallet, transactions, discord_webhook, telegram_webhook, last_processed_slot):
    wallet_address = wallet["address"]
    transactions = sorted(transactions, key=lambda x: x["slot"])  # Sort by slot (oldest to newest)

    latest_slot = last_processed_slot

    for transaction in transactions:
        slot = transaction["slot"]

        # Skip transactions older than or equal to the last processed slot
        if last_processed_slot and slot <= last_processed_slot:
            continue

        # Update the latest slot to the current transaction's slot
        if not latest_slot or slot > latest_slot:
            latest_slot = slot

        # extract the solana value from the transaction
        sol_amount = round(
            next(
                (abs(account["nativeBalanceChange"]) / 1e9 for account in transaction["accountData"] if account["account"] == wallet_address),
                0.0
            ),
            4  # Round to 2 decimal places
        )

        coin_cap = 0
        coin_name = ""
        coin_ticker = ""

        # Process SWAP transactions
        if transaction["type"] == "SWAP":
            token_transfers = transaction.get("tokenTransfers", [])
            if token_transfers:
                from_token = token_transfers[0]  # Token swapped out
                to_token = token_transfers[1] if len(token_transfers) > 1 else None  # Token received

                if from_token["fromUserAccount"] == wallet_address:
                    # Wallet initiated a swap
                    message = (
                        f"Wallet {wallet['name']} ({wallet_address}) performed a swap:\n"
                        f"Swapped Out: {from_token['tokenAmount']} {from_token['mint']}\n"
                        f"Swapped In: {to_token['tokenAmount']} {to_token['mint'] if to_token else 'N/A'}\n"
                        f"Transaction: {transaction['signature']}"
                    )
                    #send_notifications(discord_webhook, telegram_webhook, message)

        # Process TRANSFER transactions
        elif transaction["type"] == "TRANSFER":
            for token_transfer in transaction.get("tokenTransfers", []):
                if token_transfer["toUserAccount"] == wallet_address:
                    # Buying a token
                    token_mint = token_transfer["mint"]
                    amount = token_transfer["tokenAmount"]
                    pump_link = f"https://frontend-api.pump.fun/coins/{token_mint}"

                    pump_response = requests.get(pump_link)
                    pump_response.raise_for_status()
                    pump_data = pump_response.json()

                    if isinstance(pump_data, dict):
                        coin_cap = pump_data.get('usd_market_cap', 0)
                        coin_name = pump_data.get('name', 'Unknown')
                        coin_ticker = pump_data.get('symbol', 'N/A')

                    coin_cap = round(coin_cap, 2)
                    send_discord_notification(discord_webhook, wallet['name'], "BOUGHT", token_mint, amount, sol_amount, transaction['signature'], coin_cap, coin_name, coin_ticker)

                elif token_transfer["fromUserAccount"] == wallet_address:
                    # Selling a token
                    token_mint = token_transfer["mint"]
                    amount = token_transfer["tokenAmount"]
                    pump_link = f"https://frontend-api.pump.fun/coins/{token_mint}"

                    pump_response = requests.get(pump_link)
                    pump_response.raise_for_status()
                    pump_data = pump_response.json()

                    if isinstance(pump_data, dict):
                        coin_cap = pump_data.get('usd_market_cap', 0)
                        coin_name = pump_data.get('name', 'Unknown')
                        coin_ticker = pump_data.get('symbol', 'N/A')

                    coin_cap = round(coin_cap, 2)
                    send_discord_notification(discord_webhook, wallet['name'], "SOLD", token_mint, amount, sol_amount, transaction['signature'], coin_cap, coin_name, coin_ticker)

    return latest_slot  # Return the highest slot processed

def run_tasks_concurrently(wallets, helius_api_key, discord_webhook, telegram_webhook):
    """Run monitoring tasks concurrently for all wallets with a small delay between task starts."""

    def execute_with_delay(wallet):
        """Wrapper to introduce a delay between tasks."""
        time.sleep(2)  # Add a 2-second delay before starting each task
        execute_monitoring(wallet, helius_api_key, discord_webhook, telegram_webhook)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(execute_with_delay, wallet) for wallet in wallets
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                click.echo(f"An error occurred: {e}")

