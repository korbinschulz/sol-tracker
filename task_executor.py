import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import capsolver
from urllib.parse import quote
import click

def send_notifications(discord_webhook, telegram_webhook, message):
    """Send notifications to Discord and/or Telegram."""
    if discord_webhook:
        send_discord_notification(discord_webhook, message)
    if telegram_webhook:
        send_telegram_notification(telegram_webhook, message)

def send_discord_notification(webhook_url, message):
    """Send a Discord notification."""
    try:
        response = requests.post(webhook_url, json={"content": message})
        response.raise_for_status()
    except requests.RequestException as e:
        click.echo(f"Error sending Discord notification: {e}")

def send_telegram_notification(webhook_url, message):
    """Send a Telegram notification."""
    try:
        response = requests.post(webhook_url, json={"text": message})
        response.raise_for_status()
    except requests.RequestException as e:
        click.echo(f"Error sending Telegram notification: {e}")


def execute_monitoring(wallet, helius_key, discord_webhook, telegram_webhook, token_balances):
    wallet_name = wallet["name"]
    wallet_address = wallet["address"]
    last_processed_slot = wallet.get("last_processed_slot", None)

    while True:
        base_url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/transactions"
        params = {
            "api-key": helius_key,
            "type": "TRANSFER",
            "limit": 10,
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            transactions = response.json()

            # Process transactions
            if transactions:
                last_processed_slot = process_transactions(
                    wallet, transactions, discord_webhook, telegram_webhook, token_balances, last_processed_slot
                )

                # Save the latest processed slot
                wallet["last_processed_slot"] = last_processed_slot
            else:
                click.echo(f"No new transactions for {wallet_name} ({wallet_address}).")

            # Add a delay to avoid excessive API calls
            time.sleep(30)
        except requests.exceptions.RequestException as e:
            click.echo(f"Error fetching transactions for {wallet_name} - {wallet_address}: {e}")
            time.sleep(60)  # Retry after a delay


def process_transactions(wallet, transactions, discord_webhook, telegram_webhook, token_balances, last_processed_slot):
    wallet_address = wallet["address"]
    latest_slot = last_processed_slot

    for transaction in transactions:
        slot = transaction["slot"]

        # Skip transactions already processed
        if last_processed_slot and slot <= last_processed_slot:
            continue

        # Update latest slot to the highest encountered
        if not latest_slot or slot > latest_slot:
            latest_slot = slot

        # Process token transfers for buys and sells
        for token_transfer in transaction.get("tokenTransfers", []):
            if token_transfer["toUserAccount"] == wallet_address:
                # Buying a token
                token_mint = token_transfer["mint"]
                amount = token_transfer["tokenAmount"]

                message = (
                    f"Wallet {wallet['name']} ({wallet_address}) bought tokens:\n"
                    f"Token Mint: {token_mint}\n"
                    f"Amount: {amount}\n"
                    f"Transaction: {transaction['signature']}"
                )
                send_notifications(discord_webhook, telegram_webhook, message)

                # Update token balance
                token_balances[token_mint] = token_balances.get(token_mint, 0) + amount

            elif token_transfer["fromUserAccount"] == wallet_address:
                # Selling a token
                token_mint = token_transfer["mint"]
                amount = token_transfer["tokenAmount"]

                if token_balances.get(token_mint, 0) >= amount:
                    message = (
                        f"Wallet {wallet['name']} ({wallet_address}) sold tokens:\n"
                        f"Token Mint: {token_mint}\n"
                        f"Amount: {amount}\n"
                        f"Transaction: {transaction['signature']}"
                    )
                    send_notifications(discord_webhook, telegram_webhook, message)

                    # Update token balance
                    token_balances[token_mint] -= amount
                    if token_balances[token_mint] <= 0:
                        del token_balances[token_mint]

        # Process native transfers for SOL movements
        for native_transfer in transaction.get("nativeTransfers", []):
            if native_transfer["toUserAccount"] == wallet_address:
                # Received SOL
                amount = native_transfer["amount"]
                message = (
                    f"Wallet {wallet['name']} ({wallet_address}) received SOL:\n"
                    f"Amount: {amount} lamports\n"
                    f"Transaction: {transaction['signature']}"
                )
                send_notifications(discord_webhook, telegram_webhook, message)

            elif native_transfer["fromUserAccount"] == wallet_address:
                # Sent SOL
                amount = native_transfer["amount"]
                message = (
                    f"Wallet {wallet['name']} ({wallet_address}) sent SOL:\n"
                    f"Amount: {amount} lamports\n"
                    f"Transaction: {transaction['signature']}"
                )
                send_notifications(discord_webhook, telegram_webhook, message)

    return latest_slot  # Return the highest slot processed

def run_tasks_concurrently(wallets, helius_key, discord_webhook, telegram_webhook):
    """Run monitoring tasks concurrently for all wallets."""
    token_balances = {}  # Track token balances across wallets

    with ThreadPoolExecutor(max_workers=len(wallets)) as executor:
        futures = [
            executor.submit(execute_monitoring, wallet, helius_key, discord_webhook, telegram_webhook, token_balances)
            for wallet in wallets
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                click.echo(f"An error occurred: {e}")
