from java.awt import Color

from BritefuryJ.Pres import Pres
from BritefuryJ.Pres.Primitive import Primitive, Border, Image, Label
from BritefuryJ.Pres.RichText import Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, NormalText, Title, RichSpan, Body

from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder, FilledOutlinePainter

from BritefuryJ.Editor.RichText.Attrs import RichTextAttributes


from datamodel import node, xmlmodel
from datamodel.elem_fields import elem_query

from mallard import mappings
from mallard.rich_text import controller, elem, abstract_text



class Style (abstract_text.MRTAbstractText):
	contents_query = elem_query.children().map(abstract_text.remove_whitespace,
						   elem.identity).project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None, span_attrs=None):
		super(Style, self).__init__(projection_table, elem, contents)
		if span_attrs is None:
			span_attrs = RichTextAttributes()
			sa = StyleAttribute.tag_name_to_attr.get(elem.tag)
			if sa is not None:
				sa.store_value_from_element(span_attrs, elem)

		self._editorModel = controller.MallardRichTextController.instance.editorModelSpan([], span_attrs)
		self.setStyleAttrs(span_attrs)

	def node_init(self):
		self._editorModel.setModelContents(controller.MallardRichTextController.instance,
						   list(self.contents_query))

	def setStyleAttrs(self, styleAttrs):
		self._styleAttrs = styleAttrs
		self._style_functions = self._mapStyles(styleAttrs)
		self._editorModel.setSpanAttrs(styleAttrs)
		self._incr.onChanged()

	def getStyleAttrs(self):
		self._incr.onAccess()
		return self._styleAttrs

	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		p = RichSpan(list(self.contents_query))
		for f in self._style_functions:
			p = f(p)
		p = controller.MallardRichTextController.instance.editableSpan(self, p)
		return p



	def _mapStyles(self, spanAttrs):
		style_functions = []
		for k in spanAttrs.keySet():
			attr = StyleAttribute.tag_name_to_attr.get(k)
			if attr is not None:
				sf = attr.make_style_function(spanAttrs.getValue(k, 0))
				if sf is not None:
					style_functions.append(sf)
		return style_functions

	@staticmethod
	def new_span(mapping, contents, style_attrs=None):
		if style_attrs is not None:
			elem = None
			for k in style_attrs.keySet():
				attr = StyleAttribute.tag_name_to_attr.get(k)
				if attr is not None:
					x = attr.make_xml_element(style_attrs, elem)
					elem = x
			return Style(mapping, elem, contents, style_attrs)
		else:
			raise NotImplementedError







class StyleAttribute (object):
	tag_name_to_attr = {}


	def __init__(self, tag_name):
		self.tag_name = tag_name

		self.tag_name_to_attr[tag_name] = self
		mappings.text_mapping.map_tag(tag_name, Style)


	def make_style_function(self, value):
		raise NotImplementedError

	def make_xml_element(self, rich_text_attributes, child):
		raise NotImplementedError

	def store_value_from_element(self, rich_text_attributes, element):
		raise NotImplementedError

	def boolean_pres_fn(self, apply_to_pres):
		self.__style_function = lambda value: (lambda p: apply_to_pres(p))   if value   else None


class BooleanStyleAttribute (StyleAttribute):
	def __init__(self, tag_name):
		super(BooleanStyleAttribute, self).__init__(tag_name)
		self.__apply_to_pres = None

	def apply_to_pres(self, fn):
		self.__apply_to_pres = fn

	def make_style_function(self, value):
		if value:
			return self.__apply_to_pres
		else:
			return None

	def make_xml_element(self, rich_text_attributes, child):
		value = rich_text_attributes.getValue(self.tag_name, 0)
		if value:
			e = xmlmodel.XmlElem(self.tag_name)
			if child is not None:
				e.append(child)
			return e
		else:
			return child


	def store_value_from_element(self, rich_text_attributes, element):
		rich_text_attributes.putOverride(self.tag_name, True)



_italic_style = StyleSheet.instance.withValues(Primitive.fontItalic(True))
_bold_style = StyleSheet.instance.withValues(Primitive.fontBold(True))
_code_style = StyleSheet.instance.withValues(Primitive.fontFace(Primitive.monospacedFontName),
		Primitive.background(FilledOutlinePainter(Color(0.9, 0.9, 0.9), Color(0.75, 0.75, 0.75))))
_cmd_style = StyleSheet.instance.withValues(Primitive.fontFace(Primitive.monospacedFontName),
		Primitive.background(FilledOutlinePainter(Color(0.9, 0.9, 0.9), Color(0.75, 0.75, 0.75))),
		Primitive.foreground(Color(0.0, 0.5, 0.0)))
_cmd_prompt_style = StyleSheet.instance.withValues(Primitive.foreground(Color(0.0, 0.6, 0.5)))
_app_style = StyleSheet.instance.withValues(Primitive.fontItalic(True),
					    Primitive.foreground(Color(0.5, 0.0, 0.0)))
_sys_style = StyleSheet.instance.withValues(Primitive.fontFace(Primitive.monospacedFontName),
					    Primitive.foreground(Color(0.25, 0.0, 0.5)))



italic_style_attr = BooleanStyleAttribute('i')
@italic_style_attr.apply_to_pres
def apply_italic_style(p):
	return _italic_style.applyTo(p)

bold_style_attr = BooleanStyleAttribute('b')
@bold_style_attr.apply_to_pres
def apply_bold_style(p):
	return _bold_style.applyTo(p)

code_style_attr = BooleanStyleAttribute('code')
@code_style_attr.apply_to_pres
def apply_code_style(p):
	return _code_style.applyTo(p)

cmd_style_attr = BooleanStyleAttribute('cmd')
@cmd_style_attr.apply_to_pres
def apply_cmd_style(p):
	prompt = _cmd_prompt_style.applyTo(Label('$ '))
	return _cmd_style.applyTo(RichSpan([prompt, p]))

app_style_attr = BooleanStyleAttribute('app')
@app_style_attr.apply_to_pres
def apply_app_style(p):
	return _app_style.applyTo(p)

sys_style_attr = BooleanStyleAttribute('sys')
@sys_style_attr.apply_to_pres
def apply_sys_style(p):
	return _sys_style.applyTo(p)






