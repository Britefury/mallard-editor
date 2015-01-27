from BritefuryJ.Pres import Pres

from BritefuryJ.Controls import MenuItem, Hyperlink, Button, VPopupMenu

from datamodel.elem_fields import elem_query

from mallard import mappings
from mallard.rich_text import controller, elem

class _Embed (elem.MRTElem):
	def copy(self):
		raise NotImplementedError, 'abstract for {0}'.format(type(self))


class InlineEmbed (_Embed):
	value = elem_query.project_to_object(mappings.inline_embed_value_mapping)

	def __init__(self, projection_table, elem):
		super(InlineEmbed, self).__init__(projection_table, elem)
		self._editorModel = controller.MallardRichTextController.instance.editorModelInlineEmbed(self)

	def __present__(self, fragment, inheritedState):
		x = Pres.coerce(self.value).withContextMenuInteractor(_inlineEmbedContextMenuFactory)
		x = controller.MallardRichTextController.instance.editableInlineEmbed(self, x)
		return x

	def copy(self):
		return InlineEmbed(self._projection_table, self.elem)


class ParaEmbed (_Embed):
	value = elem_query.project_to_object(mappings.para_embed_value_mapping)

	def __init__(self, projection_table, elem):
		super(ParaEmbed, self).__init__(projection_table, elem)
		self._editorModel = controller.MallardRichTextController.instance.editorModelParagraphEmbed(self, self)

	def __present__(self, fragment, inheritedState):
		x = Pres.coerce(self.value).withContextMenuInteractor(_paraEmbedContextMenuFactory)
		x = controller.MallardRichTextController.instance.editableParagraphEmbed(self, x)
		return x

	def copy(self):
		return ParaEmbed(self._projection_table, self.elem)




def _inlineEmbedContextMenuFactory(element, menu):
	def deleteInlineEmbed(menuItem):
		controller.MallardRichTextController.instance.deleteInlineEmbedContainingElement(element)


	deleteItem = MenuItem.menuItemWithLabel('Delete', deleteInlineEmbed)

	menu.add(deleteItem.alignHExpand())

	return True

def _paraEmbedContextMenuFactory(element, menu):
	def deleteEmbedPara(menuItem):
		controller.MallardRichTextController.instance.deleteParagraphContainingElement(element)


	deleteItem = MenuItem.menuItemWithLabel('Delete', deleteEmbedPara)

	menu.add(deleteItem.alignHExpand())

	return True


