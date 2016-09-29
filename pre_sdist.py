# -*- coding: utf-8 -*-

"""
	This script is called only before running sdist commang on setup.py
	Only import Python's native modules here.
"""
from configparser import ConfigParser
import os


def reset_config():
	
	# Get path to config file
	config_path = os.path.expanduser('~/.lyricorc')

	# Load config.ini
	config = ConfigParser()
	config.read(config_path)

	# Force all settings to intended defaults
	config.set('actions', 'save_to_file', 'True')
	config.set('actions', 'save_to_tag', 'False')
	config.set('actions', 'overwrite', 'False')

	config.set('paths', 'lyrics_dir', 'None')

	config.set('sources', 'lyric_wikia', 'True')
	config.set('sources', 'lyrics_n_music', 'True')
	config.set('sources', 'musix_match', 'True')
	config.set('sources', 'lyricsmode', 'True')
	config.set('sources', 'az_lyrics', 'False')

	# save to config.ini
	with open(config_path, 'w') as configfile:
		config.write(configfile)
