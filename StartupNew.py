#!/APSshare/anaconda/x86_64/bin/python2.7

import PyQt4.QtGui as QtGui
import sys

app = QtGui.QApplication(sys.argv)

widget = QtGui.QWidget()

widget.resize(320,240)
widget.setWindowTitle('hello world')

widget.show()

sys.exit(app.exec_())

