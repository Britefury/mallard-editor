from datamodel.node import ProjectionMapping


title_mapping = ProjectionMapping()
as_document_mapping = ProjectionMapping()
as_block_mapping = ProjectionMapping()
block_contents_mapping = ProjectionMapping()
text_mapping = ProjectionMapping()
inline_embed_value_mapping = ProjectionMapping()
para_embed_value_mapping = ProjectionMapping()






def init_mappings():
	from . import note, page, richtext, section, title

	title_mapping.map(title=title.Title)

	as_document_mapping.map(richtext.Document)

	as_block_mapping.map(richtext.Block)

	block_contents_mapping.map(richtext.ParaEmbed, p=richtext.Para)

	text_mapping.map(richtext.XmlElemSpan, i=richtext.Style, b=richtext.Style, code=richtext.Style)

	para_embed_value_mapping.map(section=section.Section, note=note.Note)




