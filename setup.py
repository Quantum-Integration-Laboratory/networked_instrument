#make sure you make any necassary changes before running this
from setuptools import setup, find_packages
  
with open('requirements.txt') as f:
    requirements = f.readlines()
  
long_description = 'A longer description of the project, possibly not needed as your github readme should cover this'

#scripts are full files intended to be run by the commandline, read more about this before implementing
scripts_list = ["name:path"]
#packages are files inteded to be imported by other scripts
packages_list= ["name:path"] #find_packages() is an automatic option but you have to be more careful about names


setup(
        name ='qil_name',
        version ='1.0.0',
        author ='Your name',
        author_email ='@uni.sydney.edu.au',
        url ='https://github.com/Quantum-Integration-Laboratory/',
        description ='A shorter description, possibly just copy github about section',
        long_description = long_description,
        long_description_content_type ="text/markdown",
        license ='A license type',
        packages = packages_list,
        scripts=scripts_list,
        classifiers =[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: BSD-2 License",
            "Operating System :: OS Independent",
        ],
        keywords ='anything that maybe useful',
        install_requires = requirements,
        zip_safe = False
)