from BritefuryJ.Editor.RichText import RichTextController

from mallard import rich_text



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
		return rich_text.para.Para.new_p(None, contents, paraAttrs)

	def buildSpan(self, contents, spanAttrs):
		xml_elem = spanAttrs.getAttrVal(rich_text.xml_elem_span.XML_ELEM)
		if xml_elem is not None:
			elems = [x   for x in xml_elem]
			if len(elems) > 0:
				span = None
				for elem_tag_and_attrs in reversed(elems):
					span = rich_text.xml_elem_span.XmlElemSpan.new_span(None,
											    contents,
											    elem_tag_and_attrs)
					contents = [span]
				return span

		return rich_text.style.Style.new_span(None, contents, spanAttrs)
	
	
	def isDataModelObject(self, x):
		return isinstance(x, rich_text.elem.MRTElem)
	
	def insertParagraphIntoBlockAfter(self, block, paragraph, p):
		block.insertAfter(paragraph, p)
	
	def deleteParagraphFromBlock(self, block, paragraph):
		block.removeParagraph(paragraph)
	
	def deepCopyInlineEmbedValue(self, value):
		return value


MallardRichTextController.instance = MallardRichTextController('Mallard rich text editor')

