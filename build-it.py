import argparse
import datetime
from distutils.util import strtobool
import logging
from helpers.helpers import InputHelper, DockerHelper, EcrHelper

parser = argparse.ArgumentParser()
parser.add_argument('--upload', help='Push build to registry?')
arguments = parser.parse_args()
do_upload = False
if arguments.upload:
    do_upload = strtobool(arguments.upload)

START = datetime.datetime.now()
logging.warning(f'Starting at {START}')
INPUTS = InputHelper('inputs.properties')
DOCKER_FILE = DockerHelper(INPUTS)
DOCKER_FILE.build_docker_file()
AWS_ECR = EcrHelper(INPUTS)
if do_upload:
    AWS_ECR.registry_upload()
END = datetime.datetime.now()
logging.warning(f'Completed at {END} in {END - START}')
