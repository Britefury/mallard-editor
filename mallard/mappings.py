from datamodel.node import ProjectionMapping


title_mapping = ProjectionMapping()
as_document_mapping = ProjectionMapping()
as_block_mapping = ProjectionMapping()
block_contents_mapping = ProjectionMapping()
text_mapping = ProjectionMapping()
inline_embed_value_mapping = ProjectionMapping()
para_embed_value_mapping = ProjectionMapping()






def init_mappings():
	from . import note, page, section, title
	from .rich_text import document, block, embed, para, xml_elem_span, style

	title_mapping.map(title=title.Title)

	as_document_mapping.map(document.Document)

	as_block_mapping.map(block.Block)

	block_contents_mapping.map(embed.ParaEmbed, p=para.Para)

	text_mapping.map(xml_elem_span.XmlElemSpan)

	para_embed_value_mapping.map(section=section.Section, note=note.Note)




