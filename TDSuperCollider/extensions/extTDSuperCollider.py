from TDStoreTools import StorageManager
import TDFunctions as TDF
import platform, subprocess, os, threading, re, signal, webbrowser

class extTDSuperCollider:
	"""
	Extension for TDSuperCollider
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
		Launch TDSuperCollider.scd from <project_folder>/supercollider/
		Prepends sclang folder to PATH on Windows so scsynth is found.
		"""
		parent.TDSuperCollider.ClearSynthDefs()

		base_folder = os.path.join(project.folder, 'TDSuperCollider/supercollider')
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
				if 'pid' in line:
					print('Line with pid detected:', line)
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
			#print('self.proc:', self.proc)
			#print('self.proc.poll():', self.proc.poll())
			if self.proc.poll() is None:
				try:
					self.proc.terminate()
					self.proc.wait(timeout=2)
					print('Terminated sclang PID:', self.proc.pid)
				except subprocess.TimeoutExpired:
					print('Terminate timeout, using kill()')
					self.proc.kill()
				except Exception as e:
					print('Error terminating sclang:', e)
			self.proc = None
		else:
			print('No sclang proc to terminate')

		if self.server_pid:
			try:
				if platform.system() == 'Windows':
					ret = subprocess.call(['taskkill', '/PID', str(self.server_pid), '/T', '/F'])
					print('taskkill return code:', ret)
				else:
					os.kill(self.server_pid, signal.SIGTERM)
					print('Terminated scsynth PID:', self.server_pid)
			except Exception as e:
				print('Error terminating server:', e)
			self.server_pid = None
		else:
			print('No server_pid set')


	def SetLangPort(self, langPort):
		# Set the OSC out DAT port for language feedback
		self.ownerComp.op('oscout1').par.port = langPort
		print('langPort:', langPort)

	def DownloadSuperCollider(self):
		webbrowser.open('https://supercollider.github.io/')
		return
