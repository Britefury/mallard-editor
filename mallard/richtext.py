from java.util import List
from java.lang import System
from java.awt.datatransfer import DataFlavor
from java.awt import Color
from javax.imageio import ImageIO
from javax.swing import JFileChooser

import itertools, re

from copy import copy

from BritefuryJ.Controls import MenuItem, Hyperlink, Button, VPopupMenu


from BritefuryJ.Pres import Pres
from BritefuryJ.Pres.Primitive import Primitive, Border, Image, Label
from BritefuryJ.Pres.RichText import Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, NormalText, Title, RichSpan, Body
from BritefuryJ.Pres.UI import ControlsRow, Section, SectionHeading2

from BritefuryJ.LSpace.TextFocus import TextSelection
from BritefuryJ.LSpace.Input import DndHandler
from BritefuryJ.LSpace.Marker import Marker

from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder, FilledOutlinePainter

from BritefuryJ.Incremental import IncrementalValueMonitor

from Britefury.Util.Abstract import abstractmethod

from BritefuryJ.Editor.RichText import RichTextController
from BritefuryJ.Editor.RichText.Attrs import RichTextAttributes


from datamodel import node, xmlmodel
from datamodel.elem_fields import elem_query
import mallard

from . import mappings


_XML_ELEM = 'xmlelem'

_ws_matcher = re.compile(r'\s+')


def _remove_whitespace(x):
	if isinstance(x, basestring):
		return _ws_matcher.sub(' ', x)
	else:
		return x

def _identity(x):
	return x




class MallardRichTextController (RichTextController):
	def setModelContents(self, model, contents):
		model.setContents(contents)

	def modelToEditorModel(self, model):
		return model._editorModel


	def buildInlineEmbed(self, value):
		return value.copy()

	def buildParagraphEmbed(self, value):
		return value.copy()

	def buildParagraph(self, contents, paraAttrs):
		return Para.new_p(None, contents, paraAttrs)

	def buildSpan(self, contents, spanAttrs):
		xml_elem = spanAttrs.getAttrVal(_XML_ELEM)
		if xml_elem is not None:
			elems = [x   for x in xml_elem]
			if len(elems) > 0:
				span = None
				for elem_tag_and_attrs in reversed(elems):
					span = XmlElemSpan.new_span(None, contents, elem_tag_and_attrs)
					contents = [span]
				return span

		return Style.new_span(None, contents, spanAttrs)


	def isDataModelObject(self, x):
		return isinstance(x, MRTElem)

	def insertParagraphIntoBlockAfter(self, block, paragraph, p):
		block.insertAfter(paragraph, p)

	def deleteParagraphFromBlock(self, block, paragraph):
		block.removeParagraph(paragraph)

	def deepCopyInlineEmbedValue(self, value):
		return value


_editor = MallardRichTextController('Mallard rich text editor')


class MRTElem (node.Node):
	@staticmethod
	def coerce_contents(contents):
		if contents is None:
			return []
		else:
			return contents


class MRTAbstractText (MRTElem):
	contents_query = None		# Abstract

	def __init__(self, projection_table, elem, contents=None):
		super(MRTAbstractText, self).__init__(projection_table, elem)
		self.contents_query.change_listener = self._on_changed
		self._editorModel = None
		self._incr = IncrementalValueMonitor()
		if contents is not None:
			self.setContents(contents)


	def _on_changed(self):
		self._editorModel.setModelContents(_editor,  self.contents_query)
		self._incr.onChanged()


	def setContents(self, contents):
		self.contents_query = contents

	def getContents(self):
		self._incr.onAccess()
		return self.contents_query[:]






class Style (MRTAbstractText):
	contents_query = elem_query.children().map(_remove_whitespace, _identity).project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None, span_attrs=None):
		super(Style, self).__init__(projection_table, elem, contents)
		if span_attrs is None:
			span_attrs = RichTextAttributes()
			sa = StyleAttribute.tag_name_to_attr.get(elem.tag)
			if sa is not None:
				sa.store_value_from_element(span_attrs, elem)

		self._editorModel = _editor.editorModelSpan([], span_attrs)
		self.setStyleAttrs(span_attrs)

	def node_init(self):
		self._editorModel.setModelContents(_editor, list(self.contents_query))

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
		p = _editor.editableSpan(self, p)
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
_code_style = StyleSheet.instance.withValues(Primitive.fontFace(Primitive.monospaceFontName),
		Primitive.background(FilledOutlinePainter(Color(0.9, 0.9, 0.9), Color(0.75, 0.75, 0.75))))
_cmd_style = StyleSheet.instance.withValues(Primitive.fontFace(Primitive.monospaceFontName),
		Primitive.background(FilledOutlinePainter(Color(0.9, 0.9, 0.9), Color(0.75, 0.75, 0.75))),
		Primitive.foreground(Color(0.0, 0.5, 0.0)))
_cmd_prompt_style = StyleSheet.instance.withValues(Primitive.foreground(Color(0.0, 0.6, 0.5)))
_app_style = StyleSheet.instance.withValues(Primitive.fontItalic(True),
					    Primitive.foreground(Color(0.5, 0.0, 0.0)))



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








class XmlElemTagAndAttrs (object):
	def __init__(self, tag, attrs):
		self.tag = tag
		self.attrs = attrs


	def create_xml_elem(self):
		return xmlmodel.XmlElem(self.tag, **self.attrs)


	@staticmethod
	def from_xml_elem(e):
		return XmlElemTagAndAttrs(e.tag, e.attrs.attrs_dict())



class XmlElemSpan (MRTAbstractText):
	contents_query = elem_query.children().map(_remove_whitespace, _identity).project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None):
		super(XmlElemSpan, self).__init__(projection_table, elem, contents)
		elem_tag_and_attrs = XmlElemTagAndAttrs.from_xml_elem(elem)
		self._elem_tag_and_attrs = elem_tag_and_attrs
		self._editorModel = _editor.editorModelSpan([], self._span_attrs(elem_tag_and_attrs))

	def node_init(self):
		self._editorModel.setModelContents(_editor, list(self.contents_query))

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
		x = _editor.editableSpan(self, x)
		return x

	@staticmethod
	def _span_attrs(elem_tag_and_attrs):
		return RichTextAttributes.fromValues(None, {_XML_ELEM: [elem_tag_and_attrs]})


	@staticmethod
	def new_span(mapping, contents, elem_tag_and_attrs):
		return XmlElemSpan(mapping, elem_tag_and_attrs.create_xml_elem(), contents)

	_tag_border = SolidBorder(1.0, 1.0, 4.0, 4.0, Color(0.4, 0.42, 0.45), Color(0.95, 0.975, 1.0))
	_open_tag_style = StyleSheet.style(Primitive.fontSize(10), Primitive.foreground(Color(0.0, 0.3, 0.8)), Primitive.fontFace('Monospaced'))
	_close_tag_style = StyleSheet.style(Primitive.fontSize(10), Primitive.foreground(Color(0.3, 0.35, 0.4)), Primitive.fontFace('Monospaced'))





class Para (MRTAbstractText):
	contents_query = elem_query.children().map(_remove_whitespace, _identity).project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None, attrs=None):
		super(Para, self).__init__(projection_table, elem, contents)
		style = None
		if attrs is not None:
			style = attrs.getValue('style', 0)
		style = style   if style is not None   else 'normal'
		self._style = style

		para_attrs = RichTextAttributes.fromValues({'style':self._style}, None)

		self._editorModel = _editor.editorModelParagraph(self, [], para_attrs)


	def node_init(self):
		self._editorModel.setModelContents(_editor, list(self.contents_query))


	def setStyle(self, style):
		self._style = style
		para_attrs = RichTextAttributes.fromValues({'style':self._style}, None)
		self._editorModel.setParaAttrs(para_attrs)
		self._incr.onChanged()

	_styleMap = {'normal':NormalText, 'h1':Heading1, 'h2':Heading2, 'h3':Heading3, 'h4':Heading4, 'h5':Heading5, 'h6':Heading6, 'title':Title}

	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		xs = list(self.contents_query)
		combinatorClass = self._styleMap[self._style]
		x = combinatorClass(xs)
		x = _editor.editableParagraph(self, x)
		return x


	@staticmethod
	def new_p(mapping, contents, style_attrs=None):
		return Para(mapping, xmlmodel.XmlElem('p'), contents, style_attrs)



class _TempBlankPara (MRTElem):
	def __init__(self, projection_table, block):
		super(_TempBlankPara, self).__init__(projection_table, None)

		self._block = block
		self._style = 'normal'
		self._incr = IncrementalValueMonitor()
		para_attrs = RichTextAttributes.fromValues({'style': self._style}, None)
		self._editorModel = _editor.editorModelParagraph([], para_attrs)


	def setContents(self, contents):
		if len(contents) == 0:
			return
		elif len(contents) == 1 and contents[0] == '':
			return
		p = Para.new_p(self._projection_table, contents)
		self._block.append(p)

	def getContents(self):
		self._incr.onAccess()
		return []

	def setStyle(self, style):
		self._style = style
		self._incr.onChanged()

	_styleMap = {'normal':NormalText, 'h1':Heading1, 'h2':Heading2, 'h3':Heading3, 'h4':Heading4, 'h5':Heading5, 'h6':Heading6, 'title':Title}

	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		x = NormalText('')
		x = _editor.editableParagraph(self, x)
		return x

	def __repr__(self):
		return '<blank_para'



class _Embed (MRTElem):
	def copy(self):
		raise NotImplementedError, 'abstract for {0}'.format(type(self))


class InlineEmbed (_Embed):
	value = elem_query.project_to_object(mappings.inline_embed_value_mapping)

	def __init__(self, projection_table, elem):
		super(InlineEmbed, self).__init__(projection_table, elem)
		self._editorModel = _editor.editorModelInlineEmbed(self)

	def __present__(self, fragment, inheritedState):
		x = Pres.coerce(self.value).withContextMenuInteractor(_inlineEmbedContextMenuFactory)
		x = _editor.editableInlineEmbed(self, x)
		return x

	def copy(self):
		return InlineEmbed(self._projection_table, self.elem)


class ParaEmbed (_Embed):
	value = elem_query.project_to_object(mappings.para_embed_value_mapping)

	def __init__(self, projection_table, elem):
		super(ParaEmbed, self).__init__(projection_table, elem)
		self._editorModel = _editor.editorModelParagraphEmbed(self, self)

	def __present__(self, fragment, inheritedState):
		x = Pres.coerce(self.value).withContextMenuInteractor(_paraEmbedContextMenuFactory)
		x = _editor.editableParagraphEmbed(self, x)
		return x

	def copy(self):
		return ParaEmbed(self._projection_table, self.elem)




def _inlineEmbedContextMenuFactory(element, menu):
	def deleteInlineEmbed(menuItem):
		_editor.deleteInlineEmbedContainingElement(element)


	deleteItem = MenuItem.menuItemWithLabel('Delete', deleteInlineEmbed)

	menu.add(deleteItem.alignHExpand())

	return True

def _paraEmbedContextMenuFactory(element, menu):
	def deleteEmbedPara(menuItem):
		_editor.deleteParagraphContainingElement(element)


	deleteItem = MenuItem.menuItemWithLabel('Delete', deleteEmbedPara)

	menu.add(deleteItem.alignHExpand())

	return True


class Block (MRTElem):
	contents_query = elem_query.children(['p', 'section', 'note']).project_to_objects(mappings.block_contents_mapping)

	def __init__(self, projection_table, elem, contents=None):
		super(Block, self).__init__(projection_table, elem)
		self.contents_query.change_listener = self._on_changed
		self._editorModel = _editor.editorModelBlock([])
		self._incr = IncrementalValueMonitor()
		if contents is not None:
			self.setContents(contents)

	def node_init(self):
		self._editorModel.setModelContents(_editor, list(self.contents_query))



	def _filterContents(self, xs):
		return [x   for x in xs   if not isinstance(x, _TempBlankPara)]


	def _on_changed(self):
		self._editorModel.setModelContents(_editor, list(self.contents_query))
		self._incr.onChanged()


	def setContents(self, contents):
		self.contents_query = self._filterContents(list(contents))


	def append(self, para):
		self.contents_query.append(para)

	def insertAfter(self, para, p):
		index = -1
		for (i, x) in enumerate(self.contents_query):
			if p is x:
				index = i
		self.contents_query.insert(index + 1, para)

	def removeParagraph(self, para):
		index = -1
		for (i, x) in enumerate(self.contents_query):
			if para is x:
				index = i
		if index != -1:
			del self.contents_query[index]
		else:
			raise ValueError, 'could not find para'


	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		contents = self.contents_query
		xs = list(contents)   if len(contents) > 0   else [_TempBlankPara(self._projection_table, self)]
		#xs = self._contents + [_TempBlankPara( self )]
		x = Body(xs)
		x = _editor.editableBlock(self, x)
		return x





class Document (MRTElem):
	block_query = elem_query.project_to_object(mappings.as_block_mapping)

	def __init__(self, projection_table, elem):
		super(Document, self).__init__(projection_table, elem)
		self._editorModel = None


	def __present__(self, fragment, inheritedState):
		d = Pres.coerce(self.block_query).withContextMenuInteractor(_documentContextMenuFactory)
		d = d.withNonLocalDropDest(DataFlavor.javaFileListFlavor, _dndHighlight, _onDropImage)
		d = _editor.region(d)
		return d


def _img(img, maxwidth, maxheight):
	scale = min(maxwidth / float(img.width), 1.0)
	scale = min(maxheight / float(img.height), scale)
	return Image(img, img.width * scale, img.height * scale)

class _EmbeddedImage (object):
	def __init__(self, imageFile):
		self._image = ImageIO.read(imageFile)

class _InlineImage (_EmbeddedImage):
	def __present__(self, fragment, inheritedState):
		return Border(_img(self._image, 128.0, 80.0))

class _ParaImage (_EmbeddedImage):
	def __present__(self, fragment, inherited_state):
		return Border(_img(self._image, 640, 400.0))

def _documentContextMenuFactory(element, menu):
	region = element.getRegion()
	rootElement = element.getRootElement()

	def makeParagraphStyleFn(style):
		def setStyle(model):
			model.setStyle(style)

		def _onLink(link, event):
			caret = rootElement.getCaret()
			if caret is not None and caret.isValid():
				caretElement = caret.getElement()
				if caretElement.getRegion() is region:
					_editor.modifyParagraphAtMarker(caret.getMarker(), setStyle)
		return _onLink

	def insertEmbedPara(link, event):
		def _newEmbedPara():
			img = _imageFileChooser(link.element, lambda f: _ParaImage(f))
			return ParaEmbed(img)   if img is not None   else None

		caret = rootElement.getCaret()
		if caret is not None and caret.isValid():
			caretElement = caret.getElement()
			if caretElement.getRegion() is region:
				_editor.insertParagraphAtCaret(caret, _newEmbedPara)

	normalStyle = Hyperlink('Normal', makeParagraphStyleFn('normal'))
	h1Style = Hyperlink('H1', makeParagraphStyleFn('h1'))
	h2Style = Hyperlink('H2', makeParagraphStyleFn('h2'))
	h3Style = Hyperlink('H3', makeParagraphStyleFn('h3'))
	h4Style = Hyperlink('H4', makeParagraphStyleFn('h4'))
	h5Style = Hyperlink('H5', makeParagraphStyleFn('h5'))
	h6Style = Hyperlink('H6', makeParagraphStyleFn('h6'))
	titleStyle = Hyperlink('Title', makeParagraphStyleFn('title'))
	paraStyles = ControlsRow([normalStyle, h1Style, h2Style, h3Style, h4Style, h5Style, h6Style, titleStyle])
	embedPara = Hyperlink('Embed para', insertEmbedPara)
	paraEmbeds = ControlsRow([embedPara])
	menu.add(Section(SectionHeading2('Paragraph styles'), paraStyles))
	menu.add(Section(SectionHeading2('Paragraph embeds'), paraEmbeds))


	def makeStyleFn(attrName):
		def computeStyleValues(listOfSpanAttrs):
			value = listOfSpanAttrs[0].getValue(attrName, 0)
			value = not value
			attrs = RichTextAttributes()
			attrs.putOverride(attrName, value)
			return attrs

		def onButton(button, event):
			selection = rootElement.getSelection()
			if isinstance(selection, TextSelection):
				if selection.getRegion() == region:
					_editor.applyStyleToSelection(selection, computeStyleValues)
		return onButton

	def _onInsertInlineEmbed(button, event):
		def _newInlineEmbedValue():
			return _imageFileChooser(button.element, lambda f: _InlineImage(f))

		caret = rootElement.getCaret()
		if caret is not None and caret.isValid():
			caretElement = caret.getElement()
			if caretElement.getRegion() is region:
				_editor.insertInlineEmbedAtMarker(caret.getMarker(), _newInlineEmbedValue)

	italicStyle = Button.buttonWithLabel('I', makeStyleFn('i'))
	boldStyle = Button.buttonWithLabel('B', makeStyleFn('b'))
	codeStyle = Button.buttonWithLabel('code', makeStyleFn('code'))
	cmdStyle = Button.buttonWithLabel('> cmd', makeStyleFn('cmd'))
	styles = ControlsRow([italicStyle, boldStyle, codeStyle, cmdStyle]).alignHLeft()
	insertInlineEmbed = Button.buttonWithLabel('Embed', _onInsertInlineEmbed)
	inlineEmbeds = ControlsRow([insertInlineEmbed]).alignHLeft()

	menu.add(Section(SectionHeading2('Selection styles'), styles))
	menu.add(Section(SectionHeading2('Inline embeds'), inlineEmbeds))


	return True


def _dndHighlight(element, graphics, pos, action):
	marker = Marker.atPointIn(element, pos, False)
	if marker is not None and marker.isValid():
		DndHandler.drawCaretDndHighlight(graphics, element, marker)

def _makeParaEmbeddedImageFactory(imageFile):
	return lambda : ParaEmbed(_ParaImage(imageFile))

def _makeInlineEmbeddedImageFactory(imageFile):
	return lambda : InlineEmbed(_InlineImage(imageFile))

def _onDropImage(element, pos, data, action):
	marker = Marker.atPointIn(element, pos, True)
	if marker is not None and marker.isValid():
		def _onDropInline(control):
			for f in list(data):
				factory = _makeInlineEmbeddedImageFactory(f)
				_editor.insertInlineEmbedAtMarker(marker, factory)

		def _onDropParagraph(control):
			for f in list(data):
				factory = _makeParaEmbeddedImageFactory(f)
				_editor.insertParagraphAtMarker(marker, factory)

		menu = VPopupMenu([MenuItem.menuItemWithLabel('Inline', _onDropInline), MenuItem.menuItemWithLabel('As paragraph', _onDropParagraph)])
		menu.popupMenuAtMousePosition(marker.getElement())
	return True

def _imageFileChooser(element, imageValueFn):
	component = element.getRootElement().getComponent()
	fileChooser = JFileChooser()
	response = fileChooser.showDialog(component, 'Open')
	if response == JFileChooser.APPROVE_OPTION:
		sf = fileChooser.getSelectedFile()
		if sf is not None:
			return imageValueFn(sf)
	return None
