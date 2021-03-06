#!/usr/bin/env python3
import time
import sys
import os

from mutagen.id3 import USLT
from mutagen.asf import ASFUnicodeAttribute
from mutagen import MutagenError
from bs4 import BeautifulSoup

# Import all the sources modules
from lyrico_sources.lyric_wikia import donwload_from_lyric_wikia
from lyrico_sources.lyrics_n_music import donwload_from_lnm
from lyrico_sources.az_lyrics import donwload_from_az_lyrics
from lyrico_sources.musix_match import donwload_from_musix_match
from lyrico_sources.lyricsmode import donwload_from_lyricsmode

from song_helper import get_song_data, get_song_list
from audio_format_keys import FORMAT_KEYS

class Song():
	"""Container objects repersenting each song globbed from source_dir"""

	# holds count for songs for valid metadata
	valid_metadata_count = 0

	# Count for songs whose lyrics are successfully saved to file.
	lyrics_saved_to_file_count = 0

	# Count for songs whose lyrics are successfully saved to tag.
	lyrics_saved_to_tag_count = 0

	def __init__(self, path, Config):

		self.path = path

		# extract data from song
		data = get_song_data(path, Config)

		# Initialize instance variables from data extracted
		self.tag = data['tag']
		self.artist = data['artist']
		self.title = data['title']
		self.album = data['album']
		self.format = data['format']

		self.lyrics_file_name = data['lyrics_file_name']
		self.lyrics_file_path = data['lyrics_file_path']

		# If the required lyrics file is already present in LYRICS_DIR
		self.lyrics_file_present = data['lyrics_file_present']

		# If the required lyrics is already embedded in tag
		self.lyrics_tag_present = data['lyrics_tag_present']


		# Holds the downloaded lyrics
		self.lyrics = None

		# Final status to build log
		self.saved_to_tag = False
		self.saved_to_file = False
		self.source = None
		self.error = data['error']

		# As the songs are read from the files, update the class variable.
		# This is count of songs that have valid artist and title.
		if self.title and self.artist:
			Song.valid_metadata_count += 1

	def download_lyrics(self,Config):

		"""
			Only called when song has artist and title.
			Calls self.save_lyrics to save them.

		"""

		if not self.download_required(Config):
			print('\nSkipping', self.artist, '-', self.title)
			print('Lyrics already present.')
			return

		# At this point there is nothing in self.error
		print('\nDownloading:', self.artist, '-', self.title)

		# Use sources according to user settings
		if Config['sources']['lyric_wikia']:
			donwload_from_lyric_wikia(self)

		# Only try other sources if required

		if not self.lyrics and Config['sources']['lyrics_n_music']:
			donwload_from_lnm(self)

		if not self.lyrics and Config['sources']['musix_match']:
			donwload_from_musix_match(self)

		if not self.lyrics and Config['sources']['lyricsmode']:
			donwload_from_lyricsmode(self)

		if not self.lyrics and Config['sources']['az_lyrics']:
			donwload_from_az_lyrics(self)

		if not self.lyrics and self.stripable():
			#strip [] and () from title and try again
			self.strip_tags()
			self.download_lyrics(Config)

		self.save_lyrics(Config)

	def strip_tags(self):
		left = self.title.rfind("(")
		right = self.title.rfind(")")
		if left > -1 and right > -1:
			if right < len(self.title):
				self.title = self.title[:left -1] + self.title[right+1:]
			else:
				self.title = self.title[:left -1]

		left = self.title.rfind("[")
		right = self.title.rfind("]")
		if left > -1 and right -1:
			if right < len(self.title):
				self.title = self.title[:left -1] + self.title[right+1:]
			else:
				self.title = self.title[:left -1]

	def stripable(self):
		return ("(" in self.title or "[" in self.title)

	def save_lyrics(self, Config):

		"""
			Called by self.download_lyrics to save lyrics according to
			Config.save_to_file, Config.save_to_tag settings.

			Handles the case if lyrics is not found. Logs errors to console
			and Song object.

		"""
		
		if not self.lyrics:
			print('Failed:', self.error)
			return

		if self.lyrics and Config['actions']['save_to_file']:
			try:
				print(self.lyrics_file_path)
				with open(self.lyrics_file_path, 'w', encoding='utf-8') as f:
					f.write('Artist - ' + self.artist + '\n')
					f.write('Title - ' + self.title + '\n')

					album_str = 'Album - Unkown'
					if self.album:
						album_str = 'Album - ' + self.album			
					f.write(album_str)
					f.write('\n\n')

					f.write(self.lyrics)

				# update class variable
				Song.lyrics_saved_to_file_count += 1

				# update the Song instance flag
				self.saved_to_file = True

				print('Success: Lyrics saved to file.')

			except IOError as e:
				err_str = str(e)
				if e.errno == 22:
					err_str = 'Cannot save lyrics to file. Unable to create file with song metadata.'
				if e.errno == 13:
					err_str = 'Cannot save lyrics to file. The file is opened or in use.'
				if e.errno == 2:
					err_str = '"lyrics_dir" does not exist. Please set a "lyric_dir" which exists.'

				self.error = err_str
				print('Failed:', err_str)

		if self.lyrics and Config['actions']['save_to_tag']:
			lyrics_key = FORMAT_KEYS[self.format]['lyrics']
			try:
				if self.format == 'mp3':
					# encoding = 3 for UTF-8
					self.tag.add(USLT(encoding=1, lang = 'eng', desc = 'lyrics.wikia',
									text=self.lyrics))

				if self.format == 'm4a' or self.format == 'mp4':
					# lyrics_key = '\xa9lyr'
					
					if sys.version_info[0] < 3:
						lyrics_key = lyrics_key.encode('latin-1')
					self.tag[lyrics_key] = self.lyrics

				# Both flac and ogg/oga(Vorbis & FLAC), are being read/write as Vorbis Comments.
				# Vorbis Comments don't have a standard 'lyrics' tag. The 'LYRICS' tag is 
				# most common non-standard tag used for lyrics.
				if self.format == 'flac' or self.format == 'ogg' or self.format == 'oga':
					self.tag[lyrics_key] = self.lyrics

				if self.format == 'wma':
					# ASF Format uses ASFUnicodeAttribute objects instead of Python's Unicode
					self.tag[lyrics_key] = ASFUnicodeAttribute(self.lyrics)

				self.tag.save()
				self.saved_to_tag = True
				Song.lyrics_saved_to_tag_count += 1

				print('Success: Lyrics saved to tag.')

			except MutagenError:
				err_str = 'Cannot save lyrics to tag. Codec/Format not supported'
				self.error = err_str
				print('Failed:', err_str)
				
			except IOError as e:
				err_str = 'Cannot save lyrics to tag. The file is opened or in use.'
				self.error = err_str
				print('Failed:', err_str)

	def download_required(self, Config):
		"""
		Checks if a lyrics are required to be download.
		Uses Config.save_to_file, Config.save_to_tag and Config.overwrite settings
		and returns True when download is required.

		"""
		if Config.overwrite:
			# If user wants to overwite existing lyrics, always download
			# and save according to Config.save_to_file, Config.save_to_tag settings
			return True
		else:

			# Do we need to download lyrics and save to file
			file_required = False

			# Do we need to download lyrics and save to tag
			tag_required = False

			if Config['actions']['save_to_file'] and not self.lyrics_file_present:
				# if user wants to save to file and the file is not
				# present in the set LYRICS_DIR, the we need
				# to download it and save to the file.
				file_required = True

			if Config['actions']['save_to_tag'] and not self.lyrics_tag_present:
				# if user wants to save to tag and the tag does not
				# has lyrics field saved, then we need
				# to download it and save to the tag.
				tag_required = True

			# If either is required, we need to make the download request.
			# Data is then saved accordingly to the settings.
			return file_required or tag_required

	def get_log_string(self, Config):
		"""
		returns the log string of the song which is used in final log.

		"""
		template = '. \t{file}\t{tag}\t{source}\t\t{song}\t\t{error}\n'
		log = {}

		# file_status and tag each have 4 possible values
			# 'Saved' - File or tag was saved successfully
			# 'Failed' - Download or save failed. Show error.
			# 'Ignored' - Ignored according to Config.save_to_file, Config.save_to_tag setting by user.
			# 'Present' - Detected tag or file and skipped download skipped by lyrico as per Config.overwrite setting.

		if Config['actions']['save_to_file']:
			if not self.download_required(Config):
				file_status = 'Present'
			else:
				if self.saved_to_file:
					file_status = 'Saved'
				else:
					file_status = 'Failed'
		else:
			file_status = 'Ignored'

		if Config['actions']['save_to_tag']:
			if not self.download_required(Config):
				tag = 'Present'
			else:
				if self.saved_to_tag:
					tag = 'Saved'
				else:
					tag = 'Failed'
		else:
			tag = 'Ignored'
		
		# avoid exceptions raised for concatinating Unicode and None types
		if self.artist and self.title:
			log['song'] = self.artist + ' - ' + self.title
		else:
			log['song'] = self.path

		log['error'] = self.error

		log['file'] = file_status
		log['tag'] = tag
		log['source'] = self.source

		return template.format(**log)

	@staticmethod
	def log_results(song_list, Config):
		pass
