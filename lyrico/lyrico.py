# -*- coding: utf-8 -*-

import os

import platform

import argparse
import configparser

from song import Song
from song_helper import get_song_list

# testpypi 0.6.0
__version__ = "0.6.0"

Config = configparser.ConfigParser()
Config.read(os.path.expanduser('~/.lyricorc'))
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="directory where lyrico will search for mp3 files")
parser.add_argument("--overwrite", help="always download and overwrite existing lyrics")
args = parser.parse_args()




def main():
	# User wants to download lyrics.
	Config.overwrite = args.overwrite
	song_list = [Song(song_path, Config) for song_path in get_song_list(args.directory,Config)]
	print(len(song_list), 'songs detected.')
	print('Metadata extracted for', (str(Song.valid_metadata_count) + '/' + str(len(song_list))), 'songs.')
	for song in song_list:
		# Only download lyrics if 'title' and 'artist' is present
		# Error str is already present in song.error
		if song.artist and song.title:
			song.download_lyrics(Config)

		# Show immidiate log in console
		else:
			# If title was present, use that
			if song.title:
				print(song.title, 'was ignored.', song.error)
			# else use audio file path
			else:
				print(song.path, 'was ignored.', song.error)


	print('\nBuilding log...')
	Song.log_results(song_list, Config)
	print('FINISHED')

