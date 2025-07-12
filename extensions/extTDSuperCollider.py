from TDStoreTools import StorageManager
import TDFunctions as TDF
import platform, subprocess, os, threading

class extTDSuperCollider:
	"""
	Extension for launching a SuperCollider script from a relative project folder,
	with optional user-defined sclang path parameter on the component.
	"""
	# Default OS-based paths to sclang
	BINARY_MAP = {
		"Windows": r"C:\\Program Files\\SuperCollider\\sclang.exe",
		"Darwin":  "/Applications/SuperCollider.app/Contents/MacOS/sclang"
	}

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

		self.proc = None
		self.server_pid = None

		self.table = self.ownerComp.op('synthTable')

		# sclang path
		# Check for custom sclang path parameter
		user_path = self.ownerComp.par.Sclangpath.eval()
		if user_path:
			self.sclang_path = user_path
		else:
			os_name = platform.system()
			if os_name not in self.BINARY_MAP:
				raise RuntimeError(f"Unsupported OS: {os_name}")
			self.sclang_path = self.BINARY_MAP[os_name]


	def StartSuperCollider(self):
		"""
		Launches the SuperCollider file at:
		<project_folder>/supercollider/TDSuperCollider.scd
		"""
		scd_file = os.path.join(project.folder, 'supercollider', 'TDSuperCollider.scd')
		if not os.path.isfile(scd_file):
			raise FileNotFoundError(f"SuperCollider script not found: {scd_file}")

		# Launch sclang with the SC file
		proc = subprocess.Popen(
			[self.sclang_path, scd_file],
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True
		)

		# Stream console output back to TouchDesigner Textport
		def _stream():
			for line in proc.stdout:
				print('SuperCollider:', line.rstrip())
		threading.Thread(target=_stream, daemon=True).start()

		# Store process handle for later control if needed
		self.proc = proc
		return proc

	def StopSuperCollider(self):
		"""
		Stops the sclang process and the scsynth server if running.
		"""
		# kill sclang
		if self.proc and self.proc.poll() is None:
			try:
				self.proc.terminate()
				print('Terminated sclang PID:', self.proc.pid)
			except Exception as e:
				print('Error terminating sclang:', e)
		self.proc = None

		# kill scsynth server
		if self.server_pid:
			try:
				if platform.system() == 'Windows':
					subprocess.call(['taskkill', '/PID', str(self.server_pid), '/F'])
				else:
					os.kill(self.server_pid, signal.SIGTERM)
				print('Terminated scsynth PID:', self.server_pid)
			except Exception as e:
				print('Error terminating server:', e)
		self.server_pid = None
		return

	def SetLangPort(self, langPort):
		# Set the OSC out DAT port for language feedback
		self.ownerComp.op('oscout1').par.port = langPort
		print('langPort:', langPort)

	def ParseSynthMessage(self, row):
		"""
		row: e.g.
		['simpleSine', 'created', 'freq', '440', 'lpFreq', '8000', 'vol', '0.5']
		['simpleSine', 'updated', '1001', 'lpFreq', '1200']
		['simpleSine', 'killed', '1001']
		"""
		table = self.table

		# unpack common fields
		sType = row[0]
		evt   = row[1]
		sID   = int(row[2]) if evt in ('updated', 'killed') else None

		# decide where params start
		if evt == 'created':
			args = row[2:]
		else:
			args = row[3:]

		# helper: add column if missing
		def ensureCol(name):
			hdrs = table.row(0)
			if name not in hdrs:
				col = table.numCols
				table[0, col] = name
				for r in range(1, table.numRows):
					table[r, col] = ''

		# CREATED: build headers + new row
		if evt == 'created':
			# make sure id, type, status exist
			ensureCol('id')
			ensureCol('type')
			ensureCol('status')
			# for each param name
			for i in range(0, len(args), 2):
				ensureCol(args[i])

			# map param→value
			values = { args[i]: args[i+1] for i in range(0, len(args), 2) }

			# assemble row in header order
			rowData = []
			for h in table.row(0):
				if h == 'id':
					rowData.append(synthID)  # no sID yet: use newly assigned nodeID?
				elif h == 'type':
					rowData.append(sType)
				elif h == 'status':
					rowData.append('playing')
				else:
					rowData.append(values.get(h, ''))
			table.appendRow(rowData)

		# UPDATED: set single param
		elif evt == 'updated':
			param = args[0]
			value = args[1]
			ensureCol(param)
			# find the row for this ID
			for r in range(1, table.numRows):
				if int(table[r, table.row(0).index('id')]) == sID:
					c = table.row(0).index(param)
					table[r, c] = value
					break

		# KILLED: mark status
		elif evt == 'killed':
			ensureCol('status')
			for r in range(1, table.numRows):
				if int(table[r, table.row(0).index('id')]) == sID:
					c = table.row(0).index('status')
					table[r, c] = 'killed'
					break
