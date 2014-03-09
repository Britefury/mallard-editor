import os, sys

from java.awt import Color

from BritefuryJ.Pres import Pres
from BritefuryJ.Pres.Primitive import Primitive, Label, Spacer, Row, Bin, Column
from BritefuryJ.Pres.RichText import TitleBar, Page, Body, Heading1
from BritefuryJ.Pres.UI import SectionHeading1

from BritefuryJ.Graphics import SolidBorder, FillPainter

from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.DefaultPerspective import DefaultPerspective
from BritefuryJ.Projection import TransientSubject
from Britefury.Kernel.Document import Document

from LarchCore.MainApp.MainAppViewer.View import perspective
from LarchCore.MainApp.MainAppViewer.AboutPage import AboutPage


_info_style = StyleSheet.style(Primitive.selectable(False), Primitive.editable(False))
_editable_style = StyleSheet.style(Primitive.selectable(True), Primitive.editable(True))

_section_heading_style = StyleSheet.style(Primitive.background(FillPainter(Color(0.925, 0.925, 0.925))))

_section_border = SolidBorder(1.0, 3.0, 4.0, 4.0, Color(0.4, 0.4, 0.4), None)


def unload_modules_starting_with(prefixes):
	to_remove = []
	for m in sys.modules:
		for prefix in prefixes:
			if m.startswith(prefix):
				to_remove.append(m)
	for m in to_remove:
		del sys.modules[m]


class EditorPage (object):
	def __init__(self, path):
		self.__path = path
		_, self._filename = os.path.split(path)


	@property
	def path(self):
		return self.__path

	@property
	def filename(self):
		return self._filename


	def __present__(self , fragment, inherited_state):
		unload_modules_starting_with(['controls', 'datamodel', 'mallard'])

		from datamodel import xmlmodel
		from mallard import mallard

		title = _info_style(TitleBar(self._filename))

		xml_title = _section_heading_style(SectionHeading1('XML (non-editable)')).alignHExpand()
		rich_text_title = _section_heading_style(SectionHeading1('Rich text (editable)')).alignHExpand()

		with open(self.__path, 'r') as f:
			xml_rep = xmlmodel.XmlElem.from_file(f)

		rich_text_rep = mallard.edit(xml_rep)

		xml_contents = Column([xml_title, Spacer(0.0, 20.0), Pres.coerce(xml_rep).alignVRefY()])
		rich_text_contents = Column([rich_text_title, Spacer(0.0, 20.0), _editable_style(rich_text_rep).alignVRefY()])

		xml_sec = _section_border.surround(xml_contents.alignHPack()).pad(2.0, 2.0)
		rich_text_sec = _section_border.surround(rich_text_contents.alignHPack()).pad(2.0, 2.0)

		contents = Row([xml_sec.alignHExpand().alignVTop(), rich_text_sec.alignHExpand().alignVTop()])

		return _info_style(Page([title, contents]))


class EditorPageSubject (TransientSubject):
	def __init__(self, editor, enclosing_subject):
		super(EditorPageSubject, self).__init__(enclosing_subject)
		self._editor = editor


	def getTrailLinkText(self):
		return self._editor._filename


	def getFocus(self):
		return self._editor

	def getPerspective(self):
		return DefaultPerspective.instance

	def getTitle(self):
		return self._editor._filename
