from . import mappings, page

mappings.init_mappings()


def edit(elem):
	return page.Page.for_elem(elem)
