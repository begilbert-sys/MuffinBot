import logging


def set_file_level(filename, logger, level):
    file_formatter = logging.Formatter('%(name)s - %(levelname)s: %(message)s')
    fh = logging.FileHandler(filename, 'w')
    fh.setFormatter(file_formatter)
    fh.setLevel(level)
    logger.addHandler(fh)

def set_terminal_level(logger, level):
    terminal_formatter = logging.Formatter('%(message)s')
    sh = logging.StreamHandler()
    sh.setFormatter(terminal_formatter)
    sh.setLevel(level)
    logger.addHandler(sh)

def setup():
    collection_logger = logging.getLogger('collection')
    set_file_level('debug.log', collection_logger, logging.DEBUG)
    set_terminal_level(collection_logger, logging.INFO)

    discord_logger = logging.getLogger('discord')
    set_file_level('discord.log', discord_logger, logging.INFO)
    set_terminal_level(discord_logger, logging.INFO)