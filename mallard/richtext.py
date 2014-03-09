from java.util import List
from java.lang import System
from java.awt.datatransfer import DataFlavor
from javax.imageio import ImageIO
from javax.swing import JFileChooser

import itertools

from copy import copy

from BritefuryJ.Controls import MenuItem, Hyperlink, Button, VPopupMenu


from BritefuryJ.Pres import Pres
from BritefuryJ.Pres.Primitive import Primitive, Border, Image
from BritefuryJ.Pres.RichText import Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, NormalText, Title, RichSpan, Body
from BritefuryJ.Pres.UI import ControlsRow, Section, SectionHeading2

from BritefuryJ.LSpace.TextFocus import TextSelection
from BritefuryJ.LSpace.Input import DndHandler
from BritefuryJ.LSpace.Marker import Marker

from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Incremental import IncrementalValueMonitor

from Britefury.Util.Abstract import abstractmethod

from BritefuryJ.Editor.RichText import RichTextController


from datamodel import node, xmlmodel
from datamodel.elem_fields import elem_query
import mallard

from . import mappings





class MallardRichTextController (RichTextController):
	def setModelContents(self, model, contents):
		model.setContents(contents)
	
	def modelToEditorModel(self, model):
		return model._editorModel
	
	
	def buildInlineEmbed(self, value):
		return InlineEmbed(value)
	
	def buildParagraphEmbed(self, value):
		return ParaEmbed(value)
	
	def buildParagraph(self, contents, styleAttrs):
		return Para.new_p(None, contents, dict(styleAttrs))

	def buildSpan(self, contents, styleAttrs):
		return Style(contents, dict(styleAttrs))
	
	
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
	contents_query = elem_query.children().project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None, style_attrs=None):
		super(Style, self).__init__(projection_table, elem, contents)
		if style_attrs is None:
			style_attrs = {}
		self._editorModel = _editor.editorModelSpan(self.coerce_contents(contents), style_attrs)
		self.setStyleAttrs(style_attrs)

	def setStyleAttrs(self, styleAttrs):
		self._styleAttrs = styleAttrs
		self._styleSheet = self._mapStyles(styleAttrs)
		self._editorModel.setStyleAttrs(styleAttrs)
		self._incr.onChanged()

	def getStyleAttrs(self):
		self._incr.onAccess()
		return self._styleAttrs

	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		x = self._styleSheet.applyTo(RichSpan(list(self.contents_query)))
		x = _editor.editableSpan(self, x)
		return x


	_styleMap = {}
	_styleMap['italic'] = lambda x: (Primitive.fontItalic, bool(x))
	_styleMap['bold'] = lambda x: (Primitive.fontBold, bool(x))

	def _mapStyles(self, styleAttrs):
		styleSheet = StyleSheet.instance
		for k in styleAttrs:
			f = self._styleMap.get(k)
			if f is not None:
				(attrib, value) = f(styleAttrs[k])
				styleSheet = styleSheet.withAttr(attrib, value)
		return styleSheet





class Para (MRTAbstractText):
	contents_query = elem_query.children().project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None, attrs=None):
		super(Para, self).__init__(projection_table, elem, contents)
		if attrs is None:
			attrs = {}
		else:
			attrs = dict(attrs)
		self._style = attrs.get('style', 'normal')

		self._editorModel = _editor.editorModelParagraph(self, self.coerce_contents(contents), {'style':self._style})
	
	
	def setStyle(self, style):
		self._style = style
		self._editorModel.setStyleAttrs({'style':style})
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
		self._editorModel = _editor.editorModelParagraph([], {'style':self._style})
		
	
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
		pass

class InlineEmbed (_Embed):
	value = elem_query.project_to_object(mappings.inline_embed_value_mapping)

	def __init__(self, projection_table, elem):
		super(InlineEmbed, self).__init__(projection_table, elem)
		self._editorModel = _editor.editorModelInlineEmbed(self)
	
	def __present__(self, fragment, inheritedState):
		x = Pres.coerce(self.value).withContextMenuInteractor(_inlineEmbedContextMenuFactory)
		x = _editor.editableInlineEmbed(self, x)
		return x


class ParaEmbed (_Embed):
	value = elem_query.project_to_object(mappings.para_embed_value_mapping)

	def __init__(self, projection_table, elem):
		super(ParaEmbed, self).__init__(projection_table, elem)
		self._editorModel = _editor.editorModelParagraphEmbed(self, self)
	
	def __present__(self, fragment, inheritedState):
		x = Pres.coerce(self.value).withContextMenuInteractor(_paraEmbedContextMenuFactory)
		x = _editor.editableParagraphEmbed(self, x)
		return x


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


	def _filterContents(self, xs):
		return [x   for x in xs   if not isinstance(x, _TempBlankPara)]
	
	
	def _on_changed(self):
		self._editorModel.setModelContents(_editor,  self.contents_query)
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
		def computeStyleValues(styleAttrDicts):
			value = dict(styleAttrDicts[0]).get(attrName, False)
			value = not value
			attrs = {}
			attrs[attrName] = value
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
	
	italicStyle = Button.buttonWithLabel('I', makeStyleFn('italic'))
	boldStyle = Button.buttonWithLabel('B', makeStyleFn('bold'))
	styles = ControlsRow([italicStyle, boldStyle]).alignHLeft()
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
