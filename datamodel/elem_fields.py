from java.awt import Color

from BritefuryJ.Live import LiveFunction
from BritefuryJ.Pres.Primitive import Primitive, Label
from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder

from . import xmlmodel, fields





# Error sentinel value

class QueryErrorSentinel (object):
	error_message = 'Generic query error'

	def __present__(self, fragment, inh):
		return self._sentinel_border.surround(self._sentinel_style(Label(self.error_message)))


	_sentinel_border = SolidBorder(1.0, 4.0, 5.0, 5.0, Color(1.0, 0.5, 0.5), Color(1.0, 0.95, 0.95))
	_sentinel_style = StyleSheet.style(Primitive.foreground(Color(0.3, 0.0, 0.0)))




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



	def element_text_content(self):
		return TextContentQuery(self)


	def sub_query(self, method):
		return QueryField(self._methods + [method])





class DerivedQueryFieldInstance (fields.FieldInstance):
	pass


class DerivedQueryField (fields.Field):
	__field_instance_class__ = DerivedQueryFieldInstance

	def __init__(self, unerlying_query_field):
		super(DerivedQueryField, self).__init__()
		self._underlying = unerlying_query_field




# TextContentQuery error sentinel values

class TextContentQueryElementNotFound (QueryErrorSentinel):
	error_message = 'Text content: target element not found'

class TextContentQueryMultipleElements (QueryErrorSentinel):
	error_message = 'Text content: multiple elements found'

class TextContentQueryNonTextContent (QueryErrorSentinel):
	error_message = 'Text content: non-text content'

TextContentQueryElementNotFound.instance = TextContentQueryElementNotFound()
TextContentQueryMultipleElements.instance = TextContentQueryMultipleElements()
TextContentQueryNonTextContent.instance = TextContentQueryNonTextContent()



class TextContentQueryInstance (DerivedQueryFieldInstance):
	def __init__(self, field, instance):
		super(TextContentQueryInstance, self).__init__(field, instance)


		@LiveFunction
		def live():
			e = self.__get_element()
			if isinstance(e, QueryErrorSentinel):
				return e
			try:
				return e.as_text
			except xmlmodel.XmlElemHasNonTextContentError:
				return TextContentQueryNonTextContent.instance

		self.__live = live



	def __get_element(self):
		try:
			q = self._field._underlying._query_for_instance(self, self._instance)
		except xmlmodel.XmlElemenNoChildrenMatchesSelector:
			return TextContentQueryElementNotFound.instance
		except xmlmodel.XmlElemMultipleChildrenMatchSelectorError:
			return TextContentQueryMultipleElements.instance

		if not isinstance(q, xmlmodel.XmlElem):
			l = len(q)
			if l == 1:
				q = q[0]
			elif l == 0:
				return TextContentQueryElementNotFound.instance
			else:
				return TextContentQueryMultipleElements.instance

		return q



	@property
	def value(self):
		return self.__live.getValue()

	@property
	def live(self):
		return self.__live

	def set(self, value):
		e = self.__get_element()
		if isinstance(e, QueryErrorSentinel):
			return e
		else:
			del e.contents[:]
			e.append(value)
			return None




class TextContentQuery (DerivedQueryField):
	__field_instance_class__ = TextContentQueryInstance





