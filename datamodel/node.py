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



class ProjectionMapping (object):
	def __init__(self):
		self.__default_cls = None
		self.__tag_to_cls = {}


	def set_default_class(self, node_cls):
		self.__default_cls = node_cls

	def map_tag(self, tag, node_cls):
		self.__tag_to_cls[tag] = node_cls


	def map(self, default_cls=None, **tag_to_cls):
		if default_cls is not None:
			self.__default_cls = default_cls
		self.__tag_to_cls.update(tag_to_cls)


	def get_class_for(self, elem):
		"""
		Create an object for a given element

		:param elem: The element to project
		"""
		return self.__tag_to_cls.get(elem.tag, self.__default_cls)






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
		self.__children_without_projection_table = None
		self.elem = elem


	def node_init(self):
		pass


	def _copy_projection_table_to_child(self, child):
		if self._projection_table is not None:
			child._set_projection_table(self._projection_table)
			self._projection_table.put(child.elem, type(child), child)
		else:
			if self.__children_without_projection_table is None:
				self.__children_without_projection_table = [child]
			else:
				self.__children_without_projection_table.append(child)


	def _set_projection_table(self, tbl):
		self._projection_table = tbl
		if self.__children_without_projection_table is not None:
			for child in self.__children_without_projection_table:
				child._set_projection_table(tbl)
			self.__children_without_projection_table = None


	def _project_elem(self, elem, mapping):
		"""
		Create an object for a given element

		:param elem: The element to project
		:param mapping: A ProjectionMapping instance
		"""
		if isinstance(elem, basestring):
			return elem
		elif isinstance(elem, xmlmodel.XmlElem):
			cls = mapping.get_class_for(elem)
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
				node.node_init()
			return node
		else:
			raise TypeError, 'elem should be a string or an XmlElem'


	def _inv_project_elem(self, obj):
		if isinstance(obj, basestring):
			return obj
		elif isinstance(obj, Node):
			if obj._projection_table is None:
				self._copy_projection_table_to_child(obj)
			return obj.elem
		else:
			raise TypeError, 'Cannot inverse project a {0} as it is not a subclass of Node'.format(type(obj))
