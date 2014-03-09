from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan, Heading2
from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Live import LiveFunction

from datamodel import xmlmodel, node
from datamodel.elem_fields import elem_query
from controls import text_entry






class Title (node.Node):
	title_elem = elem_query


	def __present__(self, fragment, inh):
		title_editor = text_entry.text_entry_query_text(lambda: self.title_elem)

		return title_editor
