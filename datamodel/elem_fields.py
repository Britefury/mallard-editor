from java.awt import Color

from BritefuryJ.Live import LiveFunction
from BritefuryJ.Pres.Primitive import Primitive, Label
from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder

from . import xmlmodel, fields

from controls import error





class AbstractQueryField (object):
	def _get(self, instance):
		raise TypeError, 'Query field of type {0} not readable'.format(type(self))

	def _set(self, instance, value):
		raise TypeError, 'Query field of type {0} not writable'.format(type(self))


	def __get__(self, instance, owner):
		if instance is None:
			return self
		else:
			return self._get(instance)

	def __set__(self, instance, value):
		self._set(instance, value)



class CompoundSimpleQueryField (AbstractQueryField):
	def __init__(self, methods):
		super(CompoundSimpleQueryField, self).__init__()
		if isinstance(methods, list)  or  isinstance(methods, tuple):
			self._methods = methods
		else:
			self._methods = [methods]


	def _get(self, instance):
		elem = instance.elem
		for method in self._methods:
			elem = method(instance, elem)
		return elem




class DerivedQueryField (AbstractQueryField):
	def __init__(self, unerlying_query_field):
		self._underlying = unerlying_query_field




class ElemQuery (CompoundSimpleQueryField):
	def child(self, __selector=None, __text=False, **attrs):
		return ElemQuery(self._methods + [lambda instance, elem: elem.child(__selector=__selector, **attrs)])

	def children(self, __selector=None, **attrs):
		return ProjectedElemListQuery(self._methods + [lambda instance, elem: elem.children_projected(__selector=__selector, **attrs)])

	def as_object(self, __default_mapping=None, **tag_mapping):
		return AsObjectQuery(self, __default_mapping, tag_mapping)



class ProjectedElemListQuery (CompoundSimpleQueryField):
	def children(self, __selector=None, **attrs):
		return ProjectedElemListQuery(self._methods + [lambda instance, projected_list: projected_list.filter(lambda x: xmlmodel._test(x, __selector, False, attrs))])

	def as_objects(self, __default_mapping=None, **tag_mapping):
		return AsObjectsQuery(self, __default_mapping, tag_mapping)




class AsObjectQuery (DerivedQueryField):
	def __init__(self, unerlying_query_field, default_mapping, tag_mapping):
		super(AsObjectQuery, self).__init__(unerlying_query_field)
		self.__default_mapping = default_mapping
		self.__tag_mapping = tag_mapping


	def _get(self, instance):
		elem = self._underlying._get(instance)
		return instance._map_elem(elem, self.__default_mapping, self.__tag_mapping)

	def _set(self, instance, value):
		elem = value.elem
		self._underlying._set(instance, elem)


class AsObjectsQuery (DerivedQueryField):
	def __init__(self, unerlying_query_field, default_mapping, tag_mapping):
		super(AsObjectsQuery, self).__init__(unerlying_query_field)
		self.__default_mapping = default_mapping
		self.__tag_mapping = tag_mapping


	def _get(self, instance):
		projected_list = self._underlying._get(instance)
		return projected_list.map(lambda x: instance._map_elem(x, self.__default_mapping, self.__tag_mapping), lambda x: instance._inv_map_elem(x))

	def _set(self, instance, value):
		elems = [instance._inv_map_elem(x)   for x in value]
		projected_list = self._underlying._get(instance)
		projected_list[:] = elems




root_query = ElemQuery([])