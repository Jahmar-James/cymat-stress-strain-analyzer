"""
FRONTEND
main.py
/tkinter_frontend
    /core
    /top_level_create_sample
     - __init__.py
     -settings_top_level_create_sample.py
    /top_level_create_sample_group
    /top_level_plotting

BACKEND
/data_extraction -  Different formats of data fomart and styles
    - __init__.py
    - mechanical_test_data_preprocessor.py - Normalize data columns names and units
    /Cleaners - various ways to preprocess data ie. which columns to keep, which to drop, unit?, etc
        - __init__.py
        - default_data_cleaner.py
        - MTS_data_cleaner_2020.py
        - Element_data_cleaner.py
/stadards
    - __init__.py
    - sample_factory.py - Factory class to create samples
    /bases
        - __init__.py
        - analyzable_entity.py - inherited by sample and sample_group providing common methods and interface
        - base_standard_validator.py - ensure data adheres to standards
        - base_standard_operator.py - calculate sample propeties (sperating data and data processing) - will contain all methods use be default sample
        - base_standard_io_manager.py - store and load data into presistent storage. provide a remapping when needed
        - base_standard_group_io_manager.py - groups require a different way to store and load data and to consider the relationship between samples
    /default_sample - default sample class
        - __init__.py
        - sample.py - data storage, orchestrate sample creation and the nessary properties required for a sample
        - validator.py - unsure data meets standards so that sample can be created
        - sample_group.py - a collection of default samples. Possible with aggregation properties
    /visualizations_sample
    /iso_13314_2011
        - __init__.py
        - sample.py
/Visualization
    - plotting_manager.py         
    - plot_data_helpers.py  
/config
    - __init__.py
    /app_settings
    /workflow_settings
/tests
"""