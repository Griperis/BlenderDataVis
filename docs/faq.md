# FAQ


!!! info "Reporting Bugs"
    If you encounter a bug or would like to see a new feature to be implemented, the best place to get in touch is through [Github Issues](https://github.com/Griperis/BlenderDataVis/issues). 

!!! info "Surface Chart not available"
    In rare cases - for example when using single extensions (addons) directory for multiple Blender versions, the **Surface Chart** might not be enabled. 
    
    This is due to the fact that DataVis uses `Python`s `scipy` module to interpolate data. DataVis downloads these modules automatically on startup into its `site-packages` directory. When there is a version mismatch, the module cannot be imported correctly.

    To fix this navigate to the DataVis installation folder. For example on Windows it is typically:
    
    `C:\Users\USERNAME\AppData\Roaming\Blender Foundation\Blender\BLENDER_VERSION\extensions\EXTENSION_REPO_NAME\data_vis`.
    
    Delete the `site-packages` from the installation folder and restart Blender. The surface chart should be available now. 