import click

def main_logic():
    import soltracker
    soltracker.menu()


@click.command()
def start():
    main_logic()

if __name__ == "__main__":
    start()
