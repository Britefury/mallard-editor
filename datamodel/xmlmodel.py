from java.awt import Color

import StringIO

import xml.sax
import xml.sax.saxutils

from BritefuryJ.Incremental import IncrementalValueMonitor
from BritefuryJ.Live import LiveValue

from Britefury.Util.LiveList import LiveList


from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan
from BritefuryJ.StyleSheet import StyleSheet



class ElemAttrs (object):
	def __init__(self, attrs=None):
		if attrs is None:
			attrs = {}
		self.__attrs = attrs
		self.__incr = IncrementalValueMonitor()


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


class XmlElem (object):
	def __init__(self, tag, **attrs):
		self.__tag = tag
		self.__attrs = ElemAttrs(attrs)
		self.__content = LiveList()



	@property
	def tag(self):
		return self.__tag

	@property
	def attrs(self):
		return self.__attrs

	@property
	def content(self):
		return self.__content


	@property
	def text_content(self):
		for x in self.__content:
			if not isinstance(x, basestring):
				raise TypeError, 'XML node tagged {0} has non-text content'.format(self.__tag)
		return ''.join(self.__content[:])


	def children_tagged(self, tag):
		return [x   for x in self.__content   if _is_tagged(x, tag)]


	def __iter__(self):
		return iter(self.__content)


	def append(self, x):
		self.__content.append(x)
		return self

	def extend(self, xs):
		self.__content.extend(xs)
		return self


	def __present__(self, fragment, inh):
		space = Label(' ')
		open_angle = self._punc_style.applyTo(Label('<'))
		close_angle = self._punc_style.applyTo(Label('>'))
		slash = self._punc_style.applyTo(Label('/'))
		tag = self._tag_style.applyTo(Label(self.__tag))
		br = LineBreak()

		complex = False
		for x in self.__content:
			if isinstance(x, XmlElem):
				complex = True
				break

		if complex:
			end = Row([open_angle, slash, tag, close_angle])
			content = Column([NormalText([x])   for x in self.__content])
			if len(self.__attrs) == 0:
				start = Row([open_angle, tag, close_angle])
			else:
				start = Span([open_angle, tag, space, br, self.__attrs, close_angle])
			return Column([start, content.padX(20.0, 0.0), end])
		else:
			if len(self.__content) == 0:
				if len(self.__attrs) == 0:
					return Row([open_angle, tag, slash, close_angle])
				else:
					return Paragraph([open_angle, tag, space, br, self.__attrs, slash, close_angle])
			else:
				end = Row([open_angle, slash, tag, close_angle])
				content = [NormalText([x])   for x in self.__content]
				if len(self.__attrs) == 0:
					start = Row([open_angle, tag, close_angle])
				else:
					start = Span([open_angle, tag, space, br, self.__attrs, close_angle])
				return Paragraph([start] + content + [end])



	def _write_sax(self, sax_handler):
		sax_handler.startElement(self.__tag, self.__attrs.attrs_dict())
		for x in self.__content:
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

	__source = __xml_header + '<xml>abc<a x="1"></a>pqr<b x="2"></b>xyz</xml>'

	def test_read(self):
		tree = XmlElem.from_string( self.__source )
		out = tree.write_as_string()
		self.assertEqual( self.__source, out )


	def test_write(self):
		a = XmlElem( 'a', x='1' )
		b = XmlElem( 'b', x='2' )
		xml = XmlElem( 'xml' ).append('abc').append(a).append('pqr').append(b).append('xyz')
		out = xml.write_as_string()
		self.assertEqual( self.__source, out )



