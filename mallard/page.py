from BritefuryJ.Controls import TextEntry

from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column, Paragraph, LineBreak, Span
from BritefuryJ.Pres.RichText import NormalText, RichSpan, Heading2
from BritefuryJ.Pres.UI import SectionHeading1
from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.Live import LiveFunction

from datamodel import xmlmodel, node






class Page (node.Node):
	def __init__(self, mapping, elem):
		super(Page, self).__init__(mapping, elem)


		def _title():
			titles = self.elem.children_tagged('title')
			if len(titles) == 1:
				return titles[0].text_contents
			elif len(titles) == 0:
				return None
			else:
				raise ValueError, 'multiple title elements'


		class _TitleSave (TextEntry.TextEntryListener):
			def onAccept(self_, control, text):
				titles = self.elem.children_tagged('title')
				if len(titles) == 0:
					self.elem.contents.insert(xmlmodel.XmlElem('title').append(text))
				else:
					titles[0].contents[:] = text

		self._title_save = _TitleSave()
		self.title = LiveFunction(_title)



	def __present__(self, fragment, inh):
		title_heading = SectionHeading1('Title: ')

		title_editor = TextEntry(self.title, self._title_save)

		return Row([title_heading, title_editor])



	@staticmethod
	def for_elem(elem):
		mapping = node.Mapping()
		return Page(mapping, elem)