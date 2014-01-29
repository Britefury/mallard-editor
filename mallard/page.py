from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan, Heading2
from BritefuryJ.Pres.UI import SectionHeading1
from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Live import LiveFunction

from datamodel import xmlmodel, node, elem_fields
from controls import text_entry






class Page (node.Node):
	@elem_fields.QueryField
	def title_q(self, q):
		return q.children('title')

	title_text = title_q.element_text_content()


	def __present__(self, fragment, inh):
		title_heading = SectionHeading1('Title: ')

		title_editor = text_entry.text_entry_query_control(self.title_text)

		return Row([title_heading, title_editor])



	@staticmethod
	def for_elem(elem):
		mapping = node.Mapping()
		return Page(mapping, elem)