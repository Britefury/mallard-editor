import weakref

from datamodel import xmlmodel, fields



def for_child_elem(tag):
	def deco(method):
		method.__tag__ = tag
		return method
	return deco



class Mapping (object):
	def __init__(self):
		self.__map = weakref.WeakKeyDictionary()

	def get(self, elem, cls):
		m = self.__map.get(elem)
		return m.get(cls)   if m is not None   else None

	def put(self, elem, cls, node):
		m = self.__map.get(elem)
		if m is None:
			m = {}
			self.__map[elem] = m
		m[cls] = node



class NodeClass (type):
	def __init__(cls, name, bases, dict):
		super(NodeClass, cls).__init__(name, bases, dict)
		__tag_mapping__ = {}
		try:
			__tag_mapping__.update(cls.__tag_mapping__)
		except AttributeError:
			pass
		cls.__tag_mapping__ = __tag_mapping__

		__fields__ = {}
		try:
			__fields__.update(cls.__fields__)
		except AttributeError:
			pass
		cls.__fields__ = __fields__


		for name, value in dict.items():
			try:
				tag = value.__tag__
			except AttributeError:
				pass
			else:
				__tag_mapping__[tag] = value

			if isinstance(value, fields.Field):
				value._class_init(cls, name)
				__fields__[name] = value





class Node (object):
	__metaclass__ = NodeClass

	def __init__(self, mapping, elem):
		for name, field in self.__fields__.items():
			field._instance_init(self)
		self._mapping = mapping
		self.elem = elem



	def _map_elem(self, elem, default_mapping, tag_mapping):
		if isinstance(elem, basestring):
			return elem
		elif isinstance(elem, xmlmodel.XmlElem):
			if default_mapping is not None:
				cls = default_mapping
			else:
				cls = tag_mapping[elem.tag]
			node = self._mapping.get(elem, cls)
			if node is None:
				node = cls(self._mapping, elem)
				self._mapping.put(elem, cls, node)
			return node
		else:
			raise TypeError


	def _inv_map_elem(self, x):
		if isinstance(x, basestring):
			return x
		elif isinstance(x, Node):
			if x._mapping is None:
				x._mapping = self._mapping
				x._mapping.put(x.elem, type(x), x)
			return x.elem
		else:
			raise TypeError, 'Cannot inverse map a {0} as it is not a subclass of Node'.format(type(x))
