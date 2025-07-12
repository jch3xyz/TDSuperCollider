from TDStoreTools import StorageManager
import TDFunctions as TDF
import platform, subprocess, os, threading, re, signal, webbrowser

class extTDSuperCollider:
	"""
	Extension for launching a SuperCollider script from a relative project folder,
	with optional user-defined sclang path parameter on the component.
	"""
	# Default OS-based paths to sclang
	BINARY_MAP = {
		"Windows": r"C:\\Program Files\\SuperCollider-3.13.0\\sclang.exe",
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
	
	def DownloadSuperCollider(self):
		webbrowser.open('https://supercollider.github.io/')
		return

	def StartSuperCollider(self):
		"""
		Launch TDSuperCollider.scd from <project_folder>/supercollider/
		Prepends sclang folder to PATH on Windows so scsynth is found.
		"""
		base_folder = os.path.join(project.folder, 'supercollider')
		scd_file = os.path.join(base_folder, 'TDSuperCollider.scd')
		if not os.path.isfile(scd_file):
			raise FileNotFoundError(f"Script not found: {scd_file}")

		# Build environment with scsynth on PATH for Windows
		env = os.environ.copy()
		if platform.system() == 'Windows':
			sc_dir = os.path.dirname(self.sclang_path)
			env['PATH'] = sc_dir + os.pathsep + env.get('PATH', '')

		# Stop existing instance
		if self.proc and self.proc.poll() is None:
			self.StopSuperCollider()

		# Launch script with correct cwd
		proc = subprocess.Popen(
			[self.sclang_path, scd_file],
			cwd=base_folder,
			env=env,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True
		)
		self.proc = proc

		# Stream output and capture server PID
		def _stream():
			for line in proc.stdout:
				print('SuperCollider:', line.rstrip())
				m = re.search(r'pid:\s*(\d+)', line)
				if m:
					try:
						self.server_pid = int(m.group(1))
						print(f'sc server PID: {self.server_pid}')
					except ValueError:
						pass
		threading.Thread(target=_stream, daemon=True).start()
		return proc

	def StopSuperCollider(self):
		"""
		Terminate sclang and scsynth processes.
		"""
		if self.proc:
			if self.proc.poll() is None:
				try:
					self.proc.terminate()
					print('Terminated sclang PID:', self.proc.pid)
				except Exception as e:
					print('Error terminating sclang:', e)
			self.proc = None

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
		row format:
		[sType (str), sID (int), event (str), [paramName, paramValue, ...]]
		Examples:
		['simpleSine', 1001, 'created', 'freq', 330, 'lpFreq', 5000, 'vol', 0.5]
		['simpleSine', 1001, 'updated', 'lpFreq', 1200]
		['simpleSine', 1001, 'killed']
		"""
		table = self.table

		 # 1) Unwrap any incoming td.Cell → plain Python
		clean = []
		for v in row:
			if hasattr(v, 'val'):
				clean.append(v.val)
			else:
				clean.append(v)
		sType, sID, evt, *params = clean
		sID = int(sID)

		print(f"ParseSynthMessage received: {row}")
		print(f"Type: {sType}, ID: {sID}, Event: {evt}, Params: {params}")

		 # Helpers to get header names and add a column
		def header_vals():
			return [c.val for c in table.row(0)]

		def ensureCol(name):
			h = header_vals()
			if name not in h:
				# build a full column list: header + blanks
				col = [name] + [''] * (table.numRows - 1)
				table.appendCol(col)

		# CREATE: add any missing cols, then append a new row
		if evt == 'created':
			# always have these three
			for col in ('id', 'type', 'status'):
				ensureCol(col)
			# ensure each param name exists
			for i in range(0, len(params), 2):
				ensureCol(str(params[i]))
			# build a map of name→value
			vals = { str(params[i]) : params[i+1] for i in range(0, len(params), 2) }
			# assemble in header order
			newRow = []
			for h in header_vals():
				if h == 'id':
					newRow.append(sID)
				elif h == 'type':
					newRow.append(sType)
				elif h == 'status':
					newRow.append('playing')
				else:
					newRow.append(vals.get(h, ''))
			table.appendRow(newRow)

		# UPDATE: find the row for this sID and set one cell
		elif evt == 'updated' and len(params) >= 2:
			name, val = str(params[0]), params[1]
			ensureCol(name)
			h = header_vals()
			id_idx    = h.index('id')
			name_idx  = h.index(name)
			# iterate the existing rows (skipping header row)
			for rowCells in table.rows()[1:]:
				if int(rowCells[id_idx].val) == sID:
					rowCells[name_idx].val = val
					break

		# KILL: mark status="killed" on the matching row
		elif evt == 'killed':
			ensureCol('status')
			h = header_vals()
			id_idx     = h.index('id')
			status_idx = h.index('status')
			for rowCells in table.rows()[1:]:
				if int(rowCells[id_idx].val) == sID:
					rowCells[status_idx].val = 'killed'
					break

