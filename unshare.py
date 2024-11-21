#!/usr/bin/env python3

import subprocess
from pathlib import Path
import os
import argparse
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--stage', choices=['1', '2'], required=True)
parser.add_argument('--pty')
parser.add_argument('--shell', default=False, action="store_true")

args = parser.parse_args()

def stage1():
    python = Path('result/sw/bin/python3').readlink()

    #link_path = str(Path('console').absolute())
    if args.shell:
        socat = subprocess.Popen(['socat', '-d', 'PTY,raw,link=console', 'OPEN:/dev/zero'])
    else:
        socat = subprocess.Popen(['socat', '-d', 'PTY,raw,link=console,echo=0', 'STDIO'])
    time.sleep(1)
    slave_path = Path('./console').readlink()


    # (pmaster, pslave) = os.openpty()
    # master_path = Path(f'/proc/self/fd/{pmaster}').readlink()
    # slave_path = Path(f'/proc/self/fd/{pslave}').readlink()
    # print(f'slave path: {slave_path}')
    # print(f'master path: {master_path}')
    # print(f'master fd: {pmaster}')

    # slave_path.chmod(0o620)

    # if not args.shell:
    #     subprocess.Popen(['cat', '-'], close_fds=False, shell=False, stdin=pmaster)
    #     subprocess.Popen(['cat', '-'], close_fds=False, shell=False, stdout=pmaster)

    if args.shell:
        stdin = None
        stdout = None
        stderr = None
    else:
        stdin=subprocess.DEVNULL
        stdout=subprocess.DEVNULL
        stderr=subprocess.DEVNULL


    unshare = subprocess.run([
        'systemd-run',
        '--scope',
        '--quiet',
        '--user',
        '--property=Delegate=yes',
        'unshare',
        '--mount',
        '--pid',
        '--user',
        '--map-auto',
        '--map-root-user',
        '--net',
        '--fork',
        '--propagation=slave',
        str(python),
        './unshare.py',
        '--stage=2',
        '--pty',
        str(slave_path)
    ] + (['--shell'] if args.shell  else []),
                   check=False,
                   close_fds=(not args.shell),
                   pass_fds=(),
                   stdin=stdin,
                   stdout=stdout,
                   stderr=stderr,
                )
    socat.kill()
    unshare.check_returncode()

def stage2():
    script_dir = 'nix'
    chroot = Path('result/sw/bin/chroot').readlink()
    init = Path('result').readlink() / 'init'
    shell = Path('result/sw/bin/bash').readlink()
    print(f'slave path: {args.pty}')

    commands = [
        f'mount -o nodev,nosuid,size=16G -t tmpfs tmpfs {script_dir}',
        f'mkdir -p {script_dir}/proc',
        f'mkdir -p {script_dir}/dev',
        f'mkdir -p {script_dir}/etc',
        f'mkdir -p {script_dir}/tmp',
        f'mkdir -p {script_dir}/run/lock',
        f'mkdir -p {script_dir}/var/lib/journal',
        f'mkdir -p {script_dir}/sys/fs/cgroup',
        f'mkdir -p {script_dir}/nix/store',
        f'mkdir -p {script_dir}/root',
        f'mount --bind --read-only /nix/store {script_dir}/nix/store',
        f'mount --rbind --read-only /sys {script_dir}/sys',
        f'mount --rbind --read-only /dev {script_dir}/dev',
        f'mount -t proc proc {script_dir}/proc',
        #f'mount --bind {script_dir}/proc/self/fd/1 {script_dir}/dev/console',
        f'mount --bind {args.pty} {script_dir}/dev/console',
        f'mount -o nodev,nosuid,size=16G -t tmpfs tmpfs {script_dir}/tmp',
        f'mount -o nodev,nosuid,size=16G -t tmpfs tmpfs {script_dir}/run',
        f'mkdir {script_dir}/run/wrappers',
    ]

    environment = {
        'HOME': '/root',
        'container': 'unshare',
        'PATH': Path('result/sw').readlink() / 'bin',
        'SHELL': shell,
    }

    print(f"PID: {os.getpid()}")


    for command in commands:
        subprocess.run(command, shell=True, check=True, env=environment)

    print(f"chroot: {chroot}")
    print(f"dir: {script_dir}")
    print(f"init: {init}")
    print(f'console path: {args.pty}')

    if args.shell:
        os.execve(chroot, [chroot, script_dir, shell], environment)
    else:
        os.execve(chroot, [chroot, script_dir, init, '--log-level=debug'], environment)
        #os.execve(chroot, [chroot, script_dir, 'agetty', '/dev/console', 'dumb'], environment)

if args.stage == '1':
    stage1()
elif args.stage == '2':
    stage2()
else:
    sys.exit(1)
