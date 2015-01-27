from java.awt import Color

from BritefuryJ.Pres import Pres
from BritefuryJ.Pres.Primitive import Primitive, Border, Image, Label
from BritefuryJ.Pres.RichText import Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, NormalText, Title, RichSpan, Body

from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder, FilledOutlinePainter

from BritefuryJ.Editor.RichText.Attrs import RichTextAttributes

from datamodel import xmlmodel

from datamodel.elem_fields import elem_query

from mallard import mappings
from mallard.rich_text import controller, elem, abstract_text

XML_ELEM = 'xmlelem'




class XmlElemTagAndAttrs (object):
	def __init__(self, tag, attrs):
		self.tag = tag
		self.attrs = attrs


	def create_xml_elem(self):
		return xmlmodel.XmlElem(self.tag, **self.attrs)


	@staticmethod
	def from_xml_elem(e):
		return XmlElemTagAndAttrs(e.tag, e.attrs.attrs_dict())



class XmlElemSpan (abstract_text.MRTAbstractText):
	contents_query = elem_query.children()\
		.map(abstract_text.remove_whitespace, elem.identity)\
		.project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None):
		super(XmlElemSpan, self).__init__(projection_table, elem, contents)
		elem_tag_and_attrs = XmlElemTagAndAttrs.from_xml_elem(elem)
		self._elem_tag_and_attrs = elem_tag_and_attrs
		self._editorModel = controller.MallardRichTextController.instance.editorModelSpan([],
								self._span_attrs(elem_tag_and_attrs))

	def node_init(self):
		self._editorModel.setModelContents(controller.MallardRichTextController.instance,
						   list(self.contents_query))

	def setElementTagAndAttrs(self, elem_tag_and_attrs):
		self._elem_tag_and_attrs = elem_tag_and_attrs
		self._editorModel.setSpanAttrs(self._span_attrs(elem_tag_and_attrs))
		self._incr.onChanged()

	def getElementTagAndAttrs(self):
		self._incr.onAccess()
		return self._elem_tag_and_attrs

	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		open_tag = self._tag_border.surround(self._open_tag_style(Label(self._elem_tag_and_attrs.tag)))
		close_tag = self._tag_border.surround(self._close_tag_style(Label('/' + self._elem_tag_and_attrs.tag)))
		x = RichSpan([open_tag] + list(self.contents_query) + [close_tag])
		x = controller.MallardRichTextController.instance.editableSpan(self, x)
		return x

	@staticmethod
	def _span_attrs(elem_tag_and_attrs):
		return RichTextAttributes.fromValues(None, {XML_ELEM: [elem_tag_and_attrs]})


	@staticmethod
	def new_span(mapping, contents, elem_tag_and_attrs):
		return XmlElemSpan(mapping, elem_tag_and_attrs.create_xml_elem(), contents)

	_tag_border = SolidBorder(1.0, 1.0, 4.0, 4.0, Color(0.4, 0.42, 0.45), Color(0.95, 0.975, 1.0))
	_open_tag_style = StyleSheet.style(Primitive.fontSize(10), Primitive.foreground(Color(0.0, 0.3, 0.8)), Primitive.fontFace('Monospaced'))
	_close_tag_style = StyleSheet.style(Primitive.fontSize(10), Primitive.foreground(Color(0.3, 0.35, 0.4)), Primitive.fontFace('Monospaced'))



