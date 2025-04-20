# About


**Data Vis** addon for **Blender** allows you to create charts directly in Blender from **.csv** data. The addon was created as a part of bachelor thesis in 2020 and then was extended with several versions over the years improving its experience.

Follow the [quickstart](quickstart.md) to get you started.

![type:video](assets/titlevideo.mp4)

## Key Features

- **Easy to use** - Charts can be created in three clicks - [load .csv file](data.md), [select a chart](quickstart.md#creating-chart), customize settings and **create**.
- **Procedural** - After the data mesh is created everything is procedural - axis, axis labels, chart points. The data mesh can have as many points as your computer can handle.
- **Fast** - Compared to version 2.0.0 where ~1000 datapoints were a bottleneck, it is possible to visualise data with ~100k data points and possibly more depending on hardware.
- **Chart Components** - Add and remove [axis](features/axis.md), [data labels](features/data_labels.md) or [animation](features/animations.md) separately and adaptively. 
- **Customizable** - Many of the properties like axis ranges, label sizes and materials can be adjusted directly from the modifier or N-panel.
- **Materials** - use *Attributes* to customize the material of your charts using shaders.  

???+ info "How it works?"
    Charts are created using geometry nodes modifiers. Addon loads your data and creates mesh out of the CSV data points. The datapoints are then processed through several geometry nodes [modifiers](charts.md#data-modifier) to create the chart. The mesh data contains the information about animations using shape keys. Axis and data labels are created as additional modifiers.

## Feedback, Bugs, Suggestions
If you have feedback, encountered a bug or want to extend the addon, please visit the [GitHub](https://github.com/Griperis/BlenderDataVis/) repository of the addon.

## Future Development
The project is developed in free time as a hobby. If you are interested in new features or development, feel free to contact me.
There are definitely certain areas that could be improved:

- Data loading API
    - Support .json DataFrame like format
    - Rewrite the data loading API to be more robust so individual components are exchangable
- Additional chart types
    - Candle Chart
    - 3D Categorical Charts
- Pie chart improvements
    - Unlimited Data Points
    - More Animations
- Function Plotting
- Animations scaling the generated data, not only datapoint positions