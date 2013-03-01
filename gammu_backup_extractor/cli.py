#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

from __future__ import print_function

import gammu
import argparse
import pprint
import re
import os
import errno
import sys


_MINIMUM_GAMMU_VERSION = '1.32.0'

_SOURCE_FOR_MEMORY_TYPE = {
	'SM': 'SIM',
	'ME': 'phone',
}

_CHAR_SUBST_MAP = {
	u'ä': 'ae',
	u'Ä': 'Ae',
	u'ö': 'oe',
	u'Ö': 'Oe',
	u'ü': 'ue',
	u'Ü': 'Ue',
	u'ß': 'ss',
}

_VALID_FILE_NAME_CHAR_REGEX = re.compile('[^A-Z0-9a-z]', flags=re.IGNORECASE)

_VERSION_TYPE_FOR_INDEX = (
	'Gammu C runtime version',
	'python-gammu version',
	'Gammu C build-time version',
)


def find_data_fo_type(data_type, list_of_records):
	for record in list_of_records:
		if record['Type'] == data_type:
			return record['Value']
	return None


def get_full_name(list_of_records):
	last_name = find_data_fo_type('Text_LastName', list_of_records)
	first_name = find_data_fo_type('Text_FirstName', list_of_records)
	formal_name = find_data_fo_type('Text_FormalName', list_of_records)
	plain_name = find_data_fo_type('Text_Name', list_of_records)

	if first_name and last_name:
		full_name = '%s %s' % (first_name, last_name)
	elif formal_name:
		full_name = formal_name
	elif plain_name:
		full_name = plain_name
	elif last_name:
		full_name = last_name
	elif last_name:
		full_name = first_name
	else:
		full_name = None

	return full_name


def sanitize_filename(full_name):
	l = []
	for c in full_name:
		l.append(_CHAR_SUBST_MAP.get(c, c))
	return re.sub(_VALID_FILE_NAME_CHAR_REGEX, '_', ''.join(l))


def require_recent_gammu():
	fatal = False
	split_minimum_gammu_version = _MINIMUM_GAMMU_VERSION.split('.')

	for version_type_index, version in enumerate(gammu.Version()[:3]):
		if version.split('.') < split_minimum_gammu_version:
			print('%s must be %s or later, version %s found.' \
					% (_VERSION_TYPE_FOR_INDEX[version_type_index], _MINIMUM_GAMMU_VERSION, version),
					file=sys.stderr)
			fatal = True
	if fatal:
		print('\nExiting.', file=sys.stderr)
		sys.exit(1)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(version='2013.03.01')
	parser.add_argument('input_file', metavar='SOURCE.backup', help='Gammu backup file (*.backup) to extract from')
	parser.add_argument('--extract-vcards', dest='output_dir', required=True, metavar='FOLDER', help='Folder to write vCard files (*.vcf) to')
	options = parser.parse_args()

	require_recent_gammu()

	try:
		os.makedirs(options.output_dir, 0700)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise e

	backup = gammu.ReadBackup(options.input_file)
	for data_set_key in ('PhonePhonebook', 'SIMPhonebook'):
		for e in backup[data_set_key]:
			full_name = get_full_name(e['Entries'])
			if not full_name:
				print('Skipping entry:')
				pprint.pprint(e, indent=4)
				continue

			source = _SOURCE_FOR_MEMORY_TYPE.get(e['MemoryType'], 'unknown source')
			base_name = '%s.vcf' % sanitize_filename('%s  %s' % (full_name, source))
			vcard_file_name = os.path.join(options.output_dir, base_name)

			print('Writing file "%s"...' % vcard_file_name)

			vcard_content = gammu.EncodeVCARD(e)
			f = open(vcard_file_name, 'w')
			f.write(vcard_content)
			f.close()
