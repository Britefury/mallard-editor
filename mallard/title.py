from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan, Heading2
from BritefuryJ.Pres.UI import SectionHeading2
from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Live import LiveFunction

from datamodel import xmlmodel, node, elem_fields
from controls import text_entry






class Title (node.Node):
	title_elem = elem_fields.root_query


	def __present__(self, fragment, inh):
		title_heading = SectionHeading2('Title: ')

		title_editor = text_entry.text_entry_query_text(lambda: self.title_elem)

		return Row([title_heading, title_editor])
