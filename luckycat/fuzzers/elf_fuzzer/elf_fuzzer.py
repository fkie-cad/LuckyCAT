#!/usr/bin/python3
import datetime
import os
import time
import base64
import logging
import subprocess
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
        logging.info('job_name: %s' % self.job_name)
        self.ssh_port = self.config['ELF_FUZZER']['ssh_port']
        print('ssh_port: %s' % self.ssh_port)
        self.vm_path = self.config['ELF_FUZZER']['vm_path']
        print('vm_path: %s' % self.vm_path)
        self.user_name = self.config['ELF_FUZZER']['user_name']
        print('user_name: %s' % self.user_name)
        self.result_path = self.config['ELF_FUZZER']['result_path']
        print('result_path %s' % self.result_path)

    def _start_vm(self):
        print('Starting VM %s' % self.vm_path)
        self.vm = subprocess.Popen('./start.sh',
                                   shell=True,
                                   cwd=self.vm_path)
        print("Sleeping one minute to let VM boot up.")
        time.sleep(60)

    def _hard_reset_vm(self):
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
        cmd = 'ssh %s@localhost -p%s "/tmp/generate_elfs.sh" > /dev/null' % (
            self.user_name,
            self.ssh_port)
        subprocess.run(cmd, shell=True)

        cmd = 'scp -P%s %s@localhost:/tmp/orcs.tar.gz %s/orcs_%s.tar.gz' % (
            self.ssh_port,
            self.user_name,
            self.result_path,
            current_time)
        subprocess.run(cmd, shell=True)

        cmd = 'ssh %s@localhost -p%s "rm /tmp/orcs.tar.gz"' % (self.user_name,
                                                               self.ssh_port)
        subprocess.run(cmd, shell=True)

    def _fuzz_elfs(self, current_time):
        cmd = '/usr/bin/timeout 30 ssh %s@localhost -p%s "/tmp/fuzz_elfs.sh" > %s/res_%s.log' % (
            self.user_name,
            self.ssh_port,
            self.result_path,
            current_time)
        subprocess.run(cmd, shell=True)

    def _wait_for_system(self):
        cmd = '/usr/bin/timeout 5 ssh %s@localhost -p%s "exit"' % (
            self.user_name,
            self.ssh_port)

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
            cmd = 'scp -P%s %s %s@localhost:/tmp/%s' % (
                self.ssh_port,
                os.path.join(path_to_scripts, script),
                self.user_name,
                script)
            subprocess.run(cmd, shell=True)

    def _get_test_cases(self):
        cmd = '$(find /tmp/verify -exec file {} \; | grep -i ELF | cut -d: -f1)'
        output = subprocess.getoutput(cmd)
        return output.splitlines()

    def _verify_crash(self, current_time):
        cmd = 'ssh root@localhost -p%s "/tmp/compress_dump.sh"' % self.ssh_port
        subprocess.run(cmd, shell=True)

        cmd = 'scp -P%s root@localhost:/tmp/last_crash.tar.gz %s/crash_dump_%s.tar.gz' % (
            self.ssh_port,
            self.result_path,
            current_time)
        subprocess.run(cmd, shell=True)

        cmd = 'mkdir -p /tmp/verify'
        subprocess.run(cmd, shell=True)

        cmd = 'cp -v %s/orcs_%s.tar.gz /tmp/verify/verify.tar.gz' % (self.result_path, current_time)
        subprocess.run(cmd, shell=True)

        cmd = "cd /tmp/verify && tar -xvf /tmp/verify/verify.tar.gz && rm /tmp/verify/verify.tar.gz"
        subprocess.run(cmd, shell=True)

        crash_test_case = None
        test_cases = self._get_test_cases()
        for test_case in test_cases:
            print('Verifying %s' % test_case)
            cmd = '/usr/bin/timeout 5 ssh %s@localhost -p%s "rm /tmp/elf_verify"' % (
                self.user_name, self.ssh_port)
            subprocess.run(cmd, shell=True)

            path_to_current_test_case = os.path.join('/tmp/verify/', test_case)
            cmd = 'scp -P%s $f %s@localhost:/tmp/elf_verify' % (self.ssh_port,
                                                                path_to_current_test_case,
                                                                self.user_name)
            subprocess.run(cmd, shell=True)

            cmd = '/usr/bin/timeout 20 ssh %s@localhost -p%s "/tmp/exec_elf.sh"' % (
                self.user_name, self.ssh_port)
            subprocess.run(cmd, shell=True)

            cmd = '/usr/bin/timeout 5 ssh %s@localhost -p%s "exit"' % (
                self.user_name, self.ssh_port)
            response = subprocess.run(cmd, shell=True)
            if response.returncode == 0:
                continue
            else:
                print('Kernel crash probably provoked by %s' % test_case)
                with open(path_to_current_test_case, 'rb') as f:
                    crash_test_case = f.read()
                break

        print('Cleaning up temp data')
        cmd = 'cd /tmp && rm -rf /tmp/verify'
        subprocess.run(cmd, shell=True)

        cmd = '/usr/bin/timeout 10 ssh %s@localhost -p%s "rm /tmp/*.core"' % (
            self.user_name,
            self.ssh_port)
        subprocess.run(cmd, shell=True)

        if crash_test_case:
            test_case_data = base64.b64encode(crash_test_case)
            return {'test_case': test_case_data,
                    'stack_trace': test_case_data}
        else:
            return None

    def _system_has_crashed(self):
        crashed = False
        cmd = 'ssh %s@localhost -p%s "/tmp/check_crash_dump.sh" > %s/check_crash.log' % (
            self.user_name,
            self.ssh_port,
            self.result_path)
        subprocess.run(cmd, shell=True)
        with open('%s/check_crash.log' % self.result_path, 'r') as f:
            if "CRASH" in f.read():
                crashed = True
        return crashed

    def _delete_test_cases(self, current_time):
        os.remove('%s/res_%s.log' % (
            self.result_path, current_time))
        os.remove('%s/orcs_%s.tar.gz' % (
            self.result_path, current_time))

    def fuzz(self):
        iteration = 0
        self._start_vm()
        while 1:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
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
                    print("Strange: could not verify crash...")
                    raise
            else:
                print("System still alive. Continuing...")
                self._delete_test_cases(current_time)


def main():
    elf_fuzz = ElfFuzzer()
    elf_fuzz.fuzz()


if __name__ == '__main__':
    main()
