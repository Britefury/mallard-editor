from java.awt import Color

from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan, Heading2
from BritefuryJ.Pres.UI import SectionHeading1, SectionHeading2
from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Graphics import SolidBorder

from BritefuryJ.Live import LiveFunction

from datamodel import xmlmodel, node, elem_fields
from controls import text_entry

from . import title, richtext



_section_border = SolidBorder(1.0, 3.0, 5.0, 5.0, Color(0.3, 0.3, 0.3), None)


class Section (node.Node):
	title_elem = elem_fields.root_query.child('title').project_to_object(title=title.Title)
	text = elem_fields.root_query.project_to_object(richtext.Document)


	def __present__(self, fragment, inh):
		title = Row([SectionHeading2('Section: '), self.title_elem])
		return _section_border.surround(Column([title, self.text]))



	@staticmethod
	def for_elem(elem):
		mapping = node.ElementToObjectProjectionTable()
		return Section(mapping, elem)