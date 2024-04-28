# File: docs.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Manipulates tooltips and docs across the addon


from .general import DV_ShowPopup


SPECIFIC_DATA_DOCS = {
    "famous-marketshare_2D.csv": "data suitable for [pie chart], check apple's first iphone presentation",
    "species_2D.csv": "distribution of species in some area, good for [pie chart] or [bar chart]",
    "species_2D_anim.csv": "changing distribution of species in some area, good for animated [bar chart]",
    "survey-result_2D.csv": "result of user-experience questionaire for data-vis, good for [bar chart]",
    "time-data_1_2D.csv": 'datapoints in a timeline - combine with "time-data_2_2D.csv" in a [line chart]',
    "x+y-small_3D.csv": "small example of 3D x+y function, good for [bar chart, bubble chart, point chart]",
    "function-fancy_3D_anim.csv": "animated 3d function, good for [surface chart, bar chart, point chart]",
    "tan_1000-val_3D.csv": "large example of tan function, best suitable for [surface chart]",
}


def get_example_data_doc(example: str) -> str:
    """Generates documentaion string from example filename"""
    docs = []

    if "2D" in example:
        docs.append("2D data, suitable for flat visualisations")
    elif "3D" in example:
        docs.append("3D data that can be displayed in space or flat")
        docs.append("valid 3D data can be used to generate 2D charts")
    if "anim" in example:
        docs.append("example containing animations")

    if example in SPECIFIC_DATA_DOCS:
        docs.append(SPECIFIC_DATA_DOCS[example])

    docs = [f"- {d}" for d in docs]
    return "\n".join(docs)


TOOLTIPS = {
    "container_size": "Size of the container (box) in which chart is going to be created into. \n"
    "Size of chart is not changeable afterwards.",
    "data": "Make sure that the data you are visualising are suitable for the chart of your choice. \n"
    "For example it doesn't make sense to visualize numerical data in a pie chart or categorical data\n"
    "in surface chart. Addon tries to be smart about this, but there are many edge cases. Please \n"
    "refer to the examples and if something is unclear, report it to https://github.com/Griperis/BlenderDataVis",
}


def draw_tooltip_button(layout, tooltip):
    tooltip_text = TOOLTIPS.get(tooltip, None)
    if tooltip_text is None:
        return

    col = layout.column(align=True)
    col.enabled = True
    col.alignment = "RIGHT"
    col.emboss = "NONE"
    popup = col.operator(DV_ShowPopup.bl_idname, text="", icon="QUESTION")
    popup.title = "Tooltip"
    popup.msg = tooltip_text
