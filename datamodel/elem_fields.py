from java.awt import Color

from BritefuryJ.Live import LiveFunction
from BritefuryJ.Pres.Primitive import Primitive, Label
from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder

from . import xmlmodel, fields

from controls import error







class QueryFieldInstance (fields.FieldInstance):
	@property
	def query(self):
		return self._field._query_for_instance(self, self._instance)




class QueryField (fields.Field):
	__field_instance_class__ = QueryFieldInstance


	def __init__(self, methods):
		super(QueryField, self).__init__()
		if isinstance(methods, list)  or  isinstance(methods, tuple):
			self._methods = methods
		else:
			self._methods = [methods]


	def _query_for_instance(self, field_instance, instance):
		elem = instance.elem
		for method in self._methods:
			elem = method(instance, elem)
		return elem





class DerivedQueryFieldInstance (fields.FieldInstance):
	pass


class DerivedQueryField (fields.Field):
	__field_instance_class__ = DerivedQueryFieldInstance

	def __init__(self, unerlying_query_field):
		super(DerivedQueryField, self).__init__()
		self._underlying = unerlying_query_field




class ElemQueryInstance (QueryFieldInstance):
	pass


class ElemQuery (QueryField):
	__field_instance_class__ = ElemQueryInstance

	def child(self, __selector, **attrs):
		return ElemQuery(self._methods + [lambda instance, elem: elem.child(__selector=__selector, **attrs)])

	def children(self, __selector, **attrs):
		return MultipleElemQuery(self._methods + [lambda instance, elem: elem.children_projected(__selector=__selector, **attrs)])

	def as_object(self, **mapping):
		return AsObjectQuery(self._methods + [lambda instance, elem: instance._map_elem(elem, mapping)])



class MultipleElemQueryInstance (QueryFieldInstance):
	pass


class MultipleElemQuery (QueryField):
	__field_instance_class__ = MultipleElemQueryInstance

	def children(self, __selector, **attrs):
		return MultipleElemQuery(self._methods + [lambda instance, projected_list: projected_list.filter(lambda x: xmlmodel._test(x, __selector, False, attrs))])

	def as_objects(self, **mapping):
		return AsObjectsQuery(self._methods + [lambda instance, projected_list: projected_list.map(lambda x: instance._map_elem(x, mapping))])




class AsObjectQueryInstance (QueryFieldInstance):
	pass

class AsObjectQuery (QueryField):
	__field_instance_class__ = AsObjectQueryInstance



class AsObjectsQueryInstance (QueryFieldInstance):
	pass

class AsObjectsQuery (QueryField):
	__field_instance_class__ = AsObjectsQueryInstance



root_query = ElemQuery([])