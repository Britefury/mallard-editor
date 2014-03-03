from java.awt import Color

from BritefuryJ.Live import LiveFunction
from BritefuryJ.Pres.Primitive import Primitive, Label
from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder

from . import xmlmodel, fields

from controls import error





class AbstractQueryField (object):
	"""
	Abstract element query field

	Descriptors allow client code to get and set its value
	"""
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



class _CompoundSimpleQueryField (AbstractQueryField):
	"""
	The compound simple query field has a list of methods.

	It computes its value by:
		Starting with the element that underlies the node instance, it calls each method in turn like so:
		return methodN(......(method2(instance, method1(instance, method0(instance, elem)))))
	"""
	def __init__(self, methods):
		super(_CompoundSimpleQueryField, self).__init__()
		if isinstance(methods, list)  or  isinstance(methods, tuple):
			self._methods = methods
		else:
			self._methods = [methods]


	def _get(self, instance):
		elem = instance.elem
		for method in self._methods:
			elem = method(instance, elem)
		return elem




class _DerivedQueryField (AbstractQueryField):
	"""
	Derived query field has an underling query field
	"""
	def __init__(self, underlying_query_field):
		self._underlying = underlying_query_field




class ElemQuery (_CompoundSimpleQueryField):
	"""
	Element query

	Results in a single element
	"""
	def child(self, __selector=None, __text=False, **attrs):
		"""
		Returns a query that will descend from the element matching this query to a child element matching the provided tests

		:param __selector: a tag, list of tags or callable function that identifies elements that pass
		:param __text: if True, only text will pass
		:param attrs: attributes that the element must match in order to pass

		:return: an ElemQuery
		"""
		return ElemQuery(self._methods + [lambda instance, elem: elem.child(__selector=__selector, **attrs)])

	def children(self, __selector=None, **attrs):
		"""
		Returns a query that will descend from the element matching this query to a a list of child elements that match the provided tests

		:param __selector: a tag, list of tags or callable function that identifies elements that pass
		:param __text: if True, only text will pass
		:param attrs: attributes that the element must match in order to pass

		:return: an ProjectedElemListQuery
		"""
		return ProjectedElemListQuery(self._methods + [lambda instance, elem: elem.children_projected(__selector=__selector, **attrs)])

	def project_to_object(self, __default_class=None, **tag_mapping):
		"""
		Returns a query that will project the element matched by this query to an object

		:param __default_class: the default node class
		:param tag_mapping: a dictionary mapping element tag name to class

		:return: a ProjectElementToObjectQuery
		"""
		return ProjectElementToObjectQuery(self, __default_class, tag_mapping)



class ProjectedElemListQuery (_CompoundSimpleQueryField):
	def filter(self, __selector=None, **attrs):
		"""
		Returns a query that will filter the elements matching this query, retaining elements that match the provided tests

		:param __selector: a tag, list of tags or callable function that identifies elements that pass
		:param __text: if True, only text will pass
		:param attrs: attributes that the element must match in order to pass

		:return: an ProjectedElemListQuery
		"""
		return ProjectedElemListQuery(self._methods + [lambda instance, projected_list: projected_list.filter(lambda x: xmlmodel._test(x, __selector, False, attrs))])

	def project_to_objects(self, __default_mapping=None, **tag_mapping):
		"""
		Returns a query that will project the elements matched by this query to objects

		:param __default_class: the default node class
		:param tag_mapping: a dictionary mapping element tag name to class

		:return: a ProjectElementListToObjectListQuery
		"""
		return ProjectElementListToObjectListQuery(self, __default_mapping, tag_mapping)




class ProjectElementToObjectQuery (_DerivedQueryField):
	"""
	A query that projects an element to an object

	Can also be set
	"""
	def __init__(self, underlying_query_field, default_mapping, tag_mapping):
		super(ProjectElementToObjectQuery, self).__init__(underlying_query_field)
		self.__default_mapping = default_mapping
		self.__tag_mapping = tag_mapping


	def _get(self, instance):
		elem = self._underlying._get(instance)
		return instance._project_elem(elem, self.__default_mapping, self.__tag_mapping)

	def _set(self, instance, value):
		elem = value.elem
		self._underlying._set(instance, elem)


class ProjectElementListToObjectListQuery (_DerivedQueryField):
	"""
	A query that projects an element list to an object list

	Can also be set
	"""
	def __init__(self, underlying_query_field, default_mapping, tag_mapping):
		super(ProjectElementListToObjectListQuery, self).__init__(underlying_query_field)
		self.__default_mapping = default_mapping
		self.__tag_mapping = tag_mapping


	def _get(self, instance):
		projected_list = self._underlying._get(instance)
		return projected_list.map(lambda x: instance._project_elem(x, self.__default_mapping, self.__tag_mapping), lambda x: instance._inv_project_elem(x))

	def _set(self, instance, value):
		elems = [instance._inv_project_elem(x)   for x in value]
		projected_list = self._underlying._get(instance)
		projected_list[:] = elems




root_query = ElemQuery([])