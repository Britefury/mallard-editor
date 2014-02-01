from java.awt import Color

from BritefuryJ.Pres.Primitive import Primitive, Label
from BritefuryJ.StyleSheet import StyleSheet
from BritefuryJ.Graphics import SolidBorder




_error_border = SolidBorder(1.0, 4.0, 5.0, 5.0, Color(1.0, 0.5, 0.5), Color(1.0, 0.95, 0.95))
_error_style = StyleSheet.style(Primitive.foreground(Color(0.3, 0.0, 0.0)))


def error_message(message):
	return _error_border.surround(_error_style(Label(message)))




# Error sentinel value

class ErrorSentinel (object):
	error_message = 'Generic error'

	def __present__(self, fragment, inh):
		return error_message(self.error_message)


