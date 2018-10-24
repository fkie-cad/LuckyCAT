# backend configuration
samples_path = '/opt/luckycat/results'
templates_path = '/opt/luckycat/samples'
f3c_path = '/opt/luckycat'
temporary_path = '/tmp'

sample_generator_sleeptime = 0.1
crash_verification_sender_sleeptime = 10
job_scheduler_sleeptime = 60

# RabbitMQ configuration
queue_host = 'queue'

# database configuration
db_host = 'database'
db_name = 'luckycat'
db_user = 'cat'
db_password = 'lucky'

# frontend configuration
secret_key = 'this_is_f3c'
default_user_email = 'donald@great.again'
default_user_password = 'password'
default_user_api_key = 'yuL4uJ4loqCGl86NDwDloPaPa5PQZs0f9hXRrLjbnJNLau3vxWKs3qS0XKN7BV3o'

# mutation engine configuration
mutation_engines = [{'name': 'radamsa',
                     'description': 'radamsa is a test case generator for robustness testing',
                     'command': 'radamsa -m ft=2,fo=2,fn,num=5,td,tr2,ts1,tr,ts2,ld,lds,lr2,li,ls,lp,lr,lis,lrs,sr,sd,bd,bf,bi,br,bp,bei,bed,ber,uw,ui=2,ab -p nd=2 -o %OUTPUT% %INPUT% '},
                    {'name': 'urandom',
                     'description': 'just random bytes from /dev/urandom',
                     'command': 'dd if=/dev/urandom bs=64 count=1 > %OUTPUT%'},
                    {'name': 'external',
                     'description': 'fuzzer comes with its own external mutation engine',
                     'command': ''}]
maximum_samples = 4

# fuzzer configuration
fuzzers = [{'name': 'afl', 'description': 'AFL is a mutator and fuzzer'},
           {'name': 'cfuzz', 'description': 'cfuzz is a generic fuzzer that should run on all Unix-based targets'},
           {'name': 'qemufuzzer', 'description': 'qemufuzzer fuzzes binaries of whole firmware images'},
           {'name': 'elffuzzer', 'description': 'ELF fuzzer for *UNIX systems'},
           {'name': 'trapfuzzer', 'description': 'trap fuzzer for BSD-based systems'}]
