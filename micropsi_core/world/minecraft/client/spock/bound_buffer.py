class BufferUnderflowException(Exception):
	pass

class BoundBuffer:
	backup = b''
	def __init__(self, *args):
		self.buff = (args[0] if args else b'')
	
	def recv(self, bytes):
		if type(bytes) != int:
			pass #TODO Fix Bug. Therefore set Breakpoint here
		if len(self.buff) < bytes:
			raise BufferUnderflowException()
		o, self.buff = self.buff[:bytes], self.buff[bytes:]
		return o

	def append(self, bytes):
		self.buff += bytes
	
	def flush(self):
		out = self.buff
		self.buff = b''
		self.save()
		return out
	
	def save(self):
		self.backup = self.buff
	
	def revert(self):
		self.buff = self.backup

	def __len__(self):
		return self.buff.__len__()
	
	read = recv
	write = append