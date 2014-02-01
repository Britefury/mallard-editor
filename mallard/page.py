from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan, Heading2
from BritefuryJ.Pres.UI import SectionHeading1
from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Live import LiveFunction

from datamodel import xmlmodel, node, elem_fields
from controls import text_entry

from . import title






class Page (node.Node):
	title_elem = elem_fields.root_query.child('title').as_object(title=title.Title)


	def __present__(self, fragment, inh):
		return Column([self.title_elem.query])



	@staticmethod
	def for_elem(elem):
		mapping = node.Mapping()
		return Page(mapping, elem)