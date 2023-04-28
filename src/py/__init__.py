import aqt, codecs, os, anki
from aqt import qt, mw, gui_hooks, QAction
from aqt.utils import tooltip, askUser, getFile
from aqt.operations import CollectionOp, OpChanges
import importlib

ADDON_PATH = os.path.dirname(__file__)
SEL_LBL = "pyop: select file"

# Create variable sharing module ########################################
def create_pyop():
	"""Create pyop module with col, did, nid and cid set to None"""
	pyop_spec = importlib.machinery.ModuleSpec('pyop', None)
	pyop_mod = importlib.util.module_from_spec(pyop_spec)
	setattr(pyop_mod, 'col', None)
	setattr(pyop_mod, 'did', None)
	setattr(pyop_mod, 'nid', None)
	setattr(pyop_mod, 'cid', None)
	return pyop_mod

# Execute user module ###################################################
def exe(parent, did: anki.decks.DeckId, nid: anki.notes.NoteId = None, cid: anki.cards.CardId = None):
	"""Load file and execute operation"""

	def operation(col: aqt.Collection, did, nid, cid):
		import pyop
		pyop.col = col
		pyop.did = did
		pyop.nid = nid
		pyop.cid = cid
		spec.loader.exec_module(opmod)
		return type('obj', (object,), {'changes' : OpChanges})()

	def succes(r: OpChanges):
		tooltip(rf'pyop: successfully executed `{file}` with `{deck}` as target')

	def failure(e: Exception):
		msg = rf'pyop: `{file}` with `{deck}` as target failed: {str(e)}'
		tooltip(msg)
		print(msg)

	spec = importlib.util.spec_from_file_location("opmod", CFG['File'])
	if spec:
		opmod = importlib.util.module_from_spec(spec)
	if not opmod:
		tooltip(f'pyop: Failed to load `{os.path.basename(CFG["File"])}`')
		return
	deck = mw.col.decks.name(did)
	file = os.path.basename(CFG['File'])
	if askUser(
		text=f'Run {file} with deck {deck}, note {nid if nid else "<none>"}, card {cid if cid else "<none>"} as background operation?',
		parent=parent, title="Run background operation"
	):
		op = CollectionOp(parent=parent, op=lambda col: operation(col, did, nid, cid))
		op.run_in_background()
		op.success(success=succes).failure(failure=failure)

# Select file ###########################################################
def select(*_):
	"""Select file to execute (will store for future executions)"""
	path = getFile(mw, "Select python module", filter="*.py", dir=os.path.join(ADDON_PATH, 'user_files'), cb=None)

	if not path:
		return
	elif os.path.isfile(path):
		CFG['File'] = path
		mw.addonManager.writeConfig(__name__, CFG)
		for action in RUN_ACTIONS.values():
			action.setText(get_label())
			action.setEnabled(True)
	else:
		CFG['File'] = ""
		for action in RUN_ACTIONS.values():
			action.setText(get_label())
			action.setEnabled(False)

# Add menu items ########################################################
def add_main_menu():
	mw.form.menuTools.addAction(SEL_ACTION)
	mw.form.menuTools.addAction(RUN_ACTIONS["mw"])
	RUN_ACTIONS["mw"].triggered.connect(lambda: exe(mw, mw.col.decks.selected()))

def add_browser_menu(browser: aqt.browser.Browser):
	browser.form.menuEdit.addAction(SEL_ACTION)
	browser.form.menuEdit.addAction(RUN_ACTIONS["browser"])
	RUN_ACTIONS["browser"].triggered.disconnect()
	RUN_ACTIONS["browser"].triggered.connect(lambda: exe(browser, browser.table.get_current_card().did))

def add_tree_menu(browser: aqt.browser.Browser, menu: qt.QMenu,
	itm: aqt.browser.SidebarItem, i: qt.QModelIndex):
	menu.addAction(RUN_ACTIONS["tree"])
	did = anki.decks.DeckId(itm.id) if browser.col.decks.have(itm.id) else None
	RUN_ACTIONS["tree"].triggered.disconnect()
	RUN_ACTIONS["tree"].triggered.connect(lambda: exe(browser, did))
	return menu

def add_table_menu(browser: aqt.browser.Browser, menu: qt.QMenu):
	menu.addAction(SEL_ACTION)
	menu.addAction(RUN_ACTIONS["table"])
	card = browser.table.get_current_card()
	RUN_ACTIONS["table"].triggered.disconnect()
	RUN_ACTIONS["table"].triggered.connect(lambda: exe(browser, card.did, card.nid, card.id))
	return menu

def get_label():
	return f"pyop: run {os.path.basename(CFG.get('File', '<none>'))}"

# Main ##################################################################
CFG = mw.addonManager.getConfig(__name__)

ttip = "Run selected python module's `operation()` function"
SEL_ACTION = QAction(SEL_LBL)
SEL_ACTION.setToolTip("Select python module")
SEL_ACTION.triggered.connect(select)
RUN_ACTIONS = {
	"mw": QAction(get_label()),
	"browser": QAction(get_label()),
	"tree": QAction(get_label()),
	"table": QAction(get_label())
}
for action in RUN_ACTIONS.values():
	action.setToolTip(ttip)

# Create module for variable sharing
pyop = create_pyop()

gui_hooks.main_window_did_init.append(add_main_menu)
gui_hooks.browser_will_show.append(add_browser_menu)
gui_hooks.browser_sidebar_will_show_context_menu.append(add_tree_menu)
gui_hooks.browser_will_show_context_menu.append(add_table_menu)
