#!/usr/bin/env python3

def sanitize_data(s):
	"""Removes excess white-space from strings"""

	# If string only empty spaces return None
	if not s or s.isspace():
		return None

	# remove any white-space from beginning or end of the string
	s = s.strip()

	# remove double white-spaces or tabs if any
	s = re.sub(r'\s+', ' ', s)

	return s
