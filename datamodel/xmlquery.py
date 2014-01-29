from . import xmlmodel


def xq(x):
	if isinstance(x, basestring):
		elem = xmlmodel.XmlElem.from_string(x)
		return XmlQuery([elem])
	elif isinstance(x, xmlmodel.XmlElem):
		return XmlQuery([x])
	else:
		raise TypeError, 'x must be a string or an XmlElem, not a {0}'.format(type(x))




class XmlQueryEmptyError (Exception):
	pass


class XmlQueryMultipleElementsError (Exception):
	pass



class XmlQuery (object):
	def __init__(self, elems):
		self.__elems = elems


	def __len__(self):
		return len(self.__elems)


	@property
	def element(self):
		l = len(self.__elems)
		if l == 1:
			return self.__elems[0]
		elif l == 0:
			raise XmlQueryEmptyError
		else:
			raise XmlQueryMultipleElementsError

	@property
	def elements(self):
		return self.__elems[:]

	@property
	def text(self):
		return ''.join([x.text_contents   for x in self.__elems])



	@property
	def contents(self):
		for e in self.__elems:
			for c in e.contents:
				if isinstance(c, basestring):
					yield c
				else:
					yield XmlQuery([c])




	def __getitem__(self, index):
		if isinstance(index, slice):
			return XmlQuery(self.__elems[index])
		elif isinstance(index, int)  or  isinstance(index, long):
			return XmlQuery([self.__elems[index]])
		else:
			raise TypeError, 'index must be a slice, an int or a long'


	def __iter__(self):
		return (XmlQuery([x])   for x in self.__elems)



	def each(self, f):
		return [f(e)   for e in self.__elems]


	def filter(self, __selector=None, **attrs):
		return XmlQuery([e   for e in self.__elems   if self.__test_elem(e, __selector, attrs)])

	def children(self, __selector=None, **attrs):
		nodes = []
		for e in self.__elems:
			for x in e.contents:
				if isinstance(x, xmlmodel.XmlElem)  and  self.__test_elem(x, __selector, attrs):
					nodes.append(x)
		return XmlQuery(nodes)


	def find(self, __selector=None, **attrs):
		elems = []
		for e in self.__elems:
			self.__find(elems, e, __selector, attrs, False)
		return XmlQuery(elems)


	def find_all(self, __selector=None, **attrs):
		elems = []
		for e in self.__elems:
			self.__find(elems, e, __selector, attrs, True)
		return XmlQuery(elems)





	def __test_elem(self, elem, selector, attrs):
		if selector is not None:
			if isinstance(selector, basestring):
				if elem.tag != selector:
					return False
			elif callable(selector):
				if not selector(elem):
					return False
			else:
				raise TypeError, 'Selector must be a string or a callable'

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


	def __find(self, elem_list, elem, selector, attrs, descend_into_matching_elements):
		match = self.__test_elem(elem, selector, attrs)
		if match:
			elem_list.append(elem)
		if not match or descend_into_matching_elements:
			for c in elem.contents:
				if isinstance(c, xmlmodel.XmlElem):
					self.__find(elem_list, c, selector, attrs, descend_into_matching_elements)




import unittest

class TestCase_XmlQuery (unittest.TestCase):
	def setUp(self):
		xml_header = '<?xml version="1.0" encoding="iso-8859-1"?>\n'
		self._source = xml_header + '<page><title>A page</title><info x="1"><first>First info<info type="sub">Sub info</info></first><second y="2">Second info</second></info></page>'
		self._tree = xmlmodel.XmlElem.from_string(self._source)
		self._q = xq(self._tree)

	def tearDown(self):
		self._q = None
		self._tree = None
		self._source = None


	def test_accessors(self):
		# len
		self.assertEqual(len(self._q), 1)
		# element property
		self.assertEqual(self._q.element.tag, 'page')
		self.assertRaises(XmlQueryMultipleElementsError, lambda: self._q.children().element)
		# elements property
		self.assertEqual(self._q.elements, [self._tree])
		# contents property
		self.assertEqual(list(self._q.contents)[0].element.tag, 'title')
		# text property
		self.assertEqual(list(self._q.contents)[0].text, 'A page')


	def test_getitem(self):
		self.assertIsInstance(self._q[0], XmlQuery)
		self.assertEqual(self._q[0].element.tag, 'page')


	def test_iter(self):
		self.assertEqual([x.element.tag   for x in self._q], ['page'])


	def test_each(self):
		self.assertEqual(self._q.children().each(lambda e: e.tag), ['title', 'info'])


	def test_filter(self):
		# By tag selector
		self.assertEqual(self._q.children().filter('title').element.tag, 'title')
		self.assertEqual(self._q.children().filter('info').element.tag, 'info')
		# By callable selector
		self.assertEqual(self._q.children().filter(lambda e: e.tag == 'title').element.tag, 'title')
		# By attribute
		self.assertEqual(self._q.children().filter(x='1').element.tag, 'info')
		self.assertEqual(len(self._q.children().filter('title', x='1')), 0)
		# By tag and attribute
		self.assertEqual(self._q.children().filter('info', x='1').element.tag, 'info')


	def test_children(self):
		# By tag selector
		self.assertEqual(self._q.children('title').element.tag, 'title')
		self.assertEqual(self._q.children('info').element.tag, 'info')
		# By callable selector
		self.assertEqual(self._q.children(lambda e: e.tag == 'title').element.tag, 'title')
		# By attribute
		self.assertEqual(self._q.children(x='1').element.tag, 'info')
		self.assertEqual(len(self._q.children('title', x='1')), 0)
		# By tag and attribute
		self.assertEqual(self._q.children('info', x='1').element.tag, 'info')


	def test_find(self):
		self.assertEqual(len(self._q.find('info')), 1)


	def test_find_all(self):
		self.assertEqual(len(self._q.find_all('info')), 2)