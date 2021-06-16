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
> ***Provide a self service solution that allows someone to build images with limited knowledge of docker and no hands on experience.***  

## Docker Compose
__Source__ - https://docs.docker.com/compose/  
__My interpretation__ - a way to orchestrate your images to build out a functional working environment.  
Which is great but not aligned to my objective.  

## Docker Multi-stage builds
__Source__ - https://docs.docker.com/develop/develop-images/multistage-build/  
__My interpretation__ - a way to coordinate build artifacts between images to maintain a slim final image.  
Which is great but not aligned to my objective.  

## Solution
Since I could not find what I wanted I decided to make it.  
The idea is similar to https://realpython.com/learning-paths/python-gui-programming/  
1. From a list of available items  
1. Create a docker file and build it  

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
1. Continue to add common tools and possibly allow more inputs for tool versions  

# Run
To get started install the following:  
* __Python 3__ - https://realpython.com/installing-python/  
* __PIP__ - https://pip.pypa.io/en/stable/installing/  
* __Modules__ - `pip install -r requirements.txt`  
* __Docker Environment__ - https://docs.docker.com/get-started/
  > During writing of this I used Windows 10 WSL 2 backend with Docker Desktop 3.4.0  

* __AWS Account__ - This is to create AWS Elastic Container Registry (ECR) to publish images to
* __Boto Profile__ - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

Then  
1. Update __inputs.properties__ file  
   Example: see committed file  
   __PARENT_NAME__ - follow the format of repository:tag  
   __SELECTED_ITEMS__ - comma delimited list of folders to include  
   __BUILD_DIRECTORY__ - name of folder to include docker artifacts to build from  
   __PROFILE_NAME__ - name of the boto profile that allows you to connect to AWS  
   __REPOSITORY_NAME__ - the name of the ECR repository to create or pull from  
   __APPLICATION_NAME__ - the name of the image to use during upload  
   __APPLICATTION_BASE_VERSION__ - a starting version in decimal format of [0-9].[0-9]  
   > Note the version is auto increased based on what is already uploaded to ECR  

1. Execute script `python3 build-it.py`  
1. Test image  
1. Upload to ECR `python3 build-it.py --upload=true`  
1. Check ECR for vulnerabilities  
   * Fix any found and re-upload image  

# Result
Now you have:  
* An organized folder list of items to customize with  
* An simple input file to customize the image with  
* The ability to create and improve while maintaining functional code with GitHub tags  
* Labels in docker files that provide any required detail and updates to changes  
* The ability to publish tested images into AWS ECR  

What is left:  
* Continue to include more items to install  
* Enjoy  

# Useful commands
__Cleanup__ - `docker system prune`
