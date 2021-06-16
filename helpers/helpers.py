import base64
import boto3
import docker
import logging
import os
import sys
import shutil
import configparser


class InputHelper:

    __config = configparser.RawConfigParser()
    __parent_image = None
    __selected_items = None
    __docker_directory = None
    __aws_profile_name = None
    __aws_repository_name = None
    __application_name = None
    __application_base_version = None

    def __init__(self, inputs_file_name):
        self.__config.read(inputs_file_name)
        self.__parent_image = self.__config.get('image', 'PARENT_NAME')
        self.__selected_items = self.__config.get('image', 'SELECTED_ITEMS')
        self.__docker_directory = self.__config.get('image', 'DOCKER_DIRECTORY')
        self.__aws_profile_name = self.__config.get('repository', 'PROFILE_NAME')
        self.__aws_repository_name = self.__config.get('repository', 'REPOSITORY_NAME')
        self.__application_name = self.__config.get('repository', 'APPLICATION_NAME')
        self.__application_base_version = self.__config.get('repository', 'APPLICATION_BASE_VERSION')

    def get_parent_image(self):
        return self.__parent_image

    def get_selected_items(self):
        return self.__selected_items

    def get_docker_directory(self):
        return self.__docker_directory

    def get_aws_profile_name(self):
        return self.__aws_profile_name

    def get_aws_repository_name(self):
        return self.__aws_repository_name

    def get_application_name(self):
        return self.__application_name

    def get_application_base_version(self):
        return self.__application_base_version


class DockerHelper:

    __parent_image = None
    __selected_items = None
    __docker_directory = None

    def __init__(self, input_helper):
        self.__parent_image = input_helper.get_parent_image()
        self.__selected_items = input_helper.get_selected_items()
        self.__docker_directory = input_helper.get_docker_directory()
        self.__reset_docker_folder__(self.__docker_directory)

    def build_docker_file(self):
        selected_items_list = self.__input_to_list__(self.__selected_items)
        new_docker_file = [f'FROM {self.__parent_image}\n']
        base_name = self.__get_base_name__(self.__parent_image)
        for selected_ in selected_items_list:
            working_directory = f'{os.getcwd()}{os.path.sep}{selected_}{os.path.sep}{base_name}'
            if self.__path_exists__(working_directory):
                working_directory_contents = self.__get_directory_contents__(working_directory)
                if working_directory_contents:
                    found_docker = False
                    for file_ in working_directory_contents:
                        if 'Dockerfile' in file_:
                            found_docker = True
                            logging.warning(f'Adding contents to docker from {file_}')
                            with open(file_, 'r') as in_:
                                in_lines = in_.readlines()
                                if in_lines:
                                    new_docker_file.extend(in_lines)
                                else:
                                    sys.exit(f'{file_} has no content.')
                        else:
                            shutil.copy(file_, f'{self.__docker_directory}{os.path.sep}')

                    if found_docker:
                        with open(f'{self.__docker_directory}{os.path.sep}Dockerfile', 'w') as out_:
                            out_.writelines(new_docker_file)

                    else:
                        sys.exit(f'{working_directory} is missing Dockerfile')

                else:
                    sys.exit(f'{working_directory} was empty')

        return new_docker_file

    @staticmethod
    def __get_base_name__(parent_image_):
        base_name_ = None
        if ':' in parent_image_:
            for index, piv in enumerate(parent_image_.split(':')):
                if index == 0:
                    base_name_ = piv.strip()

        return base_name_

    @staticmethod
    def __get_directory_contents__(working_directory_):
        found_contents = []
        for (root, dirs, files) in os.walk(working_directory_):
            items_ = [os.path.join(root, f_) for f_ in files]
            if items_:
                found_contents = items_

        return found_contents

    @staticmethod
    def __input_to_list__(comma_delimited_):
        list_ = []
        for item_ in comma_delimited_.split(','):
            list_.append(item_.strip())

        return list_

    @staticmethod
    def __path_exists__(path_):
        if os.path.exists(path_):
            return True
        else:
            sys.exit(f'{path_} did not exist.')

    @staticmethod
    def __reset_docker_folder__(build_):
        if os.path.exists(build_):
            shutil.rmtree(build_)

        os.mkdir(build_)


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
    __registry_build = None
    __image_tag = None

    def __init__(self, input_helper):
        self.__session = boto3.Session(profile_name=input_helper.get_aws_profile_name())
        self.__repository_name = input_helper.get_aws_repository_name()
        self.__application_name = input_helper.get_application_name()
        self.__docker_directory = input_helper.get_docker_directory()
        self.__application_version_base = round(float(input_helper.get_application_base_version()), 4)
        self.__application_version_current = round(float(input_helper.get_application_base_version()), 4)
        self.get_create_repository()
        self.registry_login()
        self.registry_prune()
        self.registry_get_latest()
        self.registry_build()

    def get_repository(self):
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
        repository_lookup = self.get_repository()
        if repository_lookup:
            logging.warning(f'Repository {self.__repository_name} existed')
            repository_info = repository_lookup
        else:
            logging.warning(f'Repository {self.__repository_name} created')
            repository_info = self.create_repository()

        return repository_info

    def registry_login(self):
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

    def registry_build(self):
        self.__image_tag = f'{self.__repository_uri}:{self.__application_name}-{self.__application_version_next}'
        logging.warning(f'Building image...{self.__image_tag}')
        self.__registry_build = self.__docker_env.images.build(
            path=self.__docker_directory,
            tag=self.__image_tag,
            labels={'Application': self.__application_name,
                    'ApplicationVersion': f'{round(self.__application_version_next, 4)}'}
        )

    def registry_upload(self):
        logging.warning(f'Pushing {self.__image_tag}')
        results = self.__docker_env.images.push(self.__image_tag)
        push_lines = results.split('\r\n')
        logging.warning(f'Pushing results: {push_lines[len(push_lines) - 2]}')

    def registry_get_latest(self):
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

        if ecr_images:
            for image in ecr_images:
                image_version = round(float(image.get('imageTag').replace(f'{self.__application_name}-', '')), 4)
                if image_version > self.__application_version_current:
                    self.__application_version_current = image_version

        if self.__application_version_current == self.__application_version_base:
            self.__application_version_next = round(float(self.__application_version_current), 4)
        else:
            self.__application_version_next = round(float(self.__application_version_current + 0.1), 4)

    def registry_prune(self):
        logging.warning(f'Cleaning up local repository')
        self.__docker_env.containers.prune()
        self.__docker_env.images.prune()
