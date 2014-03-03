"""
Mallard editor XML data model


"""

from java.awt import Color

import StringIO

import xml.sax
import xml.sax.saxutils

from BritefuryJ.Incremental import IncrementalValueMonitor
from BritefuryJ.Live import LiveValue, LiveFunction

from . import projected_list


from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan
from BritefuryJ.StyleSheet import StyleSheet




class ElemAttrs (object):
	"""
	XML element attributes

	Implements the Python dictionary interface

	Live object; incremental monitor tracks accesses and changes
	"""
	def __init__(self, attrs=None):
		if attrs is None:
			attrs = {}
		self.__attrs = attrs
		self.__incr = IncrementalValueMonitor()


	def __eq__(self, other):
		if isinstance(other, ElemAttrs):
			return self.__attrs == other.__attrs
		else:
			return NotImplemented

	def __ne__(self, other):
		if isinstance(other, ElemAttrs):
			return self.__attrs != other.__attrs
		else:
			return NotImplemented


	def attrs_dict(self):
		x = {}
		x.update(self.__attrs)
		return x


	def __len__(self):
		self.__incr.onAccess()
		return len(self.__attrs)



	def __getitem__(self, key):
		self.__incr.onAccess()
		return self.__attrs[key]

	def __setitem__(self, key, value):
		self.__incr.onChanged()
		self.__attrs[key] = value

	def __delitem__(self, key):
		self.__incr.onChanged()
		del self.__attrs[key]


	def __contains__(self, key):
		self.__incr.onAccess()
		return key in self.__attrs


	def __iter__(self):
		self.__incr.onAccess()
		for k in self.__attrs.keys():
			self.__incr.onAccess()
			yield k



	def clear(self):
		self.__incr.onChanged()
		self.__attrs.clear()


	def copy(self):
		self.__incr.onAccess()
		return self.__attrs.copy()


	def get(self, key, default=None):
		self.__incr.onAccess()
		return self.__attrs.get(key, default)

	def has_key(self, key):
		self.__incr.onAccess()
		return self.__attrs.has_key(key)



	def keys(self):
		self.__incr.onAccess()
		return self.__attrs.keys()


	def update(self, values):
		self.__incr.onChanged()
		self.__attrs.update(values)


	def __pair(self, kv):
		key, value = kv
		eq = self._punc_style.applyTo(Label('='))
		return Span([self._name_style(Label(key)), eq, self._value_style(Label(value))])


	def __present__(self, fragment, inh):
		space = Label(' ')
		br = LineBreak()

		items = self.__attrs.items()

		contents = [self.__pair(items[0])]
		for x in items[1:]:
			contents.extend([space, br, self.__pair(x)])
		return Span(contents)



	_punc_style = StyleSheet.style(Primitive.foreground(Color(0.7, 0.7, 0.7)))
	_name_style = StyleSheet.style(Primitive.foreground(Color(0.0, 0.7, 0.3)))
	_value_style = StyleSheet.style(Primitive.foreground(Color(0.7, 0.3, 0.0)))


def _is_tagged(x, tag):
	return isinstance(x, XmlElem)  and  x.tag == tag


class XmlElemHasNonTextContentError (Exception):
	pass

class XmlElemMultipleChildrenMatchSelectorError (Exception):
	pass

class XmlElemenNoChildrenMatchesSelector (Exception):
	pass



def _test(elem, selector, text, attrs):
	"""
	Element selector test

	:param elem: the element or text (a str/unicode) to test
	:param selector: either 1) a tag name, 2) a list or tuple of tag names, or 3) a callable that is called with the element to test passed as a parameter
	:param text: if True, the test will only pass if elem is text
	:param attrs: a dictionary mapping attribute names to values; an element will pass the test if its attributes are a superset of those in attrs
	:return: True of the element or text passes the test, False otherwise
	"""
	if text:
		return isinstance(elem, basestring)
	else:
		if selector is not None:
			if isinstance(selector, basestring):
				if not isinstance(elem, XmlElem)  or  elem.tag != selector:
					return False
			elif isinstance(selector, list)  or  isinstance(selector, tuple):
				if not isinstance(elem, XmlElem)  or  elem.tag not in selector:
					return False
			elif callable(selector):
				if not selector(elem):
					return False
			else:
				raise TypeError, 'Selector must be a string or a callable'

		if len(attrs) > 0:
			if not isinstance(elem, XmlElem):
				return False

			a = elem.attrs.attrs_dict()
			for k, v in attrs.items():
				try:
					p = a[k]
				except KeyError:
					return False
				else:
					if p != v:
						return False

		return True






class XmlElem (object):
	def __init__(self, tag, **attrs):
		self.__tag = tag
		self.__attrs = ElemAttrs(attrs)
		self.__contents = projected_list.LiveProjectedList()



	def __eq__(self, other):
		if isinstance(other, XmlElem):
			return self.__contents == other.__contents  and  self.__attrs == other.__attrs
		else:
			return NotImplemented

	def __ne__(self, other):
		if isinstance(other, XmlElem):
			return self.__contents != other.__contents  or  self.__attrs != other.__attrs
		else:
			return NotImplemented



	@property
	def tag(self):
		return self.__tag

	@property
	def attrs(self):
		return self.__attrs

	@property
	def contents(self):
		return self.__contents


	def is_textual(self):
		for x in self.__contents:
			if not isinstance(x, basestring):
				return False
		return True



	@property
	def as_text(self):
		for x in self.__contents:
			if not isinstance(x, basestring):
				raise XmlElemHasNonTextContentError, 'XML node tagged {0} has non-text content'.format(self.__tag)
		return ''.join(self.__contents[:])


	@property
	def as_text_live(self):
		@LiveFunction
		def as_t():
			return self.as_text
		return as_t


	def __iter__(self):
		return iter(self.__contents)


	def append(self, x):
		self.__contents.append(x)
		return self

	def extend(self, xs):
		self.__contents.extend(xs)
		return self


	def children(self, __selector=None, __text=False, **attrs):
		children = []
		for x in self.__contents:
			if _test(x, __selector, __text, attrs):
				children.append(x)
		return children

	def children_projected(self, __selector=None, __text=False, **attrs):
		return self.__contents.filter(lambda x: _test(x, __selector, __text, attrs))


	def child(self, __selector=None, __text=False, **attrs):
		child = None
		for x in self.__contents:
			if _test(x, __selector, __text, attrs):
				if child is not None:
					raise XmlElemMultipleChildrenMatchSelectorError
				child = x
		if child is None:
			raise XmlElemenNoChildrenMatchesSelector
		return child


	def __present__(self, fragment, inh):
		space = Label(' ')
		open_angle = self._punc_style.applyTo(Label('<'))
		close_angle = self._punc_style.applyTo(Label('>'))
		slash = self._punc_style.applyTo(Label('/'))
		tag = self._tag_style.applyTo(Label(self.__tag))
		br = LineBreak()

		complex = False
		for x in self.__contents:
			if isinstance(x, XmlElem):
				complex = True
				break

		if complex:
			end = Row([open_angle, slash, tag, close_angle])
			content = Column([NormalText([x])   for x in self.__contents   if x != ''])
			if len(self.__attrs) == 0:
				start = Row([open_angle, tag, close_angle])
			else:
				start = Paragraph([open_angle, tag, space, br, self.__attrs, close_angle])
			return Column([start, content.padX(20.0, 0.0), end])
		else:
			if len(self.__contents) == 0:
				if len(self.__attrs) == 0:
					return Row([open_angle, tag, slash, close_angle])
				else:
					return Paragraph([open_angle, tag, space, br, self.__attrs, slash, close_angle])
			else:
				end = Row([open_angle, slash, tag, close_angle])
				content = [RichSpan([x])   for x in self.__contents]
				if len(self.__attrs) == 0:
					start = Row([open_angle, tag, close_angle])
				else:
					start = Span([open_angle, tag, space, br, self.__attrs, close_angle])
				return Paragraph([start] + content + [end])



	def _write_sax(self, sax_handler):
		sax_handler.startElement(self.__tag, self.__attrs.attrs_dict())
		for x in self.__contents:
			if isinstance(x, basestring):
				sax_handler.characters(x)
			elif isinstance(x, XmlElem):
				x._write_sax(sax_handler)
			else:
				raise TypeError, 'Invalid content of type {0}'.format(type(x))
		sax_handler.endElement(self.__tag)


	@staticmethod
	def from_file(f):
		handler = _ReadHandler()
		xml.sax.parse(f, handler)
		return handler._root

	@staticmethod
	def from_string(s):
		handler = _ReadHandler()
		xml.sax.parseString(s, handler)
		return handler._root


	def write(self, f):
		generator = xml.sax.saxutils.XMLGenerator(f)
		generator.startDocument()
		self._write_sax(generator)
		generator.endDocument()


	def write_as_string(self):
		out = StringIO.StringIO()
		generator = xml.sax.saxutils.XMLGenerator(out)
		generator.startDocument()
		self._write_sax(generator)
		generator.endDocument()
		return out.getvalue()


	_punc_style = StyleSheet.style(Primitive.foreground(Color(0.7, 0.7, 0.7)))
	_tag_style = StyleSheet.style(Primitive.foreground(Color(0.0, 0.3, 0.7)))



class _ReadHandler (xml.sax.ContentHandler):
	def __init__(self):
		self.__stack = []
		self._root = None

	def startElement(self, tag, attrs):
		e = XmlElem(tag, **attrs)
		if len(self.__stack) > 0:
			self.__stack[-1].append(e)
		else:
			self._root = e
		self.__stack.append(e)

	def endElement(self, tag):
		top = self.__stack.pop()
		if top.tag != tag:
			raise ValueError, 'Error building XML tree'

	def characters(self, x):
		self.__stack[-1].append(x)





import unittest
import StringIO


class Test_xmltree (unittest.TestCase):
	__xml_header = '<?xml version="1.0" encoding="iso-8859-1"?>\n'

	__source = __xml_header + '<xml>abc<a x="1">gg</a>pqr<b x="2"></b>xyz</xml>'

	__page = __xml_header + '<page><title>A page</title><info x="1"><first>First info<info type="sub">Sub info</info></first><second y="2">Second info</second></info></page>'


	def test_accessors(self):
		xml = XmlElem.from_string(self.__source)
		self.assertEqual(xml.tag, 'xml')
		self.assertEqual(len(xml.attrs), 0)
		self.assertEqual(len(xml.contents), 5)
		self.assertEqual(xml.contents, [x   for x in xml])


	def test_as_text(self):
		xml = XmlElem.from_string(self.__source)
		self.assertRaises(XmlElemHasNonTextContentError, lambda: xml.as_text)
		self.assertEqual(xml.contents[1].as_text, 'gg')


	def test_children(self):
		xml = XmlElem.from_string(self.__page)
		# All
		self.assertEqual(len(xml.children()), 2)
		# By tag selector
		self.assertEqual(xml.children('title')[0].tag, 'title')
		self.assertEqual(xml.children('info')[0].tag, 'info')
		# By callable selector
		self.assertEqual(xml.children(lambda e: e.tag == 'title')[0].tag, 'title')
		# By attribute
		self.assertEqual(xml.children(x='1')[0].tag, 'info')
		self.assertEqual(len(xml.children('title', x='1')), 0)
		# By tag and attribute
		self.assertEqual(xml.children('info', x='1')[0].tag, 'info')
		# Text
		self.assertEqual(xml.child('title').children(), ['A page'])



	def test_read(self):
		tree = XmlElem.from_string(self.__source)
		out = tree.write_as_string()
		self.assertEqual(self.__source, out)


	def test_write(self):
		a = XmlElem('a', x='1').append('gg')
		b = XmlElem('b', x='2')
		xml = XmlElem('xml').append('abc').append(a).append('pqr').append(b).append('xyz')
		out = xml.write_as_string()
		self.assertEqual(self.__source, out)



