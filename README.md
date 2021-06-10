# Overview

I was looking for a way to provide a docker image for development teams with the following in mind:
* Consistent  
* Repeatable  
* Customizable  
* Simple  
* Adherence  
* Standards  
* Secure  

All of this with my personal objective of:  
> Can I provide a self service solution that allows someone to build images with limited knowledge of docker and no hands on experience?  

## Docker Compose
Source: https://docs.docker.com/compose/  
My interpretation: a way to orchestrate your images to build out a functional working environment.  
Which is great but not aligned to my objective.  

## Docker Multi-stage builds
Source: https://docs.docker.com/develop/develop-images/multistage-build/  
My interpretation: a way to coordinate build artifacts between images to maintain a slim final image.  
Which is great but not aligned to my objective.

# Solution
Since I could not find what I wanted I decided to make it.  
> Provide a collection of individual docker commands which can be combined into a single file.  

To visualize the solution you can think of graphical user interface (GUI) programing.  
Example: https://realpython.com/learning-paths/python-gui-programming/  
Find the widget you want, drag to the docker file and click build.  

## Check list
In order to achieve my solution I have to consider:  
* How to organize the list of items to select  
* How to pull the selected items into a docker file  
* How to provide clean simple interaction for items  
* How to provide tagging and versioning information  
* How to handle versioning for items  
* How to notify versioning changes for items  

## Decisions
1. Language: For this I selected Python 3 to code in as I am comfortable with it, but to be fair any language could be used.  
1. Versioning: For this I am going to use git tags.  
1. Organize: For this I decided to use folders as some items require additional files.  

## Improvements
1. Create GUI interface to drive the idea.  

# Run
To get started install the following:  
* Python 3 - https://realpython.com/installing-python/  
* PIP - https://pip.pypa.io/en/stable/installing/  
* Modules: `pip install -r requirements.txt`  

Then
1. Update inputs.properties file  
   ```  
   [image]  
   PARENT_NAME=docker image:tag for this value  
   SELECTED_ITEMS=comma delimited entries of the folders you want to include  
   ```  
1. Execute script `python3 build-it.py`  
1. Build docker image: `docker build build`  
1. Test image  
1. Cleanup containers: `docker container rm $(docker container ls --filter status=exited -q)`  
1. Tag image  
1. Upload to your favorite repository  
1. Or copy contents of build folder into project and keep with code  

# Result
Now you have:  
* A folder list of items that can be included in image  
* An input file to select which items to include into image  
* A simple clean two input requirement to include items to interact with  
* Versioning of the tool based on github tags  
* Labels in docker files to provide any documentation or notes on the install  

What is left:  
* All that is left is to use whatever strategy you want for storing your images  
* Provide image to team and let them finish product specific configurations  
* Enjoy  

# Useful commands
* Remove all containers: `docker container rm $(docker container ls --filter status=exited -q)`
* Remove all images: `docker image rm $(docker image ls -q)`
