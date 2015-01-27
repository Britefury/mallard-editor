from BritefuryJ.Incremental import IncrementalValueMonitor

from BritefuryJ.Pres.RichText import Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, NormalText, Title, RichSpan, Body

from BritefuryJ.Editor.RichText.Attrs import RichTextAttributes

from datamodel import xmlmodel
from datamodel.elem_fields import elem_query

from mallard import mappings
from mallard.rich_text import controller, elem, abstract_text



class Para (abstract_text.MRTAbstractText):
	contents_query = elem_query.children()\
		.map(abstract_text.remove_whitespace,elem.identity)\
		.project_to_objects(mappings.text_mapping)

	def __init__(self, projection_table, elem, contents=None, attrs=None):
		super(Para, self).__init__(projection_table, elem, contents)
		style = None
		if attrs is not None:
			style = attrs.getValue('style', 0)
		style = style   if style is not None   else 'normal'
		self._style = style

		para_attrs = RichTextAttributes.fromValues({'style':self._style}, None)

		self._editorModel = controller.MallardRichTextController.instance.editorModelParagraph(self,
			[], para_attrs)

	
	def node_init(self):
		self._editorModel.setModelContents(controller.MallardRichTextController.instance,
						   list(self.contents_query))


	def setStyle(self, style):
		self._style = style
		para_attrs = RichTextAttributes.fromValues({'style':self._style}, None)
		self._editorModel.setParaAttrs(para_attrs)
		self._incr.onChanged()
	
	_styleMap = {'normal':NormalText,
		     'h1':Heading1,
		     'h2':Heading2,
		     'h3':Heading3,
		     'h4':Heading4,
		     'h5':Heading5,
		     'h6':Heading6,
		     'title':Title}
	
	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		xs = list(self.contents_query)
		combinatorClass = self._styleMap[self._style]
		x = combinatorClass(xs)
		x = controller.MallardRichTextController.instance.editableParagraph(self, x)
		return x


	@staticmethod
	def new_p(mapping, contents, style_attrs=None):
		return Para(mapping, xmlmodel.XmlElem('p'), contents, style_attrs)




class _TempBlankPara (elem.MRTElem):
	def __init__(self, projection_table, block):
		super(_TempBlankPara, self).__init__(projection_table, None)

		self._block = block
		self._style = 'normal'
		self._incr = IncrementalValueMonitor()
		para_attrs = RichTextAttributes.fromValues({'style': self._style}, None)
		self._editorModel = controller.MallardRichTextController.instance.editorModelParagraph([], para_attrs)


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

	_styleMap = {'normal':NormalText,
		     'h1':Heading1,
		     'h2':Heading2,
		     'h3':Heading3,
		     'h4':Heading4,
		     'h5':Heading5,
		     'h6':Heading6,
		     'title':Title}

	def __present__(self, fragment, inheritedState):
		self._incr.onAccess()
		x = NormalText('')
		x = controller.MallardRichTextController.instance.editableParagraph(self, x)
		return x

	def __repr__(self):
		return '<blank_para'


