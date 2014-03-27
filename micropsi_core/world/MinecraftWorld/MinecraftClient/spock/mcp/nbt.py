"""
Handle the NBT (Named Binary Tag) data format
"""

import os, io, zlib, gzip

from struct import Struct, error as StructError
from collections import MutableMapping, MutableSequence, Sequence
from micropsi_core.world.MinecraftWorld.MinecraftClient.spock.bound_buffer import BoundBuffer
#from utils import ByteToHex

try:
	unicode
	basestring
except NameError:
	unicode = str  # compatibility for Python 3
	basestring = str  # compatibility for Python 3

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11

class MalformedFileError(Exception):
	"""Exception raised on parse error."""
	pass

class TAG(object):
	"""TAG, a variable with an intrinsic name."""
	id = None

	def __init__(self, value=None, name=None):
		self.name = name
		self.value = value

	#Parsers and Generators
	def _parse_buffer(self, buffer):
		raise NotImplementedError(self.__class__.__name__)

	def _render_buffer(self, buffer):
		raise NotImplementedError(self.__class__.__name__)

	#Printing and Formatting of tree
	def tag_info(self):
		"""Return Unicode string with class, name and unnested value."""
		return self.__class__.__name__ + \
				('(%r)' % self.name if self.name else "") + \
				": " + self.valuestr()
	def valuestr(self):
		"""Return Unicode string of unnested value. For iterators, this returns a summary."""
		return unicode(self.value)

	def pretty_tree(self, indent=0):
		"""Return formated Unicode string of self, where iterable items are recursively listed in detail."""
		return ("\t"*indent) + self.tag_info()

	# Python 2 compatibility; Python 3 uses __str__ instead.
	def __unicode__(self):
		"""Return a unicode string with the result in human readable format. Unlike valuestr(), the result is recursive for iterators till at least one level deep."""
		return unicode(self.value)

	def __str__(self):
		"""Return a string (ascii formated for Python 2, unicode for Python 3) with the result in human readable format. Unlike valuestr(), the result is recursive for iterators till at least one level deep."""
		return str(self.value)
	# Unlike regular iterators, __repr__() is not recursive.
	# Use pretty_tree for recursive results.
	# iterators should use __repr__ or tag_info for each item, like regular iterators
	def __repr__(self):
		"""Return a string (ascii formated for Python 2, unicode for Python 3) describing the class, name and id for debugging purposes."""
		return "<%s(%r) at 0x%x>" % (self.__class__.__name__,self.name,id(self))

class _TAG_Numeric(TAG):
	"""_TAG_Numeric, comparable to int with an intrinsic name"""
	def __init__(self, value=None, name=None, buffer=None):
		super(_TAG_Numeric, self).__init__(value, name)
		if buffer:
			self._parse_buffer(buffer)

	#Parsers and Generators
	def _parse_buffer(self, buffer):
		# Note: buffer.read() may raise an IOError, for example if buffer is a corrupt gzip.GzipFile
		self.value = self.fmt.unpack(buffer.read(self.fmt.size))[0]

	def _render_buffer(self, buffer):
		buffer.write(self.fmt.pack(self.value))

#== Value Tags ==#
class TAG_Byte(_TAG_Numeric):
	"""Represent a single tag storing 1 byte."""
	id = TAG_BYTE
	fmt = Struct(">b")

class TAG_Short(_TAG_Numeric):
	"""Represent a single tag storing 1 short."""
	id = TAG_SHORT
	fmt = Struct(">h")

class TAG_Int(_TAG_Numeric):
	"""Represent a single tag storing 1 int."""
	id = TAG_INT
	fmt = Struct(">i")
	"""Struct(">i"), 32-bits integer, big-endian"""

class TAG_Long(_TAG_Numeric):
	"""Represent a single tag storing 1 long."""
	id = TAG_LONG
	fmt = Struct(">q")

class TAG_Float(_TAG_Numeric):
	"""Represent a single tag storing 1 IEEE-754 floating point number."""
	id = TAG_FLOAT
	fmt = Struct(">f")

class TAG_Double(_TAG_Numeric):
	"""Represent a single tag storing 1 IEEE-754 double precision floating point number."""
	id = TAG_DOUBLE
	fmt = Struct(">d")

class TAG_Byte_Array(TAG, MutableSequence):
	"""
	TAG_Byte_Array, comparable to a collections.UserList with
	an intrinsic name whose values must be bytes
	"""
	id = TAG_BYTE_ARRAY
	def __init__(self, name=None, buffer=None):
		super(TAG_Byte_Array, self).__init__(name=name)
		if buffer:
			self._parse_buffer(buffer)

	#Parsers and Generators
	def _parse_buffer(self, buffer):
		length = TAG_Int(buffer=buffer)
		self.value = bytearray(buffer.read(length.value))

	def _render_buffer(self, buffer):
		length = TAG_Int(len(self.value))
		length._render_buffer(buffer)
		buffer.write(bytes(self.value))

	# Mixin methods
	def __len__(self):
		return len(self.value)

	def __iter__(self):
		return iter(self.value)

	def __contains__(self, item):
		return item in self.value

	def __getitem__(self, key):
		return self.value[key]

	def __setitem__(self, key, value):
		# TODO: check type of value
		self.value[key] = value

	def __delitem__(self, key):
		del(self.value[key])

	def insert(self, key, value):
		# TODO: check type of value, or is this done by self.value already?
		self.value.insert(key, value)

	#Printing and Formatting of tree
	def valuestr(self):
		return "[%i byte(s)]" % len(self.value)

	def __unicode__(self):
		return '['+",".join([unicode(x) for x in self.value])+']'
	def __str__(self):
		return '['+",".join([str(x) for x in self.value])+']'

class TAG_Int_Array(TAG, MutableSequence):
	"""
	TAG_Int_Array, comparable to a collections.UserList with
	an intrinsic name whose values must be integers
	"""
	id = TAG_INT_ARRAY
	def __init__(self, name=None, buffer=None):
		super(TAG_Int_Array, self).__init__(name=name)
		if buffer:
			self._parse_buffer(buffer)

	def update_fmt(self, length):
		""" Adjust struct format description to length given """
		self.fmt = Struct(">" + str(length) + "i")

	#Parsers and Generators
	def _parse_buffer(self, buffer):
		length = TAG_Int(buffer=buffer).value
		self.update_fmt(length)
		self.value = list(self.fmt.unpack(buffer.read(self.fmt.size)))

	def _render_buffer(self, buffer):
		length = len(self.value)
		self.update_fmt(length)
		TAG_Int(length)._render_buffer(buffer)
		buffer.write(self.fmt.pack(*self.value))

	# Mixin methods
	def __len__(self):
		return len(self.value)

	def __iter__(self):
		return iter(self.value)

	def __contains__(self, item):
		return item in self.value

	def __getitem__(self, key):
		return self.value[key]

	def __setitem__(self, key, value):
		self.value[key] = value

	def __delitem__(self, key, value):
		del(self.value[key])

	def insert(self, key, value):
		self.value.insert(key, value)

	#Printing and Formatting of tree
	def valuestr(self):
		return "[%i int(s)]" % len(self.value)


class TAG_String(TAG, Sequence):
	"""
	TAG_String, comparable to a collections.UserString with an
	intrinsic name
	"""
	id = TAG_STRING
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_String, self).__init__(value, name)
		if buffer:
			self._parse_buffer(buffer)

	#Parsers and Generators
	def _parse_buffer(self, buffer):
		length = TAG_Short(buffer=buffer)
		read = buffer.read(length.value)
		if len(read) != length.value:
			raise StructError()
		self.value = read.decode("utf-8")

	def _render_buffer(self, buffer):
		save_val = self.value.encode("utf-8")
		length = TAG_Short(len(save_val))
		length._render_buffer(buffer)
		buffer.write(save_val)

	# Mixin methods
	def __len__(self):
		return len(self.value)

	def __iter__(self):
		return iter(self.value)

	def __contains__(self, item):
		return item in self.value

	def __getitem__(self, key):
		return self.value[key]

	#Printing and Formatting of tree
	def __repr__(self):
		return self.value

#== Collection Tags ==#
class TAG_List(TAG, MutableSequence):
	"""
	TAG_List, comparable to a collections.UserList with an intrinsic name
	"""
	id = TAG_LIST
	def __init__(self, type=None, value=None, name=None, buffer=None):
		super(TAG_List, self).__init__(value, name)
		if type:
			self.tagID = type.id
		else: self.tagID = None
		self.tags = []
		if buffer:
			self._parse_buffer(buffer)
		if not self.tagID:
			raise ValueError("No type specified for list")

	#Parsers and Generators
	def _parse_buffer(self, buffer):
		self.tagID = TAG_Byte(buffer=buffer).value
		self.tags = []
		length = TAG_Int(buffer=buffer)
		for x in range(length.value):
			self.tags.append(TAGLIST[self.tagID](buffer=buffer))

	def _render_buffer(self, buffer):
		TAG_Byte(self.tagID)._render_buffer(buffer)
		length = TAG_Int(len(self.tags))
		length._render_buffer(buffer)
		for i, tag in enumerate(self.tags):
			if tag.id != self.tagID:
				raise ValueError("List element %d(%s) has type %d != container type %d" %
						 (i, tag, tag.id, self.tagID))
			tag._render_buffer(buffer)

	# Mixin methods
	def __len__(self):
		return len(self.tags)

	def __iter__(self):
		return iter(self.tags)

	def __contains__(self, item):
		return item in self.tags

	def __getitem__(self, key):
		return self.tags[key]

	def __setitem__(self, key, value):
		self.tags[key] = value

	def __delitem__(self, key):
		del(self.tags[key])

	def insert(self, key, value):
		self.tags.insert(key, value)

	#Printing and Formatting of tree
	def __repr__(self):
		return "%i entries of type %s" % (len(self.tags), TAGLIST[self.tagID].__name__)

	#Printing and Formatting of tree
	def valuestr(self):
		return "[%i %s(s)]" % (len(self.tags), TAGLIST[self.tagID].__name__)
	def __unicode__(self):
		return "["+", ".join([tag.tag_info() for tag in self.tags])+"]"
	def __str__(self):
		return "["+", ".join([tag.tag_info() for tag in self.tags])+"]"

	def pretty_tree(self, indent=0):
		output = [super(TAG_List, self).pretty_tree(indent)]
		if len(self.tags):
			output.append(("\t"*indent) + "{")
			output.extend([tag.pretty_tree(indent + 1) for tag in self.tags])
			output.append(("\t"*indent) + "}")
		return '\n'.join(output)

class TAG_Compound(TAG, MutableMapping):
	"""
	TAG_Compound, comparable to a collections.OrderedDict with an
	intrinsic name
	"""
	id = TAG_COMPOUND
	def __init__(self, buffer=None):
		super(TAG_Compound, self).__init__()
		self.tags = []
		self.name = ""
		if buffer:
			self._parse_buffer(buffer)

	#Parsers and Generators
	def _parse_buffer(self, buffer):
		while True:
			type = TAG_Byte(buffer=buffer)
			if type.value == TAG_END:
				#print("found tag_end")
				break
			else:
				name = TAG_String(buffer=buffer).value
				try:
					tag = TAGLIST[type.value](buffer=buffer)
					tag.name = name
					self.tags.append(tag)
				except KeyError:
					raise ValueError("Unrecognised tag type")

	def _render_buffer(self, buffer):
		for tag in self.tags:
			TAG_Byte(tag.id)._render_buffer(buffer)
			TAG_String(tag.name)._render_buffer(buffer)
			tag._render_buffer(buffer)
		buffer.write(b'\x00') #write TAG_END

	# Mixin methods
	def __len__(self):
		return len(self.tags)

	def __iter__(self):
		for key in self.tags:
			yield key.name

	def __contains__(self, key):
		if isinstance(key, int):
			return key <= len(self.tags)
		elif isinstance(key, basestring):
			for tag in self.tags:
				if tag.name == key:
					return True
			return False
		elif isinstance(key, TAG):
			return key in self.tags
		return False

	def __getitem__(self, key):
		if isinstance(key, int):
			return self.tags[key]
		elif isinstance(key, basestring):
			for tag in self.tags:
				if tag.name == key:
					return tag
			else:
				raise KeyError("Tag %s does not exist" % key)
		else:
			raise TypeError("key needs to be either name of tag, or index of tag, not a %s" % type(key).__name__)

	def __setitem__(self, key, value):
		if isinstance(key, int):
			# Just try it. The proper error will be raised if it doesn't work.
			self.tags[key] = value
		elif isinstance(key, basestring):
			value.name = key
			for i, tag in enumerate(self.tags):
				if tag.name == key:
					self.tags[i] = value
					return
			self.tags.append(value)

	def __delitem__(self, key):
		if isinstance(key, int):
			self.tags = self.tags[:key] + self.tags[key:]
		elif isinstance(key, basestring):
			for i, tag in enumerate(self.tags):
				if tag.name == key:
					self.tags = self.tags[:i] + self.tags[i:]
					return
			raise KeyError("A tag with this name does not exist")
		else:
			raise ValueError("key needs to be either name of tag, or index of tag")

	def keys(self):
		return [tag.name for tag in self.tags]

	def iteritems(self):
		for tag in self.tags:
			yield (tag.name, tag)

	#Printing and Formatting of tree
	def __unicode__(self):
		return "{"+", ".join([tag.tag_info() for tag in self.tags])+"}"
	def __str__(self):
		return "{"+", ".join([tag.tag_info() for tag in self.tags])+"}"

	def valuestr(self):
		return '{%i Entries}' % len(self.tags)

	def pretty_tree(self, indent=0):
		output = [super(TAG_Compound, self).pretty_tree(indent)]
		if len(self.tags):
			output.append(("\t"*indent) + "{")
			output.extend([tag.pretty_tree(indent + 1) for tag in self.tags])
			output.append(("\t"*indent) + "}")
		return '\n'.join(output)

TAGLIST = {TAG_BYTE:TAG_Byte, TAG_SHORT:TAG_Short, TAG_INT:TAG_Int, TAG_LONG:TAG_Long, TAG_FLOAT:TAG_Float, TAG_DOUBLE:TAG_Double, TAG_BYTE_ARRAY:TAG_Byte_Array, TAG_STRING:TAG_String, TAG_LIST:TAG_List, TAG_COMPOUND:TAG_Compound, TAG_INT_ARRAY:TAG_Int_Array}

#Magic to make zlib work with gzip headers
wbits_length = 16+zlib.MAX_WBITS

#Hacky function to decode NBT data
def decode_nbt(data, compressed = True):
	if compressed:
		bbuff = BoundBuffer(zlib.decompress(data, wbits_length))
	else:
		bbuff = BoundBuffer(data)
	type = TAG_Byte(buffer = bbuff)
	name = TAG_String(buffer = bbuff).value
	tag = TAG_Compound(buffer = bbuff)
	tag.name = name
	return tag

#Eventually we should offer the option to render to a string
#That would make these functions 50% less hacky
def encode_nbt(data, compressed = True):
	bbuff = BoundBuffer()
	TAG_Byte(data.id)._render_buffer(bbuff)
	TAG_String(data.name)._render_buffer(bbuff)
	data._render_buffer(bbuff)
	if compressed:
		#Forced to use gzip to get the correct headers
		#Which means we have to hack around file objects
		gzipstring = io.StringIO()
		gzipfile = gzip.GzipFile(fileobj = gzipstring, mode = 'wb')
		gzipfile.write(bbuff.flush())
		gzipfile.close()
		return gzipstring.getvalue()
	else:
		return bbuff.flush()
