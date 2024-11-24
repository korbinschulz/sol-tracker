import click
import inquirer
import json
import os
import re
from datetime import datetime
import time
from task_executor import run_tasks_concurrently

WALLETS_FILE = 'wallets.json'
INFO_FILE = 'info.json'

# Load existing data
def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

# Save data to file
def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)


# Main CLI
@click.group()
def cli():
    pass

# Main Menu
@cli.command()
def menu():
    while True:
        click.clear()
        click.echo(click.style('SolTracker', bold=True, fg='cyan', bg='black'))
        questions = [
            inquirer.List('choice',
                          message="Choose an option",
                          choices=['1) Start Tracking', '2) Manage Wallets', '3) Info', '4) Exit'],
                          carousel=True)
        ]
        answers = inquirer.prompt(questions)

        if answers['choice'].startswith('1'):
            start_tracking()
        elif answers['choice'].startswith('2'):
            manage_wallets()
        elif answers['choice'].startswith('3'):
            manage_info()
        elif answers['choice'].startswith('4'):
            break

def manage_wallets():
    wallets = load_data(WALLETS_FILE, [])
    while True:
        click.clear()
        click.echo(click.style('SolTracker - Manage Wallets', bold=True, fg='cyan', bg='black'))
        
        for idx, wallet in enumerate(wallets):
            click.echo(f"{idx+1}) {wallet['name']} - {wallet['address']}")
        
        questions = [
            inquirer.List('wallet_choice',
                          message="Choose an option",
                          choices=['1) Add Wallet', '2) Remove Wallet', '3) Back'],
                            carousel=True)
        ]
        answers = inquirer.prompt(questions)

        if answers['wallet_choice'].startswith('1'):
            add_wallet()
        elif answers['wallet_choice'].startswith('2'):
            delete_wallet()
        elif answers['wallet_choice'].startswith('3'):
            break


def add_wallet():
    questions = [
        inquirer.Text('name', message="Enter wallet name"),
        inquirer.Text('address', message="Enter wallet address"),
    ]
    answers = inquirer.prompt(questions)

    wallets = load_data(WALLETS_FILE, [])
    wallets.extend([answers])
    save_data(WALLETS_FILE, wallets)
    click.echo("Wallet added successfully")

def delete_wallet():
    while True:
        wallets = load_data(WALLETS_FILE, [])
        wallet_choices = [f'{idx+1}) {wallet["name"]} - {wallet["address"]}' for idx, wallet in enumerate(wallets)]

        questions = [
            inquirer.List('wallet',
                          message="Choose a wallet to delete",
                          choices=wallet_choices + ['Back'],
                          carousel=True)
        ]

        answers = inquirer.prompt(questions)
        if answers['wallet'] == 'Back':
            break
        if answers['wallet'] != 'Back':
            wallet_index = int(answers['wallet'].split(')')[0]) - 1
            wallets.pop(wallet_index)
            save_data(WALLETS_FILE, wallets)
            click.echo("Wallet deleted successfully")

def set_discord_webhook(info):
    discord_webhook = input("Enter your Discord Webhook URL: ").strip()
    sanitized_webhook = re.sub(r'\s+', '', discord_webhook)
    info['discord_webhook'] = sanitized_webhook
    save_data(INFO_FILE, info)
    click.echo('Discord Webhook URL set!')   

def set_telegram_webhook(info):
    telegram_webhook = input("Enter your Telegram Webhook URL: ").strip()
    sanitized_webhook = re.sub(r'\s+', '', telegram_webhook)
    info['telegram_webhook'] = sanitized_webhook
    save_data(INFO_FILE, info)
    click.echo('Telegram Webhook URL set!') 

def set_helius_api_key(info):
    helius_api_key = input("Enter your Helius API Key: ").strip()
    sanitized_api_key = re.sub(r'\s+', '', helius_api_key)
    info['helius_api_key'] = sanitized_api_key
    save_data(INFO_FILE, info)
    click.echo('Helius API Key set!')

def manage_info():
    info = load_data(INFO_FILE, {})
    while True:
        click.clear()
        click.echo(click.style('SolTracker - Manage Info', bold=True, fg='cyan', bg='black'))
        click.echo(f'Helius API Key: {info.get("helius_api_key", "Not set")}')
        click.echo(f'Discord Webhook: {info.get("discord_webhook", "Not set")}')
        click.echo(f'Telegram Webhook: {info.get("telegram_webhook", "Not set")}')

        questions = [
            inquirer.List('info_choice',
                          message="Choose an option",
                          choices=['1) Set Helius API Key', '2) Set Discord Webhook', '3) Set Telegram Webhook', '4) Back'],
                          carousel=True)
        ]
        answers = inquirer.prompt(questions)

        if answers['info_choice'].startswith('1'):
            set_helius_api_key(info)
        elif answers['info_choice'].startswith('2'):
            set_discord_webhook(info)
        elif answers['info_choice'].startswith('3'):
            set_telegram_webhook(info)
        elif answers['info_choice'].startswith('4'):
            break

def start_tracking():
    wallets = load_data(WALLETS_FILE, [])
    info = load_data(INFO_FILE, {})
    
    if not wallets:
        click.echo("No wallets found. Please add a wallet first.")
        return
    if not info.get('helius_api_key'):
        click.echo("Helius API Key not set. Please set it first.")
        return
    #if no discord webhook or telegram webhook, ask user to set either one
    if not info.get('discord_webhook') and not info.get('telegram_webhook'):
        click.echo("No Discord or Telegram webhook set. Please set either one.")
        return
    
    try:
        run_tasks_concurrently(wallets, info['helius_api_key'], info.get('discord_webhook'), info.get('telegram_webhook'))
    except Exception as e:
        click.echo(f"Error starting tracking: {e}")
    
    input("Press Enter to continue...")

        


if __name__ == '__main__':
    cli()
