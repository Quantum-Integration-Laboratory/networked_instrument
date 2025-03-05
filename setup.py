#make sure you make any necassary changes before running this
from setuptools import setup, find_packages

"""
_______________________________________________________

All Changes are the strings below
_______________________________________________________
"""
#Must change
DriverName="qil_Networked"
version ='1.0.0'
author ='Ben Field'
email ='bfie3543@.sydney.edu.au'
repository_url = 'https://github.com/Quantum-Integration-Laboratory/networked_instrument'
description ='A set of Mixin classes to allow an instrument to run a TCP/IP client and server'

#Less important
license ='GPL-3.0'
classifiers =["Programming Language :: Python :: 3",
            "License :: OSI Approved :: BSD-2 License",
            "Operating System :: OS Independent",]
keywords =['DAQ','mixin']



"""
_______________________________________________________

For standard use these lines should not need to be changed
_______________________________________________________
"""
  
#gets all the requirements
with open('requirements.txt') as f:
    requirements = f.readlines()

#Copys the github read me as the long description
with open ('readme.md') as f:
    long_description = f.read()
    
#automatically gets all packages in the passed folder
package_list = find_packages()#where=DriverName


setup(
        name =DriverName,
        version =version,
        author =author,
        author_email =email,
        url =repository_url,
        description =description,
        long_description = long_description,
        long_description_content_type ="text/markdown",
        license =license,
        packages = package_list,
        classifiers =classifiers,
        keywords =keywords,
        install_requires = requirements,
        zip_safe = False
)