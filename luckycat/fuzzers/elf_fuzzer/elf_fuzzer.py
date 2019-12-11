#!/usr/bin/python3
import base64
import datetime
import logging
import os
import subprocess
import time

from luckycat.fuzzers.templates.python.PythonTemplateInternalMutationEngine import PythonFuzzer


class ElfFuzzer(PythonFuzzer):

    def __init__(self):
        self.path_to_this_file = os.path.split(os.path.realpath(__file__))[0]
        super(ElfFuzzer, self).__init__(config_path=os.path.join(
            self.path_to_this_file, 'fuzzer.cfg'))
        self._check_configuration()
        if not os.path.exists(self.result_path):
            os.mkdir(self.result_path)

    def _check_configuration(self):
        self.job_name = self.config['ELF_FUZZER']['job_name']
        logging.info(f'job_name: {self.job_name}')
        self.ssh_port = self.config['ELF_FUZZER']['ssh_port']
        print(f'ssh_port: {self.ssh_port}')
        self.vm_path = self.config['ELF_FUZZER']['vm_path']
        print(f'vm_path: {self.vm_path}')
        self.user_name = self.config['ELF_FUZZER']['user_name']
        print(f'user_name: {self.user_name}')
        self.result_path = self.config['ELF_FUZZER']['result_path']
        print(f'result_path {self.result_path}')

    def _start_vm(self):
        print(f'Starting VM {self.vm_path}')
        self.vm = subprocess.Popen('./start.sh',
                                   shell=True,
                                   cwd=self.vm_path)
        print('Sleeping one minute to let VM boot up.')
        time.sleep(60)

    @staticmethod
    def _hard_reset_vm():
        '''
        this method is called in case _wait_for_system
        timeouts. Then, we would have to kill the qemu
        process in order to continue. It may timeout
        because the OS takes ages to dump the coredump
        or dies during dumping...
        '''
        print('Hard reset of VM not implemented yet!')
        raise

    def _generate_elfs(self, current_time):
        cmd = f'ssh {self.user_name}@localhost -p{self.ssh_port} "/tmp/generate_elfs.sh" > /dev/null'
        subprocess.run(cmd, shell=True)

        cmd = f'scp -P{self.ssh_port} {self.user_name}@localhost:/tmp/orcs.tar.gz {self.result_path}/orcs_{current_time}.tar.gz'
        subprocess.run(cmd, shell=True)

        cmd = f'ssh {self.user_name}@localhost -p{self.ssh_port} "rm /tmp/orcs.tar.gz"'
        subprocess.run(cmd, shell=True)

    def _fuzz_elfs(self, current_time):
        cmd = f'/usr/bin/timeout 30 ssh {self.user_name}@localhost -p{self.ssh_port} "/tmp/fuzz_elfs.sh" > {self.result_path}/res_{current_time}.log'
        subprocess.run(cmd, shell=True)

    def _wait_for_system(self):
        cmd = f'/usr/bin/timeout 5 ssh {self.user_name}@localhost -p{self.ssh_port} "exit"'

        for i in range(10):
            response = subprocess.run(cmd, shell=True)
            if response.returncode == 0:
                print('VM is alive.')
                return
            print('VM is not up, sleeping...')
            time.sleep(20)
        self._hard_reset_vm()

    def _copy_scripts_to_vm(self):
        path_to_scripts = os.path.join(self.path_to_this_file, 'scripts')
        for script in ['generate_elfs.sh', 'fuzz_elfs.sh', 'exec_elf.sh',
                       'check_crash_dump.sh', 'compress_dump.sh']:
            cmd = f'scp -P{self.ssh_port} {os.path.join(path_to_scripts, script)} {self.user_name}@localhost:/tmp/{script}'
            subprocess.run(cmd, shell=True)

    @staticmethod
    def _get_test_cases():
        cmd = '$(find /tmp/verify -exec file {} \; | grep -i ELF | cut -d: -f1)'
        output = subprocess.getoutput(cmd)
        return output.splitlines()

    def _verify_crash(self, current_time):
        cmd = f'ssh root@localhost -p{self.ssh_port} "/tmp/compress_dump.sh"'
        subprocess.run(cmd, shell=True)

        cmd = f'scp -P{self.ssh_port} root@localhost:/tmp/last_crash.tar.gz {self.result_path}/crash_dump_{ current_time}.tar.gz'
        subprocess.run(cmd, shell=True)

        cmd = 'mkdir -p /tmp/verify'
        subprocess.run(cmd, shell=True)

        cmd = f'cp -v {self.result_path}/orcs_{current_time}.tar.gz /tmp/verify/verify.tar.gz'
        subprocess.run(cmd, shell=True)

        cmd = 'cd /tmp/verify && tar -xvf /tmp/verify/verify.tar.gz && rm /tmp/verify/verify.tar.gz'
        subprocess.run(cmd, shell=True)

        crash_test_case = None
        test_cases = self._get_test_cases()
        for test_case in test_cases:
            print(f'Verifying {test_case}')
            cmd = f'/usr/bin/timeout 5 ssh {self.user_name}@localhost -p{self.ssh_port} "rm /tmp/elf_verify"'
            subprocess.run(cmd, shell=True)

            path_to_current_test_case = os.path.join('/tmp/verify/', test_case)
            cmd = f'scp -P{self.ssh_port} $f {self.user_name}@localhost:/tmp/elf_verify' #  "path_to_current_test"_case was included also, no clue where...
            subprocess.run(cmd, shell=True)

            cmd = f'/usr/bin/timeout 20 ssh {self.user_name}@localhost -p{self.ssh_port} "/tmp/exec_elf.sh"'
            subprocess.run(cmd, shell=True)

            cmd = f'/usr/bin/timeout 5 ssh {self.user_name}@localhost -p{self.ssh_port} "exit"'
            response = subprocess.run(cmd, shell=True)
            if response.returncode == 0:
                continue
            else:
                print(f'Kernel crash probably provoked by {test_case}')
                with open(path_to_current_test_case, 'rb') as f:
                    crash_test_case = f.read()
                break

        print('Cleaning up temp data')
        cmd = 'cd /tmp && rm -rf /tmp/verify'
        subprocess.run(cmd, shell=True)

        cmd = f'/usr/bin/timeout 10 ssh {self.user_name}@localhost -p{self.ssh_port} "rm /tmp/*.core"'
        subprocess.run(cmd, shell=True)

        if crash_test_case:
            test_case_data = base64.b64encode(crash_test_case)
            return {'test_case': test_case_data,
                    'stack_trace': test_case_data}
        else:
            return None

    def _system_has_crashed(self):
        crashed = False
        cmd = f'ssh {self.user_name}@localhost -p{self.ssh_port} "/tmp/check_crash_dump.sh" > {self.result_path}/check_crash.log'
        subprocess.run(cmd, shell=True)
        with open(f'{self.result_path}/check_crash.log', 'r') as f:
            if 'CRASH' in f.read():
                crashed = True
        return crashed

    def _delete_test_cases(self, current_time):
        os.remove(f'{self.result_path}/res_{current_time}.log')
        os.remove(f'{self.result_path}/orcs_{current_time}.tar.gz')

    def fuzz(self):
        iteration = 0
        self._start_vm()
        while 1:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            iteration += 1
            self._copy_scripts_to_vm()
            self._generate_elfs(current_time)
            self._fuzz_elfs(current_time)
            self._send_stats({'time': current_time,
                              'iteration': iteration,
                              'fuzzer': 'elf_fuzzer'})
            self._wait_for_system()
            if self._system_has_crashed():
                crash = self._verify_crash(current_time)
                if crash:
                    self._send_crash({'fuzzer': 'elf_fuzzer',
                                      'test_case': crash['test_case'],
                                      'reason': 'kernel core dump',
                                      'additional':
                                          {'stack_trace': crash['stack_trace']}})
                else:
                    print('Strange: could not verify crash...')
                    raise
            else:
                print('System still alive. Continuing...')
                self._delete_test_cases(current_time)


def main():
    elf_fuzz = ElfFuzzer()
    elf_fuzz.fuzz()


if __name__ == '__main__':
    main()
