import re
import time
import pathlib
import warnings
import hashlib
import subprocess
from contextlib import contextmanager

from . import BASE

PORT_RE = re.compile('name\s*=\s*port_(\d+),')

IMAGE_VERSION = '0.1'
IMAGE_NAME = 'virtualbox-image-{}.vmdk'.format(IMAGE_VERSION)
IMAGE_URL = 'http://files.zerogw.com/vagga/' + IMAGE_NAME
IMAGE_SHA256 = 'xx'

STORAGE_VERSION = '0.1'
STORAGE_NAME = 'virtualbox-storage-{}.vmdk'.format(IMAGE_VERSION)
STORAGE_URL = 'http://files.zerogw.com/vagga/' + IMAGE_NAME
STORAGE_SHA256 = 'xx'


def check_sha256(filename, sum):
    with open(tmp_path, 'rb') as f:
        sha = hashlib.sha256()
        while True:
            chunk = f.read()
            if not chunk:
                break
            sha.update(chunk)
    if sha.hex_digest() != IMAGE_SHA256:
        raise ValueError("Sha256 sum mismatch")


def create_vm():
    tmpname = 'vagga-tmp'
    subprocess.check_call(['ssh-keygen', '-R', '[127.0.0.1]:7022'])
    subprocess.check_call(['VBoxManage', 'createvm', '--register',
        '--name', tmpname, '--ostype', 'Ubuntu_64'])
    subprocess.check_call(['VBoxManage', 'modifyvm', tmpname,
        '--audio', 'none',
        '--memory', '2048',
        '--cpus', '2',
        '--nic1', 'nat',
        '--nictype1', 'virtio',
        '--natpf1', 'SSH,tcp,,7022,,22',
        '--natpf1', 'NFSt1,tcp,,7049,,2049',
        '--natpf1', 'NFSu1,udp,,7049,,2049',
        '--natpf1', 'NFSt2,tcp,,7111,,111',
        '--natpf1', 'NFSu2,udp,,7111,,111',
        '--natpf1', 'unison,tcp,,7767,,7767',
        ])
    subprocess.check_call(['VBoxManage', 'storagectl', tmpname,
        '--name', 'SATA Controller',
        '--add', 'sata'])
    subprocess.check_call(['VBoxManage', 'storageattach', tmpname,
        '--storagectl', 'SATA Controller',
        '--device', '0', '--port', '0', '--type', 'hdd',
        '--medium', str(BASE / 'vm/image.vdi')])
    subprocess.check_call(['VBoxManage', 'storageattach', tmpname,
        '--storagectl', 'SATA Controller',
        '--device', '0', '--port', '1', '--type', 'hdd',
        '--medium', str(BASE / 'vm/storage.vdi')])
    subprocess.check_call(['VBoxManage', 'modifyvm', tmpname,
        '--name', 'vagga-' + IMAGE_VERSION])
    return find_vm()


def find_vm():
    vboxlist = subprocess.check_output([
        'VBoxManage', 'list', 'vms',
    ]).decode('ascii').splitlines()
    for line in vboxlist:
        if line.startswith('"vagga-'):
            return (
                line.split('{')[1].rstrip('}'),  # id
                line.split('-')[1].split('"')[0],  # version
            )
    return None, None


def download_image(url, basename, hash, destination):

    if not destination.exists():

        image_dir = BASE / 'downloads'
        image_path = image_dir / basename

        if not image_dir.exists():
            image_dir.mkdir()

        if not image_path.exists():
            tmp_path = image_path.with_extension('tmp')
            subprocess.check_call(
                ['wget', '--continue', '-O', tmp_path, url])
            check_sha256(tmp_path, hash)
            tmp_path.rename(image_path)

        subprocess.check_call([
            'VBoxManage', 'clonehd', '--format', 'vdi',
            str(image_path), str(destination)])

        return True


def check_running(cur_id):
    info = subprocess.check_output(['VBoxManage', 'showvminfo', cur_id])
    for line in info.decode('latin-1').splitlines():
        if line.startswith('State:'):
            if line.split()[1] == 'running':
                return True


def init_vm(new_storage_callback):
    if not BASE.exists():
        BASE.mkdir()

    subprocess.run(
        ['VBoxManage', 'unregistervm', 'vagga-tmp', '--delete'],
        stderr=subprocess.DEVNULL)

    download_image(IMAGE_URL, IMAGE_NAME, IMAGE_SHA256, BASE / 'vm/image.vdi')
    new_storage = download_image(STORAGE_URL, STORAGE_NAME,
                   STORAGE_SHA256, BASE / 'vm/storage.vdi')
    if new_storage:
        new_storage_callback()

    cur_id, cur_version = find_vm()
    if cur_id is None:
        cur_id, cur_version = create_vm()
    elif cur_version != IMAGE_VERSION:
        warnings.warn("Image version {} required but {} found. "
            "Please run vagga _box_upgrade"
            .format(IMAGE_VERSION, cur_version))

    if not check_running(cur_id):
        subprocess.check_call(['VBoxManage', 'startvm', cur_id,
            '--type', 'headless'])

    return cur_id


@contextmanager
def expose_ports(vm, ports):

    info = subprocess.check_output(['VBoxManage', 'showvminfo', vm])
    already = set()
    for line in info.decode('latin-1').splitlines():
        if line.startswith('NIC 1 Rule'):
            m = PORT_RE.search(line)
            if m:
                already.add(int(m.group(1)))

    left = ports - already
    if left:
        cmdline = ['VBoxManage', 'controlvm', vm, 'natpf1']
        for port in left:
            cmdline.append('port_{0},tcp,,{0},,{0}'.format(port))
        subprocess.check_call(cmdline)
    try:
        yield
    finally:
        if ports:
            cmdline = ['VBoxManage', 'controlvm', vm, 'natpf1']
            for port in ports:
                cmdline.append('delete')
                cmdline.append('port_{0}'.format(port))
            subprocess.check_call(cmdline)
