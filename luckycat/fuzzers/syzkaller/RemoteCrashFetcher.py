import os
from multiprocessing import Process
from socket import timeout as SocketTimeout

import config
from paramiko import SSHClient, AuthenticationException, SSHException, BadHostKeyException
from paramiko.buffered_pipe import PipeTimeout as PipeTimeout
from scp import SCPClient, SCPException


class RemoteCrashFetcher(Process):
    def __init__(self):
        super(RemoteCrashFetcher, self).__init__()

    def fetch_remote_crashes(self):
        """
        some exception handling code is taken from https://www.programcreek.com/python/example/105570/scp.SCPClient
        """
        try:
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(hostname=config.remote_system_ip)
            self.copy_crashes_dir_with_scp(ssh)
        except AuthenticationException:
            print(f'Authentication failed, please verify your credentials')
        except SSHException as sshException:
            print(f'Unable to establish SSH connection: {sshException}')
        except BadHostKeyException as badHostKeyException:
            print(f'Unable to verify servers host key: {badHostKeyException}')
        finally:
            ssh.close() #reicht es aus die ssh-object initialisierung vor das try zu packen?

    @staticmethod
    def copy_crashes_dir_with_scp(ssh):
        parent_dir_of_crashes_dir = os.path.dirname(config.crashes_dir)
        try:
            scp = SCPClient(ssh.get_transport())
            scp.get(remote_path=config.remote_crashes_dir, local_path=parent_dir_of_crashes_dir, recursive=True,
                    preserve_times=True)
            print('successfully fetched!!')
        except SCPException as e:
            print(f'Operation error: {e}')
        except SocketTimeout:
            """
            the fetcher will need multiple attempts if the ssh connection is bad and/or the copy dir is big
            """
            print('SocketTimeout')
        except PipeTimeout as pipetimeout:
            print(f'timeout was reached on a read from a buffered Pipe: {pipetimeout}')
        finally:
            scp.close()

    def run(self):
        while True:
            self.fetch_remote_crashes()
