#!/bin/python3
from cpt.packager import ConanMultiPackager
from conans import tools
import os, sys, platform

DEBUG_MODE = False
PACKAGE_NAME = 'qt-advanced-docking-system'
GIT_DIR = "ads-source"
NAME_PREFIX = "ADS"
STABLE_IN_GIT = True

username = "bentoudev"

# build_types = ["Release", "Debug", "RelWithDebInfo", "MinSizeRel"],

def createBuilder(channel, commit, password, version):
    branch_pattern = 'release*' # channel is set explicitly!

    if not "CONAN_VISUAL_VERSIONS" in os.environ:
        visual_versions = ["15","16"]
    else:
        ver = os.environ["CONAN_VISUAL_VERSIONS"]
        visual_versions = [ver]
        print(" [info] Selected Visual Studio version " + ver)

    if platform.system() == "Windows":
        build_types = ["Release", "Debug", "RelWithDebInfo", "MinSizeRel"]
    else:
        build_types = ["Release", "Debug"]

    # if password:
    #     return ConanMultiPackager(username=username,
    #             channel=channel,
    #             stable_branch_pattern=branch_pattern,
    #             visual_versions=visual_versions,

    #             upload="https://api.bintray.com/conan/bentoudev/yage",
    #             password=password)
    # else:

    return ConanMultiPackager(username=username,
            channel=channel,
            stable_branch_pattern=branch_pattern,
            visual_versions=visual_versions,
            build_types=build_types)

def build(channel, commit, password, version):
    os.environ[NAME_PREFIX + '_COMMIT'] = commit
    os.environ[NAME_PREFIX + '_VERSION'] = version

    builder = createBuilder(channel, commit, password, version)

    compiler = None

    if platform.system() != "Windows":
        if 'CXX' in os.environ and os.environ['CXX'].startswith('clang'):
            compiler = "clang"
            print (' [*] Selected clang')
        else:
            compiler = "gcc"
            print (' [*] Selected gcc')

    builder.add_common_builds()

    filtered_builds = []

    for settings, options, env_vars, build_requires, reference in builder.items:
        if settings['arch'] == "x86_64" and (not compiler or settings['compiler'] == compiler):

            if settings['compiler'].startswith('clang'):
                if not settings['compiler.version'].startswith('6'):
                    continue
                for libcxx in ['libc++', 'libstdc++']:
                    sets = settings.copy()
                    sets['compiler.libcxx'] = libcxx
                    filtered_builds.append([sets, options, env_vars, build_requires, reference])

            else:
                filtered_builds.append([settings, options, env_vars, build_requires, reference])

    builder.builds = filtered_builds

    builder.run()

def print_stdout(out):
    print(" [*] stdout: " + out[0])
    for x in range(len(out)):
        print(str(x) + ': ' + out[x])

def cmdRun(args, check=False):
    import subprocess
    cmd = subprocess.run(args, encoding='utf-8')
    subprocess.call()
    if check:
        cmd.check_returncode()

def runCommand(args, shell=False):
    import subprocess
    if len(args) == 0:
        return None
    try:
        if DEBUG_MODE:
            print(' [*] Running cmd... ' + args[0])
        raw_out = subprocess.check_output(args, shell=shell, cwd=GIT_DIR, stderr=subprocess.STDOUT)

        stdout = raw_out.decode()

        #cmd = run(args, encoding='utf-8', stdout=PIPE)
        #cmd.check_returncode()

        out = stdout.split('\n')
        if DEBUG_MODE:
            print_stdout(stdout)

        return str(out[0])
    except Exception as error:
        print (' [*] Caught error: ' + str(error))
        return None

def getGitVersion():
    try:
        data = {}
        data['version'] = runCommand(['git', 'describe'])
        data['commit'] = runCommand(['git', 'rev-parse', 'HEAD'])
        return data
    except Exception as error:
        print (' [*] Caught error: ' + str(error))
        return None

def upload(password):
    if not password:
        print (' [*] No repository key, skipping upload...')
        return

    runCommand(['conan', 'remote', 'add', 'yage', 'https://api.bintray.com/conan/bentoudev/yage'], True)
    runCommand(['conan', 'user', '-p', password, '-r', 'yage', username], True)
    runCommand(['conan', 'upload', PACKAGE_NAME + '*', '--all', '-r', 'yage', '-c', '--retry', '3', '--retry-wait', '10'], True)

def execute(password):
    channel = 'dev'
    version = None
    commit = None
    build_number = None

    if 'CI' in os.environ:
        print(' [info] CI Environment detected')

        if 'APPVEYOR' in os.environ:
            print(" [info] Welcome, AppVeyor!")
            if 'APPVEYOR_REPO_TAG_NAME' in os.environ:
                version = os.environ['APPVEYOR_REPO_TAG_NAME']
            if 'APPVEYOR_REPO_COMMIT' in os.environ:
                commit = os.environ['APPVEYOR_REPO_COMMIT']
#            if 'APPVEYOR_BUILD_NUMBER' in os.environ:
#                build_number = os.environ['APPVEYOR_BUILD_NUMBER']

        if 'TRAVIS' in os.environ:
            print(" [info] Welcome, Travis!")
            if 'TRAVIS_TAG' in os.environ:
                version = os.environ['TRAVIS_TAG']
            if 'TRAVIS_COMMIT' in os.environ:
                commit = os.environ['TRAVIS_COMMIT']
#            if 'TRAVIS_BUILD_NUMBER' in os.environ:
#                build_number = os.environ['TRAVIS_BUILD_NUMBER']

        if 'AZURE' in os.environ:
            print (" [info] Welcome, Azure Dev Ops!")
#            if 'AZURE_BUILD_NUMBER' in os.environ:
#                build_number = os.environ['AZURE_BUILD_NUMBER']

    if not version or not commit:
        print (' [*] Attempt to get version from git...')
        gitData = getGitVersion()
        if gitData:
            version = gitData['version']
            commit = gitData['commit']
        if STABLE_IN_GIT:
            channel = 'stable'
        ver_parts = version.split('-')
        if len(ver_parts) > 1:
            # Fix semvar
            if build_number:
                version = ver_parts[0] + '+' + build_number
            else:
                version = ver_parts[0] + '-dev'
    else:
        channel = 'stable'

    if version and commit:
        print (' [info] Channel: ' + channel)
        print (' [info] Version: ' + version)
        print (' [info] Commit: ' + commit)
        print ('')
        print (' [*] Executing conan build...')

        build(channel, commit, password, version)
        upload(password)
    else:
        msg = "Unable to determine version"
        sys.stderr.write(str.format(' [error] {}!', msg))
        raise Exception(msg)

if __name__ == '__main__':
    print ('')
    if len(sys.argv) >= 2:
        execute(sys.argv[1])
    else:
        if 'REPOSITORY_KEY' in os.environ:
            execute(os.environ['REPOSITORY_KEY'])
        else:
            print(" [warn] Missing repository key argument! Package won't be uploaded")
            execute(None)
