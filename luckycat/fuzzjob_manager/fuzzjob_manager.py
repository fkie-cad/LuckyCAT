import logging.config
import os
import argparse
import sys
import json
import base64
import requests
from urllib.parse import urljoin

logging.config.fileConfig("../logging.conf")
logging = logging.getLogger(os.path.basename(__file__).split(".")[0])


def query_yes_no(question, default="yes"):
    # taken from http://code.activestate.com/recipes/577058/
    # MIT license
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def create_job(args, token):
    # TODO: check if all arguments are provided
    if args.test_cases is None or args.fuzzing_target is None:
        logging.error("Not test cases or fuzzing target provided.")
        sys.exit(1)
    test_cases = open(args.test_cases, 'rb').read()
    fuzzing_target = open(args.fuzzing_target, 'rb').read()

    logging.info('Creating fuzz job %s with the following parameters:' % args.name)
    logging.info('\tdescription: %s' % args.description)
    logging.info('\tmaximum_samples: %s' % args.maximum_samples)
    logging.info('\tmaximum_iteration: %s' % args.maximum_iteration)
    logging.info('\tmutation_engine: %s' % args.mutation_engine)
    logging.info('\tfuzzer: %s' % args.fuzzer)
    logging.info('\ttest cases size: %i bytes' % len(test_cases))
    logging.info('\tfuzzing target cases size: %i bytes' % len(fuzzing_target))

    if not args.yes:
        res = query_yes_no('Is this correct?')
        if not res:
            logging.info('Creation aborted...')
            sys.exit(1)

    json_doc = {'name': args.name,
                'description': args.description,
                'maximum_samples': args.maximum_samples,
                'maximum_iteration': args.maximum_iteration,
                'timeout': args.timeout,
                'mutation_engine': args.mutation_engine,
                'fuzzer': args.fuzzer,
                'samples': base64.b64encode(test_cases),
                'fuzzing_target': base64.b64encode(fuzzing_target),
                }
    url = urljoin(args.url, "/api/job")
    response = requests.put(url,
                            json=json_doc,
                            headers={'Authentication-Token': token,
                                     'content-type': 'application/json'})
    if response.status_code != 200 or not response.json()['success']:
        logging.error("Could not create fuzzing job: %s" % response.text)
    else:
        print(response.text)
        logging.info("Created fuzzing job.")


def find_job_id_by_name(args, token):
    url = urljoin(args.url, "/api/jobs")
    response = requests.get(url, headers={'Authentication-Token': token,
                                          'content-type': 'application/json'})
    if response.status_code != 200:
        logging.error("Could not list jobs.")
    else:
        job_id = None
        for job in response.json():
            if job['name'] == args.name:
                job_id = job['job_id']
        return job_id


def print_job_info(job):
    print('\tname: %s' % job['name'])
    print('\tID: %s' % job['job_id'])
    print('\tdescription: %s' % job['description'])
    print('\tmaximum_samples: %s' % job['maximum_samples'])
    print('\tmaximum_iteration: %s' % job['maximum_iteration'])
    print('\tmutation_engine: %s' % job['mutation_engine'])
    print('\tfuzzer: %s' % job['fuzzer'])


def delete_job(args, token):
    if args.name is None:
        logging.error("Please provide a valid name of a job.")
    else:

        if not query_yes_no("Do you want to delete the job %s?" % args.name):
            logging.error("Aborting...")
            sys.exit(1)

        job_id = find_job_id_by_name(args, token)
        if job_id:
            url = "http://localhost:5000/api/job/%s" % job_id
            response = requests.delete(url, headers={'Authentication-Token': token,
                                                     'content-type': 'application/json'})
            if response.status_code != 200:
                logging.error("Could not delete job %s." % args.name)
            else:
                logging.info("Deleted job %s." % args.name)
        else:
            logging.error("Could not find job %s." % args.name)


def list_jobs(args, token):
    if args.name:
        url = urljoin(args.url, "/api/job/%s" % args.name)
        response = requests.get(url, headers={'Authentication-Token': token,
                                              'content-type': 'application/json'})
        if response.status_code != 200:
            logging.error("Could not list fuzz job %s: %d." % (args.name, response.status_code))
        else:
            if 'name' in response.json():
                print_job_info(response.json())
            else:
                logging.error('No job with name %s known.' % args.name)
    else:
        url = urljoin(args.url, "/api/jobs")
        response = requests.get(url, headers={'Authentication-Token': token,
                                              'content-type': 'application/json'})
        if response.status_code != 200:
            logging.error("Could not list jobs: %s" % response.text)
        else:
            for job in response.json():
                print_job_info(job)
                print("-" * 80)


def get_user_authentication_token(url, user, password):
    url = urljoin(url, '/login')
    r = requests.post(url,
                      data=json.dumps({'email': user, 'password': password}),
                      headers={'content-type': 'application/json'})
    j = r.json()
    if 'response' in j and 'user' in j['response'] and 'authentication_token' in j['response']['user']:
        return j['response']['user']['authentication_token']
    else:
        logging.error("Could not aquire authentication token: %s" % j)
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage fuzzing jobs from the command line')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', dest='create', action="store_true", default=False,
                       help='Create a fuzz job')
    group.add_argument('-d', dest='delete', action="store_true", default=False,
                       help='Delete a fuzz job')
    group.add_argument('-l', dest='list', action="store_true", default=False,
                       help='List fuzz jobs')

    # arguments for creation of fuzz job
    parser.add_argument('--name', type=str, help='Name of the fuzz job')
    parser.add_argument('--description', type=str, default='', help='Description of the fuzz job')
    parser.add_argument('--mutation-engine', choices=['radamsa', 'urandom'], help='Mutation engine to generate test cases', default='radamsa')
    parser.add_argument('--fuzzer', choices=['cfuzz', 'afl'],
                        help='Fuzzer to test target with', default='cfuzz')
    parser.add_argument('--maximum-samples', dest='maximum_samples', type=int, default=4,
                        help='Maximum number of test cases to generate at once')
    parser.add_argument('--maximum-iteration', type=int, dest='maximum_iteration',
                        default=1000000, help='Maximum number of fuzz iterations')
    parser.add_argument('--timeout', type=int, dest='timeout',
                        default=0, help='Disable fuzzing job after timeout. Default: 0 == None.')
    parser.add_argument('--test-cases', type=str, help='One or several test cases (as zip file) for fuzzing.')
    parser.add_argument('--fuzzing-target', type=str, help='Fuzzing target for fuzzing.')

    # arguments for deletion of fuzz job
    parser.add_argument('--id', type=str, help='ID of fuzz job to delete')

    # arguments for fuzz job listing
    parser.add_argument('--active', action='store_true', help='List only active fuzz jobs')
    parser.add_argument('--archived', action='store_true', help='List only archived fuzz jobs')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--yes', action='store_true', help='Answer all questions with yes')

    parser.add_argument('--user', required=True, type=str, help='Username')
    parser.add_argument('--password', required=True, type=str, help='Password')
    parser.add_argument('--url', type=str, default="http://localhost:5000", help='URL')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    token = get_user_authentication_token(args.url, args.user, args.password)

    if args.create:
        create_job(args, token)
    elif args.delete:
        delete_job(args, token)
    else:
        list_jobs(args, token)


if __name__ == "__main__":
    main()
