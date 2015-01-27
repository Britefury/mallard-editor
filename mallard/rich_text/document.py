from java.awt import Color
from javax.imageio import ImageIO
from java.awt.datatransfer import DataFlavor
from javax.swing import JFileChooser

from BritefuryJ.Controls import MenuItem, Hyperlink, Button, VPopupMenu


from BritefuryJ.Pres import Pres
from BritefuryJ.Pres.Primitive import Primitive, Border, Image, Label
from BritefuryJ.Pres.RichText import Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, NormalText, Title, RichSpan, Body
from BritefuryJ.Pres.UI import ControlsRow, Section, SectionHeading2

from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.LSpace.TextFocus import TextSelection
from BritefuryJ.LSpace.Input import DndHandler
from BritefuryJ.LSpace.Marker import Marker

from BritefuryJ.Editor.RichText.Attrs import RichTextAttributes

from datamodel.elem_fields import elem_query

from mallard import mappings
from mallard.rich_text import controller, elem, embed

_controller = controller.MallardRichTextController.instance



class Document (elem.MRTElem):
	block_query = elem_query.project_to_object(mappings.as_block_mapping)

	def __init__(self, projection_table, elem):
		super(Document, self).__init__(projection_table, elem)
		self._editorModel = None
	
	
	def __present__(self, fragment, inheritedState):
		d = Pres.coerce(self.block_query).withContextMenuInteractor(_documentContextMenuFactory)
		d = d.withNonLocalDropDest(DataFlavor.javaFileListFlavor, _dndHighlight, _onDropImage)
		d = _controller.region(d)
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
					_controller.modifyParagraphAtMarker(caret.getMarker(), setStyle)
		return _onLink
	
	def insertEmbedPara(link, event):
		def _newEmbedPara():
			img = _imageFileChooser(link.element, lambda f: _ParaImage(f))
			return embed.ParaEmbed(img)   if img is not None   else None
		
		caret = rootElement.getCaret()
		if caret is not None and caret.isValid():
			caretElement = caret.getElement()
			if caretElement.getRegion() is region:
				_controller.insertParagraphAtCaret(caret, _newEmbedPara)
	
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
					_controller.applyStyleToSelection(selection, computeStyleValues)
		return onButton
	
	def _onInsertInlineEmbed(button, event):
		def _newInlineEmbedValue():
			return _imageFileChooser(button.element, lambda f: _InlineImage(f))
		
		caret = rootElement.getCaret()
		if caret is not None and caret.isValid():
			caretElement = caret.getElement()
			if caretElement.getRegion() is region:
				_controller.insertInlineEmbedAtMarker(caret.getMarker(), _newInlineEmbedValue)
	
	def style_button(text, on_click, *style_values):
		sty = StyleSheet.instance.withValues(Primitive.fontFace(Primitive.monospacedFontName),
						     *style_values)
		return Button(sty.applyTo(Label(text)), on_click)

	italicStyle = style_button('I', makeStyleFn('i'), Primitive.fontItalic(True))
	boldStyle = style_button('B', makeStyleFn('b'), Primitive.fontBold(True))
	codeStyle = style_button('code', makeStyleFn('code'))
	cmdStyle = style_button('> cmd', makeStyleFn('cmd'))
	appStyle = style_button('app', makeStyleFn('app'))
	sysStyle = style_button('sys', makeStyleFn('sys'))
	styles = ControlsRow([italicStyle, boldStyle, codeStyle, cmdStyle, appStyle, sysStyle]).alignHLeft()
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
	return lambda : embed.ParaEmbed(_ParaImage(imageFile))

def _makeInlineEmbeddedImageFactory(imageFile):
	return lambda : embed.InlineEmbed(_InlineImage(imageFile))

def _onDropImage(element, pos, data, action):
	marker = Marker.atPointIn(element, pos, True)
	if marker is not None and marker.isValid():
		def _onDropInline(control):
			for f in list(data):
				factory = _makeInlineEmbeddedImageFactory(f)
				_controller.insertInlineEmbedAtMarker(marker, factory)
		
		def _onDropParagraph(control):
			for f in list(data):
				factory = _makeParaEmbeddedImageFactory(f)
				_controller.insertParagraphAtMarker(marker, factory)
		
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
