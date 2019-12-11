import argparse
import base64
import logging.config
import sys
from urllib.parse import urljoin

import requests

logger = logging.getLogger('fuzzjob_manager')
logger.setLevel(logging.INFO)


def query_yes_no(question, default='yes'):
    # taken from http://code.activestate.com/recipes/577058/
    # MIT license
    '''Ask a yes/no question via raw_input() and return their answer.

    'question' is a string that is presented to the user.
    'default' is the presumed answer if the user just hits <Enter>.
        It must be 'yes' (the default), 'no' or None (meaning
        an answer is required of the user).

    The 'answer' return value is True for 'yes' or False for 'no'.
    '''
    valid = {'yes': True, 'y': True, 'ye': True,
             'no': False, 'n': False}
    if default is None:
        prompt = ' [y/n] '
    elif default == 'yes':
        prompt = ' [Y/n] '
    elif default == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError(f'invalid default answer: \'{default}\'')

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write('Please respond with \'yes\' or \'no\' '
                             '(or \'y\' or \'n\').\n')


def create_job(args):
    # TODO: check if all arguments are provided
    if args.test_cases is None or args.fuzzing_target is None:
        logger.error('Not test cases or fuzzing target provided.')
        sys.exit(1)
    test_cases = open(args.test_cases, 'rb').read()
    fuzzing_target = open(args.fuzzing_target, 'rb').read()

    print(f'Creating fuzz job {args.name} with the following parameters:')
    print(f'\tdescription: {args.description}')
    print(f'\tmaximum_samples: {args.maximum_samples}')
    print(f'\tmaximum_iteration: {args.maximum_iteration}')
    print(f'\tmutation_engine: {args.mutation_engine}')
    print(f'\tfuzzer: {args.fuzzer}')
    print(f'\tverifier: {args.verifier}')
    print(f'\tcommand line arguments: {args.cmd_args}')
    print(f'\ttest cases size: {len(test_cases)} bytes')
    print(f'\tfuzzing target size: {len(fuzzing_target)} bytes')

    if not args.yes:
        res = query_yes_no('Is this correct?')
        if not res:
            logger.info('Creation aborted...')
            sys.exit(1)

    json_doc = {'name': args.name,
                'description': args.description,
                'maximum_samples': args.maximum_samples,
                'maximum_iteration': args.maximum_iteration,
                'timeout': args.timeout,
                'mutation_engine': args.mutation_engine,
                'fuzzer': args.fuzzer,
                'verifier': args.verifier,
                'cmd_args': args.cmd_args,
                'samples': base64.b64encode(test_cases),
                'fuzzing_target': base64.b64encode(fuzzing_target),
                }
    url = urljoin(args.url, '/api/job')
    response = requests.put(url,
                            json=json_doc,
                            headers={'Authorization': args.token,
                                     'content-type': 'application/json'},
                            verify=args.ssl_verify)
    if response.status_code != 200 or not response.json()['success']:
        logger.error(f'Could not create fuzzing job: {response.text}')
    else:
        print(response.text)
        logger.info('Created fuzzing job.')


def find_job_id_by_name(args):
    url = urljoin(args.url, '/api/jobs')
    response = requests.get(url, headers={'Authorization': args.token,
                                          'content-type': 'application/json'},
                            verify=args.ssl_verify)
    if response.status_code != 200:
        logger.error('Could not list jobs.')
    else:
        job_id = None
        for job in response.json():
            if job['name'] == args.name:
                job_id = job['job_id']
        return job_id


def print_job_info(job):
    print(f"\tname: {job['name']}")
    print(f"\tID: {job['job_id']}")
    print(f"\tdescription: {job['description']}")
    print(f"\tarchived: {job['archived']}")
    print(f"\tenabled: {job['enabled']}'")
    print(f"\tmaximum_samples: {job['maximum_samples']}")
    print(f"\tmaximum_iteration: {job['maximum_iteration']}")
    print(f"\tfuzzer: {job['fuzzer']}")
    print(f"\tmutation_engine: {job['mutation_engine']}")
    print(f"\tverifier: {job['verifier']}")
    print(f"\tcommand line arguments: {job['cmd_args']}")


def delete_job(args):
    if args.name is None:
        logger.error('Please provide a valid name of a job.')
    else:

        if not query_yes_no(f'Do you want to delete the job {args.name}?'):
            logger.error('Aborting...')
            sys.exit(1)

        job_id = find_job_id_by_name(args)
        if job_id:
            url = urljoin(args.url, f'/api/job/{job_id}')
            response = requests.delete(url, headers={'Authorization': args.token,
                                                     'content-type': 'application/json'},
                                       verify=args.ssl_verify)
            if response.status_code != 200:
                logging.error(f'Could not delete job {args.name}: {response.text}')
            else:
                logging.info(f'Deleted job {args.name}.')
        else:
            logging.error(f'Could not find job {args.name}.')


def list_jobs(args):
    if args.name:
        url = urljoin(args.url, f'/api/job/{args.name}')
        response = requests.get(url, headers={'Authorization': args.token,
                                              'content-type': 'application/json'},
                                verify=args.ssl_verify)
        if response.status_code != 200:
            logger.error(f'Could not list fuzz job {args.name}: {response.status_code}].')
        else:
            if 'name' in response.json():
                print_job_info(response.json())
            else:
                logger.error(f'No job with name {args.name} known.')
    else:
        url = urljoin(args.url, '/api/jobs')
        response = requests.get(url, headers={'Authorization': args.token,
                                              'content-type': 'application/json'},
                                verify=args.ssl_verify)
        if response.status_code != 200:
            logger.error(f'Could not list jobs: {response.text}')
        else:
            for job in response.json():
                print_job_info(job)
                print('-' * 80)


def parse_args():
    # TODO return results as JSON
    parser = argparse.ArgumentParser(description='Manage fuzzing jobs from the command line')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', dest='create', action='store_true', default=False,
                       help='Create a fuzz job')
    group.add_argument('-d', dest='delete', action='store_true', default=False,
                       help='Delete a fuzz job')
    group.add_argument('-l', dest='list', action='store_true', default=False,
                       help='List fuzz jobs')

    # arguments for creation of fuzz job
    parser.add_argument('--name', type=str, help='Name of the fuzz job')
    parser.add_argument('--description', type=str, default='', help='Description of the fuzz job')
    parser.add_argument('--mutation-engine', choices=['radamsa', 'urandom', 'external'],
                        help='Mutation engine to generate test cases', default='radamsa')
    parser.add_argument('--fuzzer', choices=['cfuzz', 'afl', 'qemufuzzer', 'elffuzzer', 'trapfuzzer', 'syzkaller'],
                        help='Fuzzer to test target with', default='cfuzz')
    parser.add_argument('--verifier', choices=['local_exploitable', 'remote_exploitable', 'no_verification'],
                        help='Verifier for crashes', default='no_verification')
    parser.add_argument('--maximum-samples', dest='maximum_samples', type=int, default=4,
                        help='Maximum number of test cases to generate at once')
    parser.add_argument('--maximum-iteration', type=int, dest='maximum_iteration',
                        default=1000000, help='Maximum number of fuzz iterations')
    parser.add_argument('--timeout', type=int, dest='timeout',
                        default=0, help='Disable fuzzing job after timeout. Default: 0 == None.')
    parser.add_argument('--test-cases', type=str, help='One or several test cases (as zip file) for fuzzing.')
    parser.add_argument('--fuzzing-target', type=str, help='Fuzzing target for fuzzing.')
    parser.add_argument('--cmd_args', type=str, default='', help='Command line arguments for fuzzing target.')

    # arguments for deletion of fuzz job
    parser.add_argument('--id', type=str, help='ID of fuzz job to delete')

    # arguments for fuzz job listing
    parser.add_argument('--active', action='store_true', help='List only active fuzz jobs')
    parser.add_argument('--archived', action='store_true', help='List only archived fuzz jobs')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--yes', action='store_true', help='Answer all questions with yes')

    parser.add_argument('--url', type=str, default='https://localhost:5000', help='URL')
    parser.add_argument('--ssl-verify', type=bool, default=False)
    parser.add_argument('--token', type=str, default='yuL4uJ4loqCGl86NDwDloPaPa5PQZs0f9hXRrLjbnJNLau3vxWKs3qS0XKN7BV3o')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    if args.create:
        create_job(args)
    elif args.delete:
        delete_job(args)
    else:
        list_jobs(args)


if __name__ == '__main__':
    main()
