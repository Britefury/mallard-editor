from main_app import home_page

# Larch application module


# A Larch application module must define two functions; newAppState() and newAppStateSubject(world, appState)

def newAppState():
	return home_page.new_home_page()

def newAppStateSubject(world, appState):
	return home_page.HomePageSubject( appState, world )
