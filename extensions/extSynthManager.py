# extSynthManager.py
# Revised to let SuperCollider assign synth IDs.
# TouchDesigner merely sends play/update/kill requests
# and records whatever IDs SC reports back.

from TDStoreTools import StorageManager
import TDFunctions as TDF

class extSynthManager:
	"""
	Manages logical synth instances via OSC with SuperCollider.
	- PlaySynth: send '/synth play' requests (no ID).
	- UpdateSynth / KillSynth: look up tracked IDs, send '/synth update/kill'.
	- ParseSynthMessage: handle SC callbacks 'created', 'updated', 'killed'
	to keep synthTable in sync.
	"""
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.table     = ownerComp.op('synthTable')   # DAT tracking one row per voice
		self.oscOut    = ownerComp.op('oscout1')      # OSC Out DAT
		# Initialize table header if it's empty
		if self.table.numRows == 0:
			self.table.appendRow(['name', 'id', 'type', 'status'])

	# ————————————————
	# Public API
	# ————————————————

	def PlaySynth(self, name, synthType, freqs, **params):
		"""
		Play one or more voices under a logical name.
		Args:
			name (str): logical label (e.g. "pad1", "bassLine")
			synthType (str): SC SynthDef name (e.g. "simpleSine")
			freqs (float|list): one frequency or a list of freqs
			**params: additional named synth params (e.g. lpFreq=3000)
		"""
		freqs_list = freqs if isinstance(freqs, (list, tuple)) else [freqs]
		for freq in freqs_list:
			# Build a "/synth play" message with no ID field
			msg = [
				synthType,
				'play',
				'name', name,
				'freq', freq
			]
			# append any extra params
			for k, v in params.items():
				msg += [str(k), v]
			self.oscOut.sendOSC('/synth', msg)

	def UpdateSynth(self, name, **params):
		"""
		Update all voices for a given logical name.
		Sends one '/synth update' per tracked ID.
		"""
		hdr = [c.val for c in self.table.row(0)]
		# locate rows matching our name
		name_idx = hdr.index('name')
		id_idx   = hdr.index('id')
		rows = [
			(i+1, row)
			for i, row in enumerate(self.table.rows()[1:])
			if row[name_idx].val == name
		]
		if not rows:
			debug(f"[extSynthManager] No voices tracked under '{name}'")
			return

		# send update to each node, then patch table cells
		for rowIndex, rowCells in rows:
			synthType = rowCells[hdr.index('type')].val
			nodeID    = int(rowCells[id_idx].val)

			# build '/synth update' with explicit 'id' kv
			msg = [synthType, 'update', 'id', nodeID]
			for k, v in params.items():
				msg += [str(k), v]
			self.oscOut.sendOSC('/synth', msg)

			# ensure columns exist for each param, then write back
			for k, v in params.items():
				if k not in hdr:
					self._appendColumn(k)
					hdr = [c.val for c in self.table.row(0)]
				colIdx = hdr.index(k)
				rowCells[colIdx].val = v

	def KillSynth(self, name):
		"""
		Kill (free) all voices for a given logical name.
		Sends '/synth kill' per ID, then removes rows.
		"""
		hdr = [c.val for c in self.table.row(0)]
		name_idx = hdr.index('name')
		id_idx   = hdr.index('id')

		# collect row indices (descending) for safe deletion
		targets = [
			(i+1, int(row[id_idx].val))
			for i, row in enumerate(self.table.rows()[1:])
			if row[name_idx].val == name
		]
		if not targets:
			debug(f"[extSynthManager] No voices to kill under '{name}'")
			return

		# send kill messages and delete table rows
		for rowIndex, nodeID in sorted(targets, key=lambda x: -x[0]):
			synthType = self.table.row(rowIndex)[hdr.index('type')].val
			msg = [synthType, 'kill', 'id', nodeID]
			self.oscOut.sendOSC('/synth', msg)
			self.table.deleteRow(rowIndex)

	def ParseSynthMessage(self, row):
		"""
		Callback from OSC In DAT: keep table in sync.
		Expected row: [ synthType, nodeID, event, paramName1, paramVal1, ... ]
		Events:
		- created: row arrives after SC.Spawn → add a new table row
		- updated: SC confirms a set → patch the single cell
		- killed:   SC confirms free → delete the row
		"""
		# unwrap TD cells
		clean = [c.val if hasattr(c, 'val') else c for c in row]
		sType, sID, evt, *params = clean
		sID = int(sID)

		# helpers
		hdr = [c.val for c in self.table.row(0)]
		def ensureCols(names):
			for name in names:
				if name not in hdr:
					self._appendColumn(name)

		# map params list → dict
		pmap = { params[i]: params[i+1] for i in range(0, len(params), 2) }

		if evt == 'created':
			# bring in at least these columns
			ensureCols(['name', 'id', 'type', 'status'] + list(pmap.keys()))
			newRow = []
			for col in [c.val for c in self.table.row(0)]:
				if col == 'name':
					newRow.append(pmap.get('name', sType))
				elif col == 'id':
					newRow.append(sID)
				elif col == 'type':
					newRow.append(sType)
				elif col == 'status':
					newRow.append('playing')
				else:
					newRow.append(pmap.get(col, ''))
			self.table.appendRow(newRow)

		elif evt == 'updated':
			# find the row by sID and patch each param
			id_idx = hdr.index('id')
			for rowCells in self.table.rows()[1:]:
				if int(rowCells[id_idx].val) == sID:
					for k, v in pmap.items():
						ensureCols([k])
						colIdx = [c.val for c in self.table.row(0)].index(k)
						rowCells[colIdx].val = v
					break

		elif evt == 'killed':
			# find & remove row matching this ID
			id_idx = hdr.index('id')
			for i, rowCells in enumerate(self.table.rows()[1:], start=1):
				if int(rowCells[id_idx].val) == sID:
					self.table.deleteRow(i)
					break

	# ————————————————
	# Internal helpers
	# ————————————————

	def _appendColumn(self, name):
		"""Adds a new column 'name' with blank cells."""
		blanks = [''] * (self.table.numRows - 1)
		self.table.appendCol([name] + blanks)
