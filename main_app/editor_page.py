import os

from BritefuryJ.Pres.Primitive import Primitive, Label, Row
from BritefuryJ.Pres.RichText import TitleBar, Page, Body

from BritefuryJ.StyleSheet import StyleSheet

from BritefuryJ.DefaultPerspective import DefaultPerspective
from BritefuryJ.Projection import TransientSubject
from Britefury.Kernel.Document import Document

from LarchCore.MainApp.MainAppViewer.View import perspective
from LarchCore.MainApp.MainAppViewer.AboutPage import AboutPage





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
		

		title = TitleBar(self._filename)
		return Page([title])


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
