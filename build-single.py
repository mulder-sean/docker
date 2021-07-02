import argparse
import datetime
from distutils.util import strtobool
import logging
from helpers.helpers import InputHelper, DockerHelper, EcrHelper, GitHelper

parser = argparse.ArgumentParser()
parser.add_argument('--upload', help='Boolean to determine if build should be published to registry')
parser.add_argument('--clone', help='Boolean to determine if code should be cloned')
arguments = parser.parse_args()
do_upload = False
clone = False
if arguments.upload:
    do_upload = strtobool(arguments.upload)
if arguments.clone:
    clone = strtobool(arguments.clone)

TYPE = 'build'
START = datetime.datetime.now()
logging.warning(f'Starting at {START}')
INPUTS = InputHelper('inputs.properties')
DOCKER_BUILD = DockerHelper(INPUTS)
DOCKER_BUILD.create_docker_file(TYPE)
GIT = GitHelper(INPUTS)
if clone:
    GIT.clone_git()
AWS_ECR = EcrHelper(INPUTS)
DOCKER_BUILD.set_repository_uri(AWS_ECR.get_repository_uri())
DOCKER_BUILD.set_application_version_next(AWS_ECR.get_application_version_next())
DOCKER_BUILD.set_docker_env(AWS_ECR.get_docker_env())
DOCKER_BUILD.set_network(AWS_ECR.get_network())
BUILD_TAG = DOCKER_BUILD.build_docker_image(TYPE)
if do_upload:
    AWS_ECR.registry_upload(BUILD_TAG)
END = datetime.datetime.now()
logging.warning(f'Completed at {END} in {END - START}')
