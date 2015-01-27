from datamodel import node


def identity(x):
	return x



class MRTElem (node.Node):
	@staticmethod
	def coerce_contents(contents):
		if contents is None:
			return []
		else:
			return contents
