import pathlib
import warnings
import hashlib
import subprocess


BASE = pathlib.Path().home() / '.vagga'
IMAGE_VERSION = '0.1'
IMAGE_NAME = 'virtualbox-image-{}.vmdk'.format(IMAGE_VERSION)
IMAGE_URL = 'http://files.zerogw.com/vagga/' + IMAGE_NAME
IMAGE_SHA256 = 'xx'


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
        '--device', '0',
        '--port', '0',
        '--type', 'hdd',
        '--medium', str(BASE / 'vm/current.vdi')])
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


def init_vm():
    if not BASE.exists():
        BASE.mkdir()

    subprocess.run(
        ['VBoxManage', 'unregistervm', 'vagga-tmp', '--delete'],
        stderr=subprocess.DEVNULL)

    if not (BASE / 'vm/current.vdi').exists():

        image_dir = BASE / 'downloads'
        image_path = image_dir / IMAGE_NAME

        if not image_dir.exists():
            image_dir.mkdir()

        if not image_path.exists():
            tmp_path = image_path.with_extension('tmp')
            subprocess.check_call(
                ['wget', '--continue', '-O', tmp_path,
                 IMAGE_URL])
            check_sha256(tmp_path, IMAGE_SHA256)
            tmp_path.rename(image_path)

        subprocess.check_call([
            'VBoxManage', 'clonehd', '--format', 'vdi',
            str(image_path), str(BASE / 'vm/current.vdi')])

    cur_id, cur_version = find_vm()
    if cur_id is None:
        cur_id, cur_version = create_vm()
    elif cur_version != IMAGE_VERSION:
        warnings.warn("Image version {} required but {} found. "
            "Please run vagga _box_upgrade"
            .format(IMAGE_VERSION, cur_version))

    subprocess.run(['VBoxManage', 'startvm', cur_id, '--type', 'headless'])
