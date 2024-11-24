import requests
import subprocess
import platform
import click
import json
import os

def main_logic():
    import soltracker
    soltracker.menu()


@click.command()
def start():
    main_logic()

if __name__ == "__main__":
    start()
