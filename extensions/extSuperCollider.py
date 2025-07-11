from TDStoreTools import StorageManager
import TDFunctions as TDF

class extSuperCollider:
	"""
	extSuperCollider description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	def StartSuperCollider(self):
		pass

	def SetLangPort(self, langPort):
		self.ownerComp.op('oscout1').par.port = langPort
		print('langPort: ', langPort)
		pass
