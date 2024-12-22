<p align="center">
    <img src="media/logo.png" alt="Addon logo" height="60px" style="padding-right: 20px;">
    <img src="https://download.blender.org/branding/blender_logo_socket.png" alt="Blender logo" width="200px" style="padding-left: 20px; padding-bottom: 20px;">
</p>
<h3 align="center">
    Data visualisation addon for blender
</h3>
<p align="center">
    Load data into Blender and create visualisations!
</p>
<p align="center">
    <a href="https://github.com/Griperis/BlenderDataVis/wiki/Manual">User manual</a> |
    <a href="https://youtu.be/qIF7QPu2cOI">Video</a> |
    <a href="https://blendermarket.com/products/data-visualisation-addon">Blender Market</a> |
    <a href="https://griperis.gumroad.com/l/data-vis">Gumroad</a> |
    <a href="https://csv-extractor.herokuapp.com/">Column Extractor</a> |
    <a href="https://www.buymeacoffee.com/griperis">Buy me a coffee</a>
</p>

> [!TIP]
> The 3.0.0 version using geometry nodes is currently in the development, feel free to try it from master. Otherwise download stable 2.1.0 release.

## Quickstart
Download `data_vis.zip` and install it in Blender (Edit -> Preferences -> Addons). Or get the folder `data_vis` (from repo or the zip) and move it into blender addons directory manually.
<p align="center">
    <img src="./media/use_case.gif" height="250px">
    <img src="./media/animations_3D.gif" height="250px">
</p>

## Possible results
<p align="center">
    <img src="https://pqfusw.db.files.1drv.com/y4mdRF4h1pF4gaRw8bpA6y8jBFZGGSN458CM-01AK8f2UxQbNRYeYOcuhq56BHEosW4ZFdn81MN7a-VUwenuGRXB-1TEwmbZYbdBlpQsMQqPg5s9k3-JNEpYsSfyVfkFTDddSSt8rVU0POtvm3MhBA8fgdnkiR8WDTJmKEXlIu5ZAuzx0OsSo7aIZ37N2oTXrCyUjXFiNGyBus61GlN3LlhEw?width=1920&height=1080&cropmode=none" height="165x">
    <img src="https://jyu4wq.db.files.1drv.com/y4mDwYua54jSza0oiPv5aNGZeeY-36weBtVb0ryWTXYK-bh-tf_wBMbKsF-e7maV8Q8nN1qX7tFiaFaTPeTAqyLwr3B74N-V5T2vjc1I87MMR2iT2hyAQBXU1rV0ZRjBPbiPGmV8_ET-fhrzbB93qEog2sQuHI-1HMh40giGj8pGSwE_NxyW2MgzQVWhrNzn5FXKCHgXEQwfHEKDVKUKRZLMg?width=1920&height=1080&cropmode=none"height="165px">
    <img src="https://vsdb2q.db.files.1drv.com/y4monFbUmmqb8VmUcWKEP439PXodK3JwaruUb0BmdQVwPlZqDplRZ2ovQSLXTITw8dK04WQIbr3x0Nm4q7WazMXpnzOgtMfgEHxYRyT3-iT6rApISdwsuBgOYvxYWmv_STxJ8731EXksNV-WTGNCexFq7Xj82Ee77jW-amjmomA9rMEROw9AAZb1AwQWjBn0JheAISHNq56JnKvIYOwKk0bcQ?width=1920&height=1080&cropmode=none" height="165px">
</p>

## Introduction
Brief section about how to use the addon and what principles are applied to data and visualisations and how addon works. Addon extends Blender UI in two places:
- Add Object Menu - Create new visualisations under Chart subgroup (Shift + A)
- View3D Tools - Manipulate with data and some properties (N - DataVis tab) - this position can be edited in settings

Addon uses Blender coordinate system, 2D chart is generated along X and Z axis, 3D charts extend along Y axis. Form of chart creation and parametrization is inspired by matplotlib. I tried to make chart creation simple but customizable.

### CSV Format
Addon supports values separated by `, (commas)`
Data are in `X, Y, [Z]` format, where each entry is on new line. First line can contain labels for axis.
Two types of data are supported:

Categorical `X, Y` X is category and Y is e. g. X occurence 
```
species, occurance
dogs, 5
cats, 10
parrots, 2
```
Numerical `X, Y, [Z]` are numerical values.
```
x, sin(x)
0, 0.0
0.785, 0.706
1.57, 0.99
3.14, 0.0
```

```
x, y, x + y
0, 0, 0
0, 1, 1
1, 0, 1
1, 1, 2
```

Data also can have multiple top values  `Z in t, t + 1, t + 2`. There is a possibility to create animation and keyframes for each data and interpolate between it. (Supported for Bar, Point and Surface chart)
```
x, y, x + y
0, 0, 0, 3, 10
0, 1, 1, 4, 0
1, 0, 1, 5, 3
1, 1, 2, 1, 2
```

### Creating chart
Use add object menu and select chart which suits your needs. If you set data type and dimensions correctly, chart should create with automatic axis ranges and steps and default coloring. You can try to play with parameters and if you can come up with something cool.
All charts sizes are normalized to 1 meter cube, e. g. you can create stem chart by using bar and point chart or dual-line chart by creating two line charts with proper settings.
Addon can create materials for chart in two ways. U can check Use Nodes parameter in chart creation and addon automatically creates and assigns node shader material to your chart. Second option is that addon creates materials for each object in chart (only where objects are used). Axis and ticks with text have also default assigned material. U can customize size of step or range of axis to normalize data into different space to combine with different type of chart or to put it in different perspective.

Surface chart is supported only if you install scipy and numpy into Blenders python.
This can be done in addon preferences (experimental) or in system console using pip.

## Status
Currently supported features:
- Pie chart (Categorical)
- Line chart (Categorical, Numeric)
- Bar chart (Categorical, 2D Numeric, 3D Numeric)
- Point chart / Scatterplot (2D Numeric, 3D Numeric)
- Surface chart (Using scipy)
- Bubble chart (2D, 3D Numeric + animatable size and height)
- Creating axis with labels from data
- Ranges of data to visualise can be set
- Materials and 3 types of coloring of charts (Including default Node Shader for gradients and random colors)
- Basic animations from data
- Panel settings (to prevent sidebar cluster)
- Loaded data list
- Data inspector
- Label alignment to active camera or active view
- Chart container size
- Example data available in addon

Known issues:
- Charts from larger files (>200 entries) take long time to generate (except surface chart), because of large numbers of manipulations with objects instead of meshes

Planned features:
- Multiple categories for categorical charts
- Function plotting


Feel free to submit any issues or ideas!

## Author
Zdeněk Doležal - Bachelor Thesis

Faculty of information technology BUT

Version 2.1.1
