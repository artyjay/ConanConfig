import argparse
import itertools
import pathlib
import os
import subprocess
import sys

from conans.client.conan_api import ConanAPIV1 as conan_api

REMOTE     = 'artyjay'
REMOTE_URL = 'https://artyjay.jfrog.io/artifactory/api/conan/conan-local'

CONAN_PROFILE_TEMPLATE = '''[settings]
{settings}
[options]
[build_requires]
[env]
{env}
'''

HOST_SETTINGS = {
    'Linux':
    {
        'os_arch': [
            {
                'name': 'linux-x86_64',
                'settings':
                {
                    'os': 'Linux',
                    'os_build': 'Linux',
                    'arch': 'x86_64',
                    'arch_build': 'x86_64',
                }
            }
        ],
        'compilers': [
            {
                'name': 'clang',
                'settings':
                {
                    'compiler': 'clang',
                    'compiler.version': '11',
                    'compiler.libcxx': 'libstdc++11'
                },
                'env':
                {
                    'CC': 'clang-11',
                    'CXX': 'clang-11',
                    'AR': 'llvm-ar-11',
                    'NM': 'llvm-nm-11',
                    'LD': 'llvm-link-11',
                    'STRIP': 'llvm-strip-11'
                }
            },
            {
                'name': 'gcc',
                'settings':
                {
                    'compiler': 'gcc',
                    'compiler.version': '10',
                    'compiler.libcxx': 'libstdc++11'
                },
                'env':
                {
                    'CC': 'gcc-10',
                    'CXX': 'g++-10',
                    'AR': 'gcc-ar-10',
                    'NM': 'gcc-nm-10'
                }
            }
        ]
    },
    'Windows':
    {
        'os_arch': [
            {
                'name': 'windows-x86_64',
                'settings':
                {
                    'os': 'Windows',
                    'os_build': 'Windows',
                    'arch': 'x86_64',
                    'arch_build': 'x86_64',
                }
            }
        ],
        'compilers': [
            {
                'name': 'msvc_mt',
                'settings':
                {
                    'compiler': 'Visual Studio',
                    'compiler.version': '16',
                    'compiler.runtime': 'MT'
                }
            }
        ]
    }
}

BUILD_TYPES = [
    {
        'name': 'debug',
        'settings':
        {
            'build_type': 'Debug'
        }
    },
    {
        'name': 'release',
        'settings':
        {
            'build_type': 'Release'
        }
    }
]

def Main():
    parser = argparse.ArgumentParser(
        description='Script for setting up Conan')

    platform_help = ", ".join(HOST_SETTINGS.keys())

    parser.add_argument('-p', '--platform', type=str, help=f'Host platform to setup Conan for, supported platforms [{platform_help}]')
    args = parser.parse_args()

    host_platform = args.platform
    print(f'Setup Conan for {host_platform}')

    profiles_path = os.path.join(pathlib.Path.home(), '.conan', 'profiles')
    print(f'Conan profiles folder {profiles_path}')
    os.makedirs(profiles_path, exist_ok=True)

    settings = HOST_SETTINGS[host_platform]

    os_arch_types = settings['os_arch']
    compiler_types = settings['compilers']

    # Add artyjay remote repo
    conan, _, _ = conan_api.factory()
    conan.create_app()

    remotes = conan.remote_list()
    found = [x for x in remotes if x.name == REMOTE]

    if len(found) == 0:
        print(f'Adding remote - {REMOTE} -> {REMOTE_URL}')
        conan.remote_add(REMOTE, REMOTE_URL)
    else:
        print(f'Not adding remote {REMOTE} as it is already registered')

    # Run permutations to generation profiles
    for profile in itertools.product(os_arch_types, compiler_types, BUILD_TYPES):
        os_arch = profile[0]
        compiler = profile[1]
        build = profile[2]

        os_arch_name = os_arch['name']
        compiler_name = compiler['name']
        build_name = build['name']

        profile_settings = {}
        profile_env = {}

        for entry in profile:
            entry_settings = entry.get('settings', {})
            entry_env = entry.get('env', {})

            # Update compiler.runtime for Visual Studio
            # Append 'd' to compiler.runtime for Visual Studio debug builds.
            if entry_settings.get('compiler', '') == 'Visual Studio':
                runtime = 'MT' if compiler_name == 'msvc_mt' else 'MD'
                debug_suffix = 'd' if build_name == 'debug' else ''
                runtime_value = f'{runtime}{debug_suffix}'
                entry_settings['compiler.runtime'] = runtime_value

            profile_settings.update(entry_settings)
            profile_env.update(entry_env)

        def values_string(entry_dict):
            return '\n'.join(map(lambda kv: f'{kv[0]}={kv[1]}', entry_dict.items()))

        profile_name         = f'{os_arch_name}-{compiler_name}-{build_name}'
        profile_settings_str = values_string(profile_settings)
        profile_env_str      = values_string(profile_env)
        
        profile = CONAN_PROFILE_TEMPLATE.format(settings=profile_settings_str,
                                                env=profile_env_str)

        profile_path = os.path.join(profiles_path, profile_name)

        if not os.path.exists(profile_path):
            print(f'Generating profile {profile_name}')
            with open(profile_path, 'wt') as profile_file:
                profile_file.write(profile)
        else:
            print(f'Skipping profile generation for {profile_name} as profile already exists')

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(Main())

# ------------------------------------------------------------------------------