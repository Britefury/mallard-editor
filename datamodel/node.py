import weakref

from datamodel import xmlmodel, fields



class ElementToObjectProjectionTable (object):
	"""
	Maps element and object class to object.

	Effectively a dictionary mapping (element, obj_class) -> object

	The elements are weak keys.
	"""
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
	"""
	Node metaclass
	"""
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
	"""
	Node class
	"""
	__metaclass__ = NodeClass

	def __init__(self, projection_table, elem):
		for name, field in self.__fields__.items():
			field._instance_init(self)
		self._projection_table = projection_table
		self.elem = elem



	def _project_elem(self, elem, default_class, tag_to_class):
		"""
		Create an object for a given element

		:param elem: The element to project
		"""
		if isinstance(elem, basestring):
			return elem
		elif isinstance(elem, xmlmodel.XmlElem):
			cls = tag_to_class.get(elem.tag, default_class)
			if cls is None:
				raise TypeError, 'Could not determine object class for \'{0}\' element for node type {1}'.format(elem.tag, type(self))
			if not isinstance(cls, NodeClass):
				if callable(cls):
					cls = cls()
				else:
					raise TypeError, 'Object class for \'{0}\' element for node type {1} is of type {2}, should be a NodeClass or a callable'.format(elem.tag, type(self), type(cls))
			node = self._projection_table.get(elem, cls)
			if node is None:
				node = cls(self._projection_table, elem)
				self._projection_table.put(elem, cls, node)
			return node
		else:
			raise TypeError


	def _inv_project_elem(self, obj):
		if isinstance(obj, basestring):
			return obj
		elif isinstance(obj, Node):
			if obj._projection_table is None:
				obj._projection_table = self._projection_table
				obj._projection_table.put(obj.elem, type(obj), obj)
			return obj.elem
		else:
			raise TypeError, 'Cannot inverse project a {0} as it is not a subclass of Node'.format(type(obj))
