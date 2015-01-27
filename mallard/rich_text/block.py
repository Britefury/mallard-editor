from BritefuryJ.Incremental import IncrementalValueMonitor

from BritefuryJ.Pres.RichText import Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, NormalText, Title, RichSpan, Body

from datamodel.elem_fields import elem_query

from mallard import mappings
from mallard.rich_text import controller, elem, para


class Block (elem.MRTElem):
	contents_query = elem_query.children(['p', 'section', 'note']).project_to_objects(mappings.block_contents_mapping)

	def __init__(self, projection_table, elem, contents=None):
		super(Block, self).__init__(projection_table, elem)
		self.contents_query.change_listener = self._on_changed
		self._editorModel = controller.MallardRichTextController.instance.editorModelBlock([])
		self._incr = IncrementalValueMonitor()
		if contents is not None:
			self.setContents(contents)

	def node_init(self):
		self._editorModel.setModelContents(controller.MallardRichTextController.instance,
						   list(self.contents_query))



	def _filterContents(self, xs):
		return [x   for x in xs   if not isinstance(x, para._TempBlankPara)]
	
	
	def _on_changed(self):
		self._editorModel.setModelContents(controller.MallardRichTextController.instance,
						   list(self.contents_query))
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
		xs = list(contents)   if len(contents) > 0   else [para._TempBlankPara(self._projection_table, self)]
		#xs = self._contents + [_TempBlankPara( self )]
		x = Body(xs)
		x = controller.MallardRichTextController.instance.editableBlock(self, x)
		return x


