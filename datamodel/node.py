import weakref

from datamodel import xmlmodel



def for_child_elem(tag):
	def deco(method):
		method.__tag__ = tag
		return method
	return deco



class Mapping (object):
	def __init__(self):
		self.__map = weakref.WeakKeyDictionary()

	def get(self, elem):
		return self.__map.get(elem)

	def put(self, elem, node):
		self.__map[elem]	= node



class NodeClass (type):
	def __init__(cls, name, bases, dict):
		super(NodeClass, cls).__init__(name, bases, dict)
		try:
			mapping = cls.__tag_mapping__
		except AttributeError:
			mapping = {}
			cls.__tag_mapping__ = mapping

		for name, value in dict.items():
			try:
				tag = value.__tag__
			except AttributeError:
				pass
			else:
				mapping[tag] = value


class Node (object):
	__metaclass__ = NodeClass

	def __init__(self, mapping, elem):
		self.__mapping = mapping
		self.elem = elem


	def child(self, child_elem):
		if isinstance(child_elem, basestring):
			return child_elem
		elif isinstance(child_elem, xmlmodel.XmlElem):
			child_node = self.__mapping.get(child_elem)
			if child_node is None:
				cls = self.__tag_mapping__[child_elem.tag]
				child_node = cls(self.__mapping, child_elem)
			return child_node
		else:
			raise TypeError
