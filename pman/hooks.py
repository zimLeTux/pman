import os
import subprocess

from . import creationutils


class Converter(object):
    def __init__(self, supported_exts, ext_dst_map=None):
        self.supported_exts = supported_exts
        if ext_dst_map is None:
            self.ext_dst_map = {
                ext: '.bam'
                for ext in supported_exts
            }
        else:
            self.ext_dst_map = ext_dst_map

    def __call__(self, func):
        func.supported_exts = self.supported_exts
        func.ext_dst_map = self.ext_dst_map
        return func


@Converter(['.blend'])
def converter_blend_bam(config, user_config, srcdir, dstdir, assets):
    args = [
        'blend2bam',
        '--srcdir', srcdir,
        '--material-mode', config['general']['material_mode'],
        '--physics-engine', config['general']['physics_engine'],
    ]
    if user_config['blender']['use_last_path']:
        blenderdir = os.path.dirname(user_config['blender']['last_path'])
        args += [
            '--blender-dir', blenderdir,
        ]
    args += assets
    args += [
        dstdir
    ]

    # print("Calling blend2bam: {}".format(' '.join(args)))

    subprocess.call(args, env=os.environ.copy(), stdout=subprocess.DEVNULL)

@Converter([
    '.egg.pz', '.egg',
    '.obj', '.mtl',
    '.fbx', '.dae',
    '.ply',
])
def converter_native_bam(_config, _user_config, srcdir, dstdir, assets):
    processes = []
    for asset in assets:
        if asset.endswith('.mtl'):
            # Handled by obj
            continue

        ext = '.' + asset.split('.', 1)[1]
        dst = asset.replace(srcdir, dstdir).replace(ext, '.bam')
        args = [
            'native2bam',
            asset,
            dst
        ]

        # print("Calling native2bam: {}".format(' '.join(args)))
        processes.append(subprocess.Popen(args, env=os.environ.copy(), stdout=subprocess.DEVNULL))

    for proc in processes:
        proc.wait()


def create_git(projectdir, config, _user_config):
    if not os.path.exists(os.path.join(projectdir, '.git')):
        args = [
            'git',
            'init',
            '.'
        ]
        subprocess.call(args, env=os.environ.copy())

    templatedir = creationutils.get_template_dir()
    creationutils.copy_template_files(projectdir, templatedir, (
        ('panda.gitignore', '.gitignore'),
    ))

    gitignorepath = os.path.join(projectdir, '.gitignore')
    add_export_dir = False
    with open(gitignorepath, 'r') as gitignorefile:
        if config['build']['export_dir'] not in gitignorefile.readlines():
            add_export_dir = True

    if add_export_dir:
        with open(gitignorepath, 'a') as gitignorefile:
            gitignorefile.write(config['build']['export_dir'])
