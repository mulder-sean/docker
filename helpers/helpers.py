import base64
import boto3
import docker
import logging
import os
import sys
import shutil
import configparser
from git import Repo
from docker.errors import BuildError


class InputHelper:
    """
    Class to pull parameters from file and return values.
    """

    __config = None

    def __init__(self, inputs_file_name):
        self.__config = configparser.RawConfigParser()
        self.__config.read(inputs_file_name)

    def get_application(self, key):
        """
        Get parameter from application section
        :param key: string
        :return: string
        """
        return self.__config.get('application', key)

    def get_application_image(self, key):
        """
        Get parameter from application_image section
        :param key: string
        :return: string
        """
        return self.__config.get('application_image', key)

    def get_application_build(self, key):
        """
        Get parameter from application_build section
        :param key: string
        :return: string
        """
        return self.__config.get('application_build', key)

    def get_ecr_repository(self, key):
        """
        Get parameter from ecr_repository section
        :param key: string
        :return: string
        """
        return self.__config.get('ecr_repository', key)


class DockerHelper:

    __application_parent = None
    __application_items = None
    __application_directory = None
    __build_parent = None
    __build_items = None
    __build_directory = None
    __repository_uri = None
    __application_name = None
    __application_version_next = None
    __docker_env = None
    __git_url = None
    __git_branch = None
    __build_folder = None
    __exec_command = None
    __exec_options = None
    __build_artifacts = None
    __multi_build_folder = None
    __network = None
    __timezone = None

    def __init__(self, input_helper):
        self.__application_name = input_helper.get_application('NAME')
        self.__application_parent = input_helper.get_application_image('PARENT_NAME')
        self.__application_items = input_helper.get_application_image('SELECTED_ITEMS')
        self.__application_directory = input_helper.get_application_image('DIRECTORY')
        self.__build_parent = input_helper.get_application_build('PARENT_NAME')
        self.__build_items = input_helper.get_application_build('SELECTED_ITEMS')
        self.__build_directory = input_helper.get_application_build('DIRECTORY')
        self.__git_url = input_helper.get_application_build('URL')
        self.__git_branch = input_helper.get_application_build('BRANCH')
        self.__build_folder = input_helper.get_application_build('BUILD_FOLDER')
        self.__timezone = input_helper.get_application_image('TIMEZONE')
        self.__exec_command = input_helper.get_application_build('EXEC_COMMAND')
        self.__exec_options = input_helper.get_application_build('EXEC_OPTIONS')
        self.__build_artifacts = input_helper.get_application_build('ARTIFACTS')
        self.__multi_build_folder = input_helper.get_application_build('MULTI_DIRECTORY')
        self.__reset_docker_folder__(self.__multi_build_folder)
        self.__reset_docker_folder__(self.__build_directory)
        self.__reset_docker_folder__(self.__application_directory)

    def create_multi_docker_file(self):
        """
        Creates a single docker file that will use multi stage builds
        :return: list
        """
        new_docker_file = []
        current_directory = self.__multi_build_folder
        code_items = self.__input_to_list__(self.__build_items)
        app_items = self.__input_to_list__(self.__application_items)

        if self.__build_parent == self.__application_parent:
            base_name = self.__get_base_name__(self.__build_parent)

            if code_items:
                new_docker_file.append(f'FROM {self.__build_parent} as B\n')
                for ci in code_items:
                    working_directory = f'{os.getcwd()}{os.path.sep}{ci}{os.path.sep}{base_name}'
                    if self.__path_exists__(working_directory):
                        working_directory_contents = self.__get_directory_contents__(working_directory)
                        if working_directory_contents:
                            found_docker = False
                            for file_ in working_directory_contents:
                                if 'Dockerfile' in file_:
                                    found_docker = True
                                    logging.warning(f'Adding contents to {current_directory}/Dockerfile from {file_}')
                                    with open(file_, 'r') as in_:
                                        in_lines = in_.readlines()
                                        if in_lines:
                                            new_docker_file.extend(self.__update_tokens__(in_lines))
                                        else:
                                            sys.exit(f'{file_} has no content.')
                                else:
                                    shutil.copy(file_, f'{current_directory}{os.path.sep}')

                            if not found_docker:
                                sys.exit(f'{working_directory} is missing Dockerfile')

                        else:
                            sys.exit(f'{working_directory} was empty')

                new_docker_file.append('\n')

            if app_items:
                new_docker_file.append(f'FROM {self.__application_parent} as A\n')
                for ai in app_items:
                    working_directory = f'{os.getcwd()}{os.path.sep}{ai}{os.path.sep}{base_name}'
                    if self.__path_exists__(working_directory):
                        working_directory_contents = self.__get_directory_contents__(working_directory)
                        if working_directory_contents:
                            found_docker = False
                            for file_ in working_directory_contents:
                                if 'Dockerfile' in file_:
                                    found_docker = True
                                    logging.warning(f'Adding contents to {current_directory}/Dockerfile from {file_}')
                                    with open(file_, 'r') as in_:
                                        in_lines = in_.readlines()
                                        if in_lines:
                                            new_docker_file.extend(self.__update_tokens__(in_lines))
                                        else:
                                            sys.exit(f'{file_} has no content.')
                                else:
                                    shutil.copy(file_, f'{current_directory}{os.path.sep}')

                            if not found_docker:
                                sys.exit(f'{working_directory} is missing Dockerfile')

                        else:
                            sys.exit(f'{working_directory} was empty')

                new_docker_file.append('\n')
        else:
            sys.exit(f'You cannot build code with {self.__build_parent} '
                     f'and build application with {self.__application_parent} '
                     f'they have to be the same.')

        if new_docker_file:
            new_docker_file.append(f'COPY --from=B '
                                   f'/code/{self.__build_artifacts}/ /opt/code/ \n')
            with open(f'{current_directory}/Dockerfile', 'w') as out_:
                out_.writelines(new_docker_file)

        return new_docker_file

    def create_docker_file(self, image_type):
        """
        Create docker file in appropriate directory
        :param image_type: string only (application|build)
        :return: list
        """

        new_docker_file = []
        if image_type == 'application':
            current_name = self.__application_parent
            current_items = self.__application_items
            current_directory = self.__application_directory
            new_docker_file.append(f'FROM {current_name}\n')
        elif image_type == 'build':
            current_name = self.__build_parent
            current_items = self.__build_items
            current_directory = self.__build_directory
            new_docker_file.append(f'FROM {current_name}\n')
        else:
            sys.exit(f'You must only choose application or build for image_type')

        selected_items_list = self.__input_to_list__(current_items)
        base_name = self.__get_base_name__(current_name)
        for selected_ in selected_items_list:
            working_directory = f'{os.getcwd()}{os.path.sep}{selected_}{os.path.sep}{base_name}'
            if self.__path_exists__(working_directory):
                working_directory_contents = self.__get_directory_contents__(working_directory)
                if working_directory_contents:
                    found_docker = False
                    for file_ in working_directory_contents:
                        if 'Dockerfile' in file_:
                            found_docker = True
                            logging.warning(f'Adding contents to {current_directory}/Dockerfile from {file_}')
                            with open(file_, 'r') as in_:
                                in_lines = in_.readlines()
                                if in_lines:
                                    new_docker_file.extend(self.__update_tokens__(in_lines))
                                else:
                                    sys.exit(f'{file_} has no content.')
                        else:
                            shutil.copy(file_, f'{current_directory}{os.path.sep}')

                    if found_docker:
                        with open(f'{current_directory}{os.path.sep}Dockerfile', 'w') as out_:
                            out_.writelines(new_docker_file)

                    else:
                        sys.exit(f'{working_directory} is missing Dockerfile')

                else:
                    sys.exit(f'{working_directory} was empty')

        return new_docker_file

    def __update_tokens__(self, lines):
        """
        Replace any tokens in file
        :param lines: list
        :return: list
        """
        updated_lines = []
        for line in lines:
            if '@' in line:
                temp_line = line
                temp_line = temp_line.replace('@URL@', self.__git_url)
                temp_line = temp_line.replace('@BRANCH@', self.__git_branch)
                temp_line = temp_line.replace('@FOLDER@', self.__build_folder)
                temp_line = temp_line.replace('@TIMEZONE@', self.__timezone)
                if 'gradlew' in self.__exec_command:
                    temp_line = temp_line.replace('@EXEC@', f'/code/{self.__exec_command}')
                else:
                    temp_line = temp_line.replace('@EXEC@', {self.__exec_command})
                temp_line = temp_line.replace('@OPTS@', self.__exec_options)
                updated_lines.append(temp_line)
            else:
                updated_lines.append(line)

        return updated_lines

    def build_multi_docker_image(self):
        """
        Build the multi stage docker file and include artifacts from one build into final image
        without any of the build requirements
        :return: string
        """
        current_directory = self.__multi_build_folder
        image_tag = f'{self.__repository_uri}:{self.__application_name}-{self.__application_version_next}'
        logging.warning(f'Building {current_directory}/Dockerfile with tag {image_tag}')
        try:
            results = self.__docker_env.images.build(
                path=current_directory,
                tag=image_tag,
                quiet=False,
                labels={'Application': self.__application_name,
                        'ApplicationVersion': f'{round(self.__application_version_next, 4)}'},
                timeout=120,
                network_mode=self.__network.name,
            )
            logging.warning(f'Completed build of id {results[0].id}')
        except BuildError as be:
            bi = iter(be.build_log)
            while True:
                try:
                    i = next(bi)
                    logging.warning(i)
                except StopIteration:
                    break
            sys.exit(bi)

        return image_tag

    def build_docker_image(self, image_type):
        """
        Build the image using customized dockerfile
        :param image_type: string only (application|build)
        :return: string image_name
        """

        if image_type == 'application':
            current_directory = self.__application_directory
            image_tag = f'{self.__repository_uri}:{self.__application_name}-{self.__application_version_next}'
        elif image_type == 'build':
            current_directory = self.__build_directory
            image_tag = f'{self.__application_name}:{self.__application_version_next}'
        else:
            sys.exit(f'You must only choose application or build for image_type')

        logging.warning(f'Building {current_directory}/Dockerfile with tag {image_tag}')
        results = self.__docker_env.images.build(
            path=current_directory,
            tag=image_tag,
            quiet=False,
            labels={'Application': self.__application_name,
                    'ApplicationVersion': f'{round(self.__application_version_next, 4)}'}
        )
        logging.warning(f'Completed build of id {results[0].id}')
        return image_tag

    @staticmethod
    def __get_base_name__(parent_name_):
        """
        Get only base image name from tag by excluding anything after :
        :param parent_name_: string
        :return: string
        """
        base_name_ = None
        if ':' in parent_name_:
            for index, piv in enumerate(parent_name_.split(':')):
                if index == 0:
                    base_name_ = piv.strip()

        return base_name_

    @staticmethod
    def __get_directory_contents__(working_directory_):
        """
        Get all files in folder (includes subdirectories)
        :param working_directory_: string
        :return: list
        """
        found_contents = []
        for (root, dirs, files) in os.walk(working_directory_):
            items_ = [os.path.join(root, f_) for f_ in files]
            if items_:
                found_contents = items_

        return found_contents

    @staticmethod
    def __input_to_list__(comma_delimited_):
        """
        Convert comma delimited string into a list while removing spaces
        :param comma_delimited_:
        :return: list
        """
        list_ = []
        for item_ in comma_delimited_.split(','):
            list_.append(item_.strip())

        return list_

    @staticmethod
    def __path_exists__(path_):
        """
        Check of directory exists and return true or stop execution as all directories should exist
        :param path_: string
        :return: bool
        """
        if os.path.exists(path_):
            return True
        else:
            sys.exit(f'{path_} did not exist.')

    @staticmethod
    def __reset_docker_folder__(build_):
        """
        Remove directories before starting work to ensure its only what we want
        :param build_: string
        :return: None
        """
        if os.path.exists(build_):
            os.system(f'rm -rf {build_}')  # Does not work in windows
            # shutil.rmtree(build_)

        os.mkdir(build_)

    def set_repository_uri(self, uri):
        self.__repository_uri = uri

    def set_application_version_next(self, application_next):
        self.__application_version_next = application_next

    def set_docker_env(self, docker_env):
        self.__docker_env = docker_env

    def set_network(self, network):
        self.__network = network


class EcrHelper:

    __session = None
    __repository_name = None
    __registry_id = None
    __repository_uri = None
    __docker_env = None
    __application_name = None
    __application_version_base = None
    __application_version_current = None
    __application_version_next = None
    __docker_directory = None
    __network = None
    __network_name = None

    def __init__(self, input_helper):
        self.__session = boto3.Session(profile_name=input_helper.get_ecr_repository('PROFILE_NAME'))
        self.__repository_name = input_helper.get_ecr_repository('NAME')
        self.__application_name = input_helper.get_application('NAME')
        self.__docker_directory = input_helper.get_application_image('DIRECTORY')
        self.__network_name = input_helper.get_application_image('NETWORK_NAME')
        self.__application_version_base = round(float(input_helper.get_application('BASE_VERSION')), 4)
        self.__application_version_current = round(float(input_helper.get_application('BASE_VERSION')), 4)
        self.get_create_repository()
        self.registry_login()
        self.registry_prune()
        self.registry_get_latest()
        self.__create_my_network__()

    def get_repository(self):
        """
        Get ecr repository from AWS
        :return: dict
        """
        found_repository = {}
        results = self.__session.client('ecr').describe_repositories()
        if results.get('repositories'):
            if len(results.get('repositories')) > 1:
                sys.exit(f'Something wrong found multiple {self.__repository_name}: {results.get("repositories")}')
            else:
                found_repository = results.get('repositories')[-1]
                if results.get('repositories')[-1].get('registryId'):
                    self.__registry_id = results.get('repositories')[-1].get('registryId')
                    self.__repository_uri = results.get('repositories')[-1].get('repositoryUri')

        return found_repository

    def get_repositories(self):
        """
        Get ecr repositories from AWS
        :return: list of dict
        """
        found_repositories = []
        keep_searching = True
        next_token = None
        while keep_searching:
            if next_token:
                results = self.__session.client('ecr').describe_repositories(nextToken=next_token)
            else:
                results = self.__session.client('ecr').describe_repositories()

            if results:
                if results.get('nextToken'):
                    next_token = results.get('nextToken')
                else:
                    keep_searching = False

                if results.get('repositories'):
                    found_repositories.extend(results.get('repositories'))

        return found_repositories

    def create_repository(self):
        """
        Create ecr repository in AWS
        :return: dict
        """
        new_repository = {}
        results = self.__session.client('ecr').create_repository(
            repositoryName=self.__repository_name,
            imageScanningConfiguration={
                'scanOnPush': True
            },
            imageTagMutability='IMMUTABLE',
            encryptionConfiguration={
                'encryptionType': 'AES256'
            }
        )
        if results.get('repository'):
            new_repository = results.get('repository')
            if results.get('repository').get('registryId'):
                self.__registry_id = results.get('repository').get('registryId')
                self.__repository_uri = results.get('repository').get('repositoryUri')

        return new_repository

    def get_create_repository(self):
        """
        Get repository from ecr and if missing or not found create it
        :return: dict
        """
        repository_lookup = self.get_repository()
        if repository_lookup:
            logging.warning(f'Repository {self.__repository_name} existed')
            repository_info = repository_lookup
        else:
            logging.warning(f'Repository {self.__repository_name} created')
            repository_info = self.create_repository()

        return repository_info

    def registry_login(self):
        """
        Log into ecr repository in aws
        :return: None
        """
        logging.warning(f'Logging into registry {self.__repository_uri}')
        if self.__registry_id:
            auth_request = self.__session.client('ecr').get_authorization_token(
                registryIds=[self.__registry_id])
            if auth_request.get('authorizationData'):
                for auth_data in auth_request.get('authorizationData'):
                    if auth_data.get('authorizationToken'):
                        auth_token = auth_data.get('authorizationToken')
                        auth_list = base64.b64decode(auth_token).decode('utf-8').split(':')
                        auth_endpoint = auth_data.get('proxyEndpoint')
                        self.__docker_env = docker.from_env()
                        self.__docker_env.login(username=auth_list[0], password=auth_list[1], registry=auth_endpoint)

    def __create_my_network__(self):
        """
        Create a local bridge docker network for the image to utilize.
        Without this issues with downloads and DNS lookups kept happening.
        :return: network
        """
        self.__network = self.__docker_env.networks.create(
            name=self.__network_name,
            driver='bridge',
            internal=False,
            scope='local',
            enable_ipv6=False,
        )

    def registry_upload(self, image_name):
        """
        Upload image to the ERC registry
        :param image_name: string
        :return: None
        """
        logging.warning(f'Pushing {image_name}')
        results = self.__docker_env.images.push(image_name)
        push_lines = results.split('\r\n')
        logging.warning(f'Pushing results: {push_lines[len(push_lines) - 2]}')

    def registry_get_latest(self):
        """
        Set the next value based on search of ecr repository
        :return: None
        """
        ecr_images = []
        ecr_keep_searching = True
        ecr_next_token = None
        logging.warning(f'Fetching images from {self.__repository_name}')
        while ecr_keep_searching:
            if ecr_next_token:
                results = self.__session.client('ecr').list_images(
                    repositoryName=self.__repository_name,
                    nextToken=ecr_next_token
                )
            else:
                results = self.__session.client('ecr').list_images(
                    repositoryName=self.__repository_name
                )

            if results.get('nextToken'):
                ecr_next_token = results.get('nextToken')
            else:
                ecr_keep_searching = False

            if results.get('imageIds'):
                ecr_images.extend(results.get('imageIds'))

        use_base = True
        if ecr_images:
            for image in ecr_images:
                image_version = round(float(image.get('imageTag').split('-')[-1]), 4)
                if image_version >= self.__application_version_current:
                    self.__application_version_current = image_version
                    use_base = False

        if self.__application_version_current == self.__application_version_base and use_base:
            self.__application_version_next = round(float(self.__application_version_current), 4)
        else:
            self.__application_version_next = round(float(self.__application_version_current + 0.1), 4)

    def registry_prune(self):
        """
        Remove any local docker containers, images, networks to prevent cache issues.
        :return: None
        """
        logging.warning(f'Cleaning up local repository')
        self.__docker_env.containers.prune()
        self.__docker_env.images.prune()
        self.__docker_env.networks.prune()

    def get_repository_uri(self):
        return self.__repository_uri

    def get_application_version_next(self):
        return self.__application_version_next

    def get_docker_env(self):
        return self.__docker_env

    def get_network(self):
        return self.__network


class GitHelper:

    __url = None
    __git_folder = None
    __repo = None
    __branch = None

    def __init__(self, input_helper):
        self.__url = input_helper.get_application_build('URL')
        self.__git_folder = f'{input_helper.get_application_build("MULTI_DIRECTORY")}{os.path.sep}code'
        self.__reset_git_folder__(self.__git_folder)
        self.__branch = input_helper.get_application_build('BRANCH')

    @staticmethod
    def __reset_git_folder__(build_):
        """
        Delete directory and all its contents then create directory to start fresh
        :param build_: string
        :return: None
        """
        if os.path.exists(build_):
            os.system(f'rm -rf {build_}')  # Prob fails on Windows when not using GIT overrides

        os.mkdir(build_)

    def clone_git(self):
        """
        Checkout code into local directory
        :return: repo
        """
        logging.warning(f'Cloning from {self.__url} branch {self.__branch} into {self.__git_folder}')
        return Repo.clone_from(self.__url,
                               self.__git_folder,
                               depth=1,
                               branch=self.__branch)

    def __switch_branch__(self):
        """
        If full clone is done you can switch to another branch with this
        :return: None
        """
        self.__repo.git.checkout(self.__branch)
