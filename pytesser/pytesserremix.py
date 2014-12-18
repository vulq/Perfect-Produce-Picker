"""OCR in Python using the Tesseract engine from Google
http://code.google.com/p/pytesser/
by Michael J.T. O'Kelly
V 0.0.1, 3/10/07"""

"""Edited by Joshua Korn to accomodate trained languages, whitelists, and single character analysis."""

import Image
import subprocess
import os

import util
import errors
curPath = os.path.dirname(os.path.abspath(__file__))
newPath = curPath + os.sep + "Tesseract-OCR" + os.sep + "tesseract"
tesseract_exe_name = newPath # Name of executable to be called at command line
scratch_image_name = "temp.bmp" # This file must be .bmp or other Tesseract-compatible format
scratch_text_name_root = "temp" # Leave out the .txt extension
cleanup_scratch_flag = True  # Temporary files cleaned up after OCR operation

def call_tesseract(input_filename, output_filename):
	"""Calls external tesseract.exe on input file (restrictions on types),
	outputting output_filename+'txt'"""
	args = [tesseract_exe_name, input_filename, output_filename]
	args.append("-l eng2+eng3+eng4+eng5+eng6+eng7+eng8")
	args.append("-psm")
	args.append(str(10))
	args.append("letters")
	proc = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
	retcode = proc.wait()
	if retcode!=0:
		errors.check_for_errors()

def image_to_string(im, cleanup = cleanup_scratch_flag):
	"""Converts im to file, applies tesseract, and fetches resulting text.
	If cleanup=True, delete scratch files after operation."""
	try:
		util.image_to_scratch(im, scratch_image_name)
		call_tesseract(scratch_image_name, scratch_text_name_root)
		text = util.retrieve_text(scratch_text_name_root)
	finally:
		if cleanup:
			util.perform_cleanup(scratch_image_name, scratch_text_name_root)
	return text

def image_file_to_string(filename, cleanup = cleanup_scratch_flag, graceful_errors=True):
	"""Applies tesseract to filename; or, if image is incompatible and graceful_errors=True,
	converts to compatible format and then applies tesseract.  Fetches resulting text.
	If cleanup=True, delete scratch files after operation."""
	try:
		try:
			call_tesseract(filename, scratch_text_name_root)
			text = util.retrieve_text(scratch_text_name_root)
		except errors.Tesser_General_Exception:
			if graceful_errors:
				im = Image.open(filename)
				text = image_to_string(im, cleanup)
			else:
				raise
	finally:
		if cleanup:
			util.perform_cleanup(scratch_image_name, scratch_text_name_root)
	return text