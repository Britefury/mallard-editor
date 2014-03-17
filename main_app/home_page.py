from java.awt import Color

from javax.swing import JFileChooser

from org.python.core.util import FileUtil

import os, glob, zipfile

from BritefuryJ.Controls import Hyperlink

from BritefuryJ.Pres.Primitive import Primitive, Spacer, Label, Row, Column
from BritefuryJ.Pres.RichText import TitleBarWithSubtitle, Page, Body, RichSpan
from BritefuryJ.Pres.UI import SectionHeading2

from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.DefaultPerspective import DefaultPerspective
from BritefuryJ.Projection import TransientSubject
from Britefury.Kernel.Document import Document

from LarchCore.MainApp.MainAppViewer.View import perspective
from LarchCore.MainApp.MainAppViewer.AboutPage import AboutPage

from Britefury import app_in_jar

from main_app import editor_page



_page_style = StyleSheet.style(Primitive.selectable(False), Primitive.editable(False))
_dir_style = StyleSheet.style(Primitive.foreground(Color(0.0, 0.2, 0.4)))



def _get_examples():
	names_and_bytes = None

	z = None
	if app_in_jar.startedFromJar():
		stream = Column.getResourceAsStream('/mallard_examples.zip')
		if stream is not None:
			f = FileUtil.wrap(stream)
			try:
				z = zipfile.ZipFile(f, 'r')
			except zipfile.BadZipfile:
				pass

	if z is None:
		if os.path.isfile('mallard_examples.zip'):
			try:
				z = zipfile.ZipFile('mallard_examples.zip', 'r')
			except zipfile.BadZipfile:
				pass


	if z is not None:
		names_and_bytes = []
		infos = z.infolist()
		for info in infos:
			if info.filename.lower().endswith('.page'):
				names_and_bytes.append((info.filename, z.read(info)))
	return names_and_bytes




class HomePage (object):
	def __init__(self, path):
		self.__path = path

		example_names_and_bytes = _get_examples()

		page_files = glob.glob(os.path.join(path, '*.page'))
		self._pages = [editor_page.EditorPage.from_path(p)   for p in page_files]


		if example_names_and_bytes is not None:
			self._example_pages = [editor_page.EditorPage.from_bytes(name, xml_bytes)   for name, xml_bytes in example_names_and_bytes]
		else:
			self._example_pages = None



	def __present__(self , fragment, inherited_state):
		title = TitleBarWithSubtitle('Mallard editor', 'development prototype - SAVE FUNCTIONALITY NOT IMPLEMENTED')
		path_heading = SectionHeading2(['Displaying contents of: ', _dir_style(RichSpan(self.__path))])

		links = [Hyperlink(p.filename, editor_page.EditorPageSubject(p, fragment.subject))   for p in self._pages]

		if self._example_pages is not None:
			examples_heading = SectionHeading2('Example mallard documents:')
			example_links = [Hyperlink(p.filename, editor_page.EditorPageSubject(p, fragment.subject))   for p in self._example_pages]
			examples_section = [Spacer(0.0, 20.0), examples_heading, Column(example_links)]
		else:
			examples_section = []

		return _page_style(Page([title, path_heading, Column(links)] + examples_section))


class HomePageSubject (TransientSubject):
	def __init__(self, home_page, world):
		super(HomePageSubject, self).__init__(world.worldSubject)
		self._home_page = home_page
		self._world = world


	def getTrailLinkText(self):
		return 'Home'


	def getFocus(self):
		return self._home_page

	def getPerspective(self):
		return DefaultPerspective.instance

	def getTitle(self):
		return 'Mallard Editor'




def new_home_page():
	openDialog = JFileChooser()
	openDialog.setFileSelectionMode( JFileChooser.DIRECTORIES_ONLY )
	openDialog.setDialogTitle('Choose directory to search for Mallard .page files')
	response = openDialog.showDialog( None, 'Choose' )
	if response == JFileChooser.APPROVE_OPTION:
		sf = openDialog.getSelectedFile()
		if sf is not None:
			filename = sf.getPath()
			if filename is not None  and  os.path.isdir( filename ):
				return HomePage(filename)

	return HomePage('.')
