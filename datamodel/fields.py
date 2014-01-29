__author__ = 'Geoff'



class FieldInstance (object):
	def __init__(self, field, instance):
		self._field = field
		self._instance = instance



class Field (object):
	__field_instance_class__ = FieldInstance


	def __init__(self):
		self._name = None
		self._cls = None
		self._attr_name = None


	def _class_init(self, cls, name):
		self._name = name
		self._cls = cls
		self._attr_name = intern('__node_field_' + name)


	def _instance_init(self, instance):
		setattr(instance, self._attr_name, self.__field_instance_class__(self, instance))


	def __get__(self, instance, owner):
		if instance is None:
			return self
		else:
			return getattr(instance, self._attr_name)


