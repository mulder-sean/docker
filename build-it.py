import configparser
import datetime
import logging
import os
import shutil
import sys


def get_base_name(parent_image_):
    base_name_ = None
    if ':' in parent_image_:
        for index, piv in enumerate(parent_image_.split(':')):
            if index == 0:
                base_name_ = piv.strip()

    return base_name_


def get_directory_contents(working_directory_):
    found_contents = []
    for (root, dirs, files) in os.walk(working_directory_):
        items_ = [os.path.join(root, f_) for f_ in files]
        if items_:
            found_contents = items_

    return found_contents


def init(build_):
    if os.path.exists(build_):
        shutil.rmtree(build_)

    os.mkdir(build_)


def input_to_list(comma_delimited_):
    list_ = []
    for item_ in comma_delimited_.split(','):
        list_.append(item_.strip())

    return list_


def path_exists(path_):
    if os.path.exists(path_):
        return True
    else:
        sys.exit(f'{path_} did not exist.')


START = datetime.datetime.now()
logging.warning(f'Starting at {START}')
OUTPUT_DIRECTORY = 'build'
init(OUTPUT_DIRECTORY)
CONFIG = configparser.RawConfigParser()
CONFIG.read('inputs.properties')
PARENT_IMAGE = CONFIG.get('image', 'PARENT_NAME')
SELECTED_ITEMS = CONFIG.get('image', 'SELECTED_ITEMS')
SELECTED_ITEMS_LIST = input_to_list(SELECTED_ITEMS)
BASE_NAME = get_base_name(PARENT_IMAGE)
DOCKER_FILE_CONTENTS = [f'FROM {PARENT_IMAGE}\n']

for selected_ in SELECTED_ITEMS_LIST:
    working_directory = f'{os.getcwd()}{os.path.sep}{selected_}{os.path.sep}{BASE_NAME}'
    if path_exists(working_directory):
        working_directory_contents = get_directory_contents(working_directory)
        if working_directory_contents:
            found_docker = False
            for file_ in working_directory_contents:
                if 'Dockerfile' in file_:
                    found_docker = True
                    logging.warning(f'Adding contents to docker from {file_}')
                    with open(file_, 'r') as in_:
                        in_lines = in_.readlines()
                        if in_lines:
                            DOCKER_FILE_CONTENTS.extend(in_lines)
                        else:
                            sys.exit(f'{file_} has no content.')
                else:
                    shutil.copy(file_, f'{OUTPUT_DIRECTORY}{os.path.sep}')

            if found_docker:
                with open(f'{OUTPUT_DIRECTORY}{os.path.sep}Dockerfile', 'w') as out_:
                    out_.writelines(DOCKER_FILE_CONTENTS)

            else:
                sys.exit(f'{working_directory} is missing Dockerfile')

        else:
            sys.exit(f'{working_directory} was empty')

END = datetime.datetime.now()
logging.warning(f'Completed at {END} in {END - START}')
