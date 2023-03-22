# driver_template
A template for any QIL written driver to interface with our lab equipment.
 
We define a driver as anything that allows our instruments to interface with python regardless of how many other languages it has to go through.
 
Ideally each has a set of python files, an `__init__.py` that defines the module interface whereby we can use `import repository_name` in python and ideally a jupyter notebook that serves as a minimum working example and documentation of the modules usage.
 
# Packaging
In order to make files easier to access they can be installed as a package via pip and such.
 
In our case as there may be multiple packages doing the same thing, make sure you set packages to install with a specific name i.e. `package_yourname` that way multiple branches can be tracked.
 
For the most part it is important that the driver is installed in a permanent location, and possibly in a per branch location if it is likely we are going to swap branches often (i.e. Ben and Tims moku code).
 
Install is from the package directory
 
```
pip install --editable .
```
The `--editable` flag means the installed script just points back to the folder so updates are properly reflected, hence the need for a permenant location, and clear names.


