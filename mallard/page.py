from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan, Heading2
from BritefuryJ.Pres.UI import SectionHeading1, SectionHeading2
from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Live import LiveFunction

from datamodel import xmlmodel, node
from datamodel.elem_fields import elem_query
from controls import text_entry

from . import mappings, title, section, note, rich_text






class Page (node.Node):
	title_elem = elem_query.child('title').project_to_object(mappings.title_mapping)
	text = elem_query.project_to_object(mappings.as_document_mapping)


	def __present__(self, fragment, inh):
		title = Row([SectionHeading2('Title: '), self.title_elem])
		return Column([title, self.text])



	@staticmethod
	def for_elem(elem):
		mapping = node.ElementToObjectProjectionTable()
		return Page(mapping, elem)