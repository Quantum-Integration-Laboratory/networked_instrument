#make sure you make any necassary changes before running this
from setuptools import setup, find_packages
  
with open('requirements.txt') as f:
    requirements = f.readlines()
  
with open ('readme.md') as f:
    long_description = f.read()

package_list = find_packages(where="qil-Networked")



setup(
        name ='qil-Networked',
        version ='1.0.0',
        author ='Ben Field',
        author_email ='bfie3543@uni.sydney.edu.au',
        url ='https://github.com/Quantum-Integration-Laboratory/networked_instrument',
        description ='A set of Mixin classes to allow an instrument to run a TCP/IP client and server',
        long_description = long_description,
        long_description_content_type ="text/markdown",
        license ='BSD-2',
        packages = package_list,
        classifiers =[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: BSD-2 License",
            "Operating System :: OS Independent",
        ],
        keywords =['DAQ','Mixin'],
        install_requires = requirements,
        zip_safe = False
)