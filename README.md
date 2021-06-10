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
__Source__ - https://docs.docker.com/compose/  
__My interpretation__ - a way to orchestrate your images to build out a functional working environment.  
Which is great but not aligned to my objective.  

## Docker Multi-stage builds
__Source__ - https://docs.docker.com/develop/develop-images/multistage-build/  
__My interpretation__ - a way to coordinate build artifacts between images to maintain a slim final image.  
Which is great but not aligned to my objective.  

# Solution
Since I could not find what I wanted I decided to make it.  
> Provide a collection of individual docker commands which can be combined into a single file.  

Idea similar to https://realpython.com/learning-paths/python-gui-programming/  
1. From a list of available items  
1. Drop into file and build it  

## Check list
In order to achieve my solution I have to consider:  
* How to organize the list of items to select  
* How to pull the selected items into a docker file  
* How to provide clean simple interaction for items  
* How to provide tagging and versioning information  
* How to handle versioning for items  
* How to notify versioning changes for items  

## Decisions
1. __Language__ - I chose Python 3, but could have been done in any language  
1. __Versioning__ - To reduce complication I chose GitHub tags  
1. __Organize__ - I chose to use folders to allow for additional artifacts to be included  

## Improvements
1. Creating a GUI interface with choices to pick and choose instead of text file  
1. Build into the script the docker commands to build and tag based on additional inputs  
1. Continue to add common tools and possibly allow more inputs for tool versions  

# Run
To get started install the following:  
* __Python 3__ - https://realpython.com/installing-python/  
* __PIP__ - https://pip.pypa.io/en/stable/installing/  
* __Modules__ - `pip install -r requirements.txt`  

Then  
1. Update __inputs.properties__ file  
   ```  
   [image]  
   PARENT_NAME=image identity that will be used as base  
   SELECTED_ITEMS=comma delimited list of items  
   ```  
1. Execute script `python3 build-it.py`  
1. Build docker image: `docker build build`  
1. Test image  
1. Tag image  
1. Upload to your favorite repository  

# Result
Now you have:  
* An organized folder list of items to customize with  
* An simple input file to customize the image with  
* The ability to create and improve while maintaining functional code with GitHub tags  
* Labels in docker files that provide any required detail and updates to changes  

What is left:  
* All that is left is to use whatever strategy required to label and store images  
* Notify development teams on how to pull image and finish product specific customizations  
* Enjoy  

# Useful commands
__Remove all containers__ `docker container rm $(docker container ls --filter status=exited -q)`  
__Remove all images__ `docker image rm $(docker image ls -q)`  
