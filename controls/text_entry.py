from BritefuryJ.Controls import TextEntry
from BritefuryJ.Live import LiveFunction


from . import query_control
from datamodel import elem_fields




def text_entry_query_control(query_instance):
	@LiveFunction
	def control():
		live = query_instance.live
		val = live.getValue()
		if isinstance(val, elem_fields.QueryErrorSentinel):
			return val
		else:
			class Listener (TextEntry.TextEntryListener):
				def onAccept(l, control, text):
					query_instance.set(text)
			return TextEntry(live, Listener())
	return control

