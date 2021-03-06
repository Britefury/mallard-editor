from BritefuryJ.Controls import TextEntry
from BritefuryJ.Live import LiveFunction


from . import query_control
from datamodel import elem_fields, xmlmodel
from . import error





def text_entry_elem(elem):
	@LiveFunction
	def control():
		if not elem.is_textual():
			return error.error_message('Element has non-textual content')
		else:
			class Listener (TextEntry.TextEntryListener):
				def onAccept(l, control, text):
					elem.contents[:] = [text]
			return TextEntry(elem.as_text_live, Listener())
	return control



def text_entry_query_text(fn):
	@LiveFunction
	def control():
		try:
			elem = fn()
		except xmlmodel.XmlElemNoChildMatchesSelector:
			return error.error_message('Query did not match any elements')
		except xmlmodel.XmlElemMultipleChildrenMatchSelectorError:
			return error.error_message('Query matched multiple elements')

		if not elem.is_textual():
			return error.error_message('Element has non-textual content')
		else:
			class Listener (TextEntry.TextEntryListener):
				def onAccept(l, control, text):
					elem.contents[:] = [text]
			return TextEntry(elem.as_text_live, Listener())
	return control
