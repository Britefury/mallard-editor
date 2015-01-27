import re

from BritefuryJ.Incremental import IncrementalValueMonitor

from mallard.rich_text import controller
from mallard.rich_text import elem


_ws_matcher = re.compile(r'\s+')


def remove_whitespace(x):
	if isinstance(x, basestring):
		return _ws_matcher.sub(' ', x)
	else:
		return x


class MRTAbstractText (elem.MRTElem):
	contents_query = None		# Abstract

	def __init__(self, projection_table, elem, contents=None):
		super(MRTAbstractText, self).__init__(projection_table, elem)
		self.contents_query.change_listener = self._on_changed
		self._editorModel = None
		self._incr = IncrementalValueMonitor()
		if contents is not None:
			self.setContents(contents)


	def _on_changed(self):
		self._editorModel.setModelContents(controller.MallardRichTextController.instance,
						   self.contents_query)
		self._incr.onChanged()


	def setContents(self, contents):
		self.contents_query = contents

	def getContents(self):
		self._incr.onAccess()
		return self.contents_query[:]


