#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Python
import inspect
import os

#=======================================================================================
# Library
#=======================================================================================

class missingArgumentError(Exception): pass

def dprint(*args):
	
	#=============================
	"""Print a debugging message with automagically added context information."""
	#=============================

	parentStackContext = inspect.stack()[1]
	contextLocals = parentStackContext[0].f_locals
	className = ""
	
	if len(args) == 0:
		raise missingArgumentError("dprint needs at least 1 argument, 0 were given.")
	elif len(args) == 1:
		message = args[0]
	else:
		message = " ".join(args)
	
	if "self" in contextLocals.keys():
		className = "{name}.".format(\
			name=contextLocals["self"].__class__.__name__)
		
	print("[DEBUG:{fileName}:{line}:{className}{functionName}] {message}"\
		.format(\
			fileName = parentStackContext.filename.rpartition(os.sep)[2],\
			message = message,\
			line = parentStackContext.lineno,\
			className = className,\
			functionName=parentStackContext.function) )