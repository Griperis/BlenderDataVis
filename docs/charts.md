# Charts

After loading data, appropriate charts are available in `Create Chart` menu.

![Create Chart Menu](assets/create_chart.png)

Check how to add or customize individual chart features like [axis](features/axis.md)
or [colors](features/color.md). 

Everything begins with a chart mesh created from the `Create Chart`. This mesh represents
the data in 3D. `XYZ` positions are based on the data and `Shape Keys` are used to handle animatinos. `W` attribute is assigned to mesh attributes.

Two core modifiers of the charts are data modifier and chart modifier. These modifiers work together to manipulate the chart mesh into a form of a chart.

## Supported Chart Types

The following chart types are available in the `Create Chart` menu:

| Chart Type      | Description                                 |
|-----------------|---------------------------------------------|
| Bar Chart       | Visualizes data as bars.         |
| Line Chart      | Connects data points with lines.             |
| Point Chart (Scatter Plot)    | Displays data as points in 3D space.         |
| Pie Chart       | Represents data as slices of a circle.       |
| Surface Chart   | Shows data as a 3D surface.                  |

## Data Modifier

This modifier takes the mesh, normalizes it into a `Container Size` space, calculates various attributes used in other modifiers and allows modifying ranges.

| Attribute         | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| Container Size    | The normalized space in which the mesh is fit.                              |
| Auto Range        | Switches between automatic range taken from the data or values from `Min Range` and `Max Range`.                  |
| Min Range         | Defines **minimum** for data points to be taken from. Used to exclude points from the visualised data.                              |
| Max Range         | Defines **maximum** for data points to be taken from. Used to exclude points from the visualised data.                 |
| Override Z Range  | Toggle to override Z range in addition to `Auto Range`. This is used for defining the base contanier for animations range.              |
| Z Min             | **Minimum** used when `Override Z Range` is toggled.   |
| Z Max             | **Maximum** used when `Override Z Range` is toggled.   |

## Chart Modifier

Each chart type has it's own modifier and values that can be tweaked to customize the chart.
All charts have a `Material` to assign material for the chart.