from java.awt import Color

from javax.swing import JFileChooser

import os
import glob

from BritefuryJ.Controls import Hyperlink

from BritefuryJ.Pres.Primitive import Primitive, Label, Row, Column
from BritefuryJ.Pres.RichText import TitleBarWithSubtitle, Page, Body

from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.DefaultPerspective import DefaultPerspective
from BritefuryJ.Projection import TransientSubject
from Britefury.Kernel.Document import Document

from LarchCore.MainApp.MainAppViewer.View import perspective
from LarchCore.MainApp.MainAppViewer.AboutPage import AboutPage

from main_app import editor_page



_page_style = StyleSheet.style(Primitive.selectable(False), Primitive.editable(False))
_dir_style = StyleSheet.style(Primitive.foreground(Color(0.0, 0.2, 0.4)))



class HomePage (object):
	def __init__(self, path):
		self.__path = path

		page_files = glob.glob(os.path.join(path, '*.page'))

		self._pages = [editor_page.EditorPage(os.path.join(path, p))   for p in page_files]


	def __present__(self , fragment, inherited_state):
		title = TitleBarWithSubtitle('Mallard editor', 'development prototype - SAVE FUNCTIONALITY NOT IMPLEMENTED')
		path = Row([Label('Displaying contents of: '), _dir_style(Label(self.__path))]).alignHPack()

		links = [Hyperlink(p.filename, editor_page.EditorPageSubject(p, fragment.subject))   for p in self._pages]

		return _page_style(Page([title, path, Column(links)]))


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
	response = openDialog.showDialog( None, 'Choose path' )
	if response == JFileChooser.APPROVE_OPTION:
		sf = openDialog.getSelectedFile()
		if sf is not None:
			filename = sf.getPath()
			if filename is not None  and  os.path.isdir( filename ):
				return HomePage(filename)

	return HomePage('.')
