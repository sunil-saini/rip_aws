import os
import json
import logging.config
from services import aws
from configparser import RawConfigParser
from services.host import host_data, project

logger = logging.getLogger(__name__)
host = host_data()


def start_logging(default_level=logging.INFO):
    path = host['resources']+"logging.json"
    if os.path.exists(path):
        with open(path, 'rt') as log_f:
            config = json.load(log_f)
            handler = config['handlers']
            prefix_path = host['store'] + "logs/"

            log_file_handlers = ['info_file_handler', 'debug_file_handler', 'error_file_handler']

            for log_file_handler in log_file_handlers:
                handler[log_file_handler]['filename'] = prefix_path + handler[log_file_handler]['filename']

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


start_logging()


def properties_config_parser():
    prop_file_path = host['resources']+"commands.properties"
    parser = RawConfigParser()
    parser.read(prop_file_path)
    return parser


def check_file_exists(file_path):
    return os.path.isfile(file_path)


def write_string_to_file(filename, string):
    fp = open(filename, 'w')
    fp.write(string)
    fp.close()
    logger.info("file %s updated successfully" % filename)


def service_function_mapping(s):
    mapping = {
        "ec2": aws.ec2,
        "s3": aws.s3,
        "lambdas": aws.lambdas,
        "ssm_parameters": aws.ssm_parameters,
        "route53": aws.hosted_zones,
        "lb": aws.load_balancers,
        "cloudfront": aws.cloud_fronts
    }

    return mapping[s]


def source_alias_functions(file_to_source):

    if host['os'] == "darwin" and host['shell'] == "/bin/bash":
        profile_file = host['home'] + "/.bash_profile"
    else:
        profile_file = host['home'] + "/." + host['shell'].split("/")[-1] + "rc"

    line_to_append = "\n# added by "+project+"\nsource "+file_to_source+"\n"

    fp = open(profile_file, 'a+')
    fp.seek(0)
    file_content = fp.read()

    if line_to_append not in file_content:
        fp.write(line_to_append)
        fp.close()
        logger.info("file %s updated successfully" % profile_file)


def services_suffix(service_for):
    suffixes = {
        "ec2": "instances",
        "s3": "buckets",
        "route53": "hosted zones",
        "cloudfront": "distributions"
    }
    return suffixes.get(service_for, None)


def read_project_current_commands():
    read_parser = properties_config_parser()
    print("\n---------------------------------------------------------------------\n")
    for sec in read_parser.sections():
        for item in read_parser.items(sec):
            suffix = services_suffix(sec)
            description = item[0].split("_")[0].title() + " " + sec
            if suffix:
                description += " " + suffix
            print("%s -\t%s" % (description.ljust(35), item[1]))
    print("\n%s -\t%s" % ("List commands".ljust(35), "awss"))
    print("%s -\t%s" % ("Rename commands".ljust(35), "awss configure\n"))
    print("%s -\t%s" % ("Fetch latest data from AWS".ljust(35), "awss update"))
    print("%s -\t%s" % ("Update project to latest version".ljust(35), "awss upgrade\n"))
    print("\n---------------------------------------------------------------------\n")


def configure_project_commands():
    logger.info("Started configuring project commands...")
    read_parser = properties_config_parser()
    write_parser = RawConfigParser()

    try:
        input_method = raw_input
    except NameError:
        input_method = input

    need_to_rename = False

    for sec in read_parser.sections():
        write_parser.add_section(sec)
        for item in read_parser.items(sec):
            suffix = services_suffix(sec)
            description = item[0].split("_")[0].title() + " " + sec
            if suffix:
                description += " " + suffix
            description += " [ Current - " + item[1] + " ]: "
            cmd = input_method(description)
            if cmd:
                write_parser.set(sec, item[0], cmd)
                need_to_rename = True
            else:
                write_parser.set(sec, item[0], item[1])

    if need_to_rename:
        properties_file = host['resources']+"commands.properties"
        with open(properties_file, 'w') as configfile:
            write_parser.write(configfile)
        print("\nCommand(s) renamed successfully\n")

    logger.info("commands configured successfully")


def create_alias_functions():
    logger.info("Creating alias functions...")
    parser = properties_config_parser()

    awss_vars = [project]

    for service in parser.sections():
        list_cmd = parser[service].get('list_command')
        get_cmd = parser[service].get('get_command', None)

        awss_vars.append(list_cmd)
        awss_vars.append(service)

        if get_cmd:
            awss_vars.append(get_cmd)

    params_to_pass = ' '.join(awss_vars)
    aliases_sh = "bash +x "+host['scripts']+"aliases.sh"
    cmd = aliases_sh + " " + params_to_pass
    logger.info("command - %s" % cmd)
    os.system(cmd)


def merge_properties_file():
    new_parser = properties_config_parser()
    old_prop_file_path = host['resources']+"commands.properties.bak"
    old_parser = RawConfigParser()
    old_parser.read(old_prop_file_path)

    current_parser = RawConfigParser()

    for sec in new_parser.sections():
        current_parser.add_section(sec)
        for key, value in new_parser.items(sec):
            if old_parser.has_option(sec, key):
                current_parser.set(sec, key, old_parser[sec].get(key))
            else:
                current_parser.set(sec, key, value)

    properties_file = host['resources'] + "commands.properties"
    with open(properties_file, 'w') as configfile:
        current_parser.write(configfile)
