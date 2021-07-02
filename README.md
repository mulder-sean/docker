# Overview

I was looking for a way to provide a docker image for development teams with the following in mind:  
* Consistent  
* Repeatable  
* Customizable  
* Simple  
* Secure  

All of this with my personal objective of:  
> ***Provide a self-service solution that allows someone to build images with limited knowledge of docker and no hand's on experience.***  

## Docker Compose
__Source__ - https://docs.docker.com/compose/  
__My interpretation__ - a way to orchestrate your images to build out a functional working environment.  
Which is great, but I don't have a need for this just yet.  

## Docker Multi-stage builds
__Source__ - https://docs.docker.com/develop/develop-images/multistage-build/  
__My interpretation__ - a way to coordinate build artifacts between images to maintain a slim final image.  
Which is perfect for part of my solution.  

## Solution
I could not find all that I wanted in a single solution, so I decided to build one.  
The idea is similar to https://realpython.com/learning-paths/python-gui-programming/  
1. Update configuration file, picking and choosing from available list of items  
1. Build multistage docker file from selections  
1. Build images  
1. Publish image to ECR for service deployment  

## Check list
In order to achieve my solution I had to consider:  
* How to organize the list of items to select  
* How to pull the selected items into a docker file  
* How to provide clean simple interaction for items  
* How to handle versioning  
* How to document and track changes  

## Decisions
1. __Language__ - I chose Python 3, but could have been done in any language  
1. __Versioning__ - To reduce complication I chose GitHub tags and ECR naming conventions  
1. __Organize__ - I chose to use folders:  
   * allows inclusion of additional static files  
   * allows various base images  
   * allows for documentation notes which are not included in images  

## Improvements
1. Creating a GUI interface with choices to pick and choose instead of text file  
1. Continue to add folders for various components  

# Run
To get started install the following:  
* __Python 3__ - https://realpython.com/installing-python/  
* __PIP__ - https://pip.pypa.io/en/stable/installing/  
* __Modules__ - `pip install -r requirements.txt`  
* __Docker Environment__ - https://docs.docker.com/get-started/  
  > During writing of this I used Windows 10 WSL 2 backend with Docker Desktop 3.5.1  

* __AWS Account__ - This is to create AWS Elastic Container Registry (ECR) to publish images to  
* __Boto Profile__ - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html  

Then
1. Update __inputs.properties__ file  
   > See committed file for examples and input details.  
1. Execute script:  
   > __WARNING__ do not run two builds at the same time as it will fail  
   * Multi Stage Builds: `python3 build-multi.py`  
   * Single Stage Builds: `python3 build-single.py`  
     * Primarily used for testing out new items  
     * Defaults to the inputs for __application_build__  
     * Has additional option __--clone__ that will perform a git clone to include in build  
1. Test image  
1. Upload to ECR: `python3 build-multi.py --upload=true`  
1. Check ECR for vulnerabilities  
   * Fix any found and rebuild and re-upload image  

# Result
Now I have:  
* An organized folder list of items to choose from  
* A simple input file to modify for customization  
  * Enabling anyone to build images with no operating system skills  
* Labels in docker files that provide any required detail and updates to changes  
* The ability to publish tested images into AWS ECR  

# Useful commands
__Cleanup__ - `docker system prune -a`
