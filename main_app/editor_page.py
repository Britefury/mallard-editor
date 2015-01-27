import os, sys

from java.awt import Color

from BritefuryJ.Pres import Pres
from BritefuryJ.Pres.Primitive import Primitive, Label, Spacer, Row, Bin, Column
from BritefuryJ.Pres.RichText import TitleBar, Page, Body, Heading1
from BritefuryJ.Pres.UI import SectionHeading1
from BritefuryJ.Controls import ScrolledViewport

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
	def __init__(self, filename, xml_path=None, xml_bytes=None):
		self._filename = filename
		self.__xml_path = xml_path
		self.__xml_bytes = xml_bytes


	@staticmethod
	def from_path(path):
		filename = os.path.split(path)[1]
		return EditorPage(filename, xml_path=path)


	@staticmethod
	def from_bytes(filename, xml_bytes):
		return EditorPage(filename, xml_bytes=xml_bytes)


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

		if self.__xml_path is not None:
			with open(self.__xml_path, 'r') as f:
				xml_rep = xmlmodel.XmlElem.from_file(f)
		elif self.__xml_bytes is not None:
			xml_rep = xmlmodel.XmlElem.from_string(self.__xml_bytes)
		else:
			raise ValueError, 'Must provide either path or bytes'

		rich_text_rep = mallard.edit(xml_rep)

		scrolled_xml = ScrolledViewport(Pres.coerce(xml_rep).alignVRefY(), 100.0, 400.0, None)
		scrolled_rich_text = ScrolledViewport(_editable_style(rich_text_rep).alignVRefY(), 100.0, 400.0, None)
		xml_contents = Column([xml_title.alignVRefY(), Spacer(0.0, 20.0), scrolled_xml])
		rich_text_contents = Column([rich_text_title.alignVRefY(), Spacer(0.0, 20.0), scrolled_rich_text])

		xml_sec = _section_border.surround(xml_contents).pad(2.0, 2.0)
		rich_text_sec = _section_border.surround(rich_text_contents).pad(2.0, 2.0)

		contents = Row([xml_sec.alignHExpand(), rich_text_sec.alignHExpand()])

		return _info_style(Page([title.alignVRefY(), contents])).alignVExpand()


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
